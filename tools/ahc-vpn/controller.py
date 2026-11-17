#!/usr/bin/env python3
"""AHC VPN controller v2: private local queue, Aqua worker and recovery worker."""
import argparse
import contextlib
import datetime as dt
import fcntl
import json
import os
import pathlib
import re
import stat
import subprocess
import sys
import tempfile
import time
import uuid

ROOT = pathlib.Path.home() / '.ahc-vpn'
SC = '/usr/sbin/scutil'
ACTIONS = {'list', 'status', 'connect', 'disconnect', 'confirm', 'rollback'}
ID = re.compile(r'[0-9a-f]{32}\Z')
STATES = {'Connected', 'Disconnected', 'Connecting', 'Disconnecting'}
MAX_JSON = 65536

class Fault(RuntimeError):
    pass

def now():
    return time.time()

def iso(t):
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).isoformat()

def epoch(s):
    d = dt.datetime.fromisoformat(s.replace('Z', '+00:00'))
    if d.tzinfo is None:
        raise Fault('timestamp requires timezone')
    return d.timestamp()

def private_dir(p):
    p.mkdir(mode=0o700, exist_ok=True)
    s = p.lstat()
    if not stat.S_ISDIR(s.st_mode) or s.st_uid != os.getuid() or s.st_mode & 0o077:
        raise Fault('unsafe directory: ' + p.name)

def setup():
    os.umask(0o077)
    private_dir(ROOT)
    for d in ('requests', 'processing', 'results', 'logs', 'bin'):
        private_dir(ROOT / d)

def read(p):
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as f:
        s = os.fstat(f.fileno())
        if not stat.S_ISREG(s.st_mode) or s.st_uid != os.getuid() or s.st_mode & 0o077 or s.st_size > MAX_JSON:
            raise Fault('unsafe JSON file: ' + p.name)
        data = json.loads(f.read(MAX_JSON + 1))
    if not isinstance(data, dict):
        raise Fault('JSON object required')
    return data

def sync_dir(p):
    fd = os.open(p, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)

def write(p, data):
    fd, tmp = tempfile.mkstemp(prefix='.tmp-', dir=p.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=True, allow_nan=False)
            f.write('\n'); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, p)
        sync_dir(p.parent)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def remove(p):
    p.unlink(); sync_dir(p.parent)

@contextlib.contextmanager
def locked(name='lock', seconds=1):
    fd = os.open(ROOT / name, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        s = os.fstat(fd)
        if not stat.S_ISREG(s.st_mode) or s.st_uid != os.getuid() or s.st_mode & 0o077:
            raise Fault('unsafe lock')
        end = time.monotonic() + seconds
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB); break
            except BlockingIOError:
                if time.monotonic() >= end:
                    raise Fault('controller busy')
                time.sleep(.1)
        yield
    finally:
        os.close(fd)

def command(argv, timeout=5):
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=True)
    except (subprocess.SubprocessError, OSError):
        # Never print scutil output: it can contain connection details.
        raise Fault('OS command failed or timed out') from None
    return r.stdout.strip()

def boot_id():
    return command(['/usr/sbin/sysctl', '-n', 'kern.boottime'])

def sc(*args):
    return command([SC, '--nc', *args])

def profiles():
    d = read(ROOT / 'profiles.json')
    if not d or any(not re.fullmatch('[A-Z]{2}', k) or v != 'AHC ' + k for k, v in d.items()):
        raise Fault('invalid profile allowlist; expected country -> AHC COUNTRY')
    return d

def inventory():
    out = sc('list')
    rows = []
    for line in out.splitlines():
        m = re.search(r'\((Connected|Disconnected|Connecting|Disconnecting|Invalid)\).*?"([^"]+)"', line)
        if m:
            rows.append((m[2], m[1]))
        elif '"' in line or line.lstrip().startswith('*'):
            raise Fault('unrecognized VPN list row')
    if not rows:
        raise Fault('VPN list empty; GUI context not verified')
    return rows

def state(name):
    lines = sc('status', name).splitlines()
    if not lines or lines[0].strip() not in STATES:
        raise Fault('VPN status unknown: ' + name)
    return lines[0].strip()

def snapshot(cfg, allow_transition=False):
    rows = inventory()
    for name in cfg.values():
        if sum(n == name for n, _ in rows) != 1:
            raise Fault('VPN profile missing or ambiguous: ' + name)
    if any(n not in cfg.values() and s != 'Disconnected' for n, s in rows):
        raise Fault('unmanaged VPN active or unknown; do not modify')
    d = {k: state(v) for k, v in cfg.items()}
    if not allow_transition and any(s not in ('Connected', 'Disconnected') for s in d.values()):
        raise Fault('VPN transition in progress')
    if sum(s == 'Connected' for s in d.values()) > 1:
        raise Fault('multiple managed VPNs connected')
    return d

def wait(name, desired, deadline=None):
    end = time.monotonic() + 20
    while True:
        if deadline is not None and time.monotonic() >= deadline:
            raise Fault('lease expired during switch')
        if state(name) == desired:
            return
        if time.monotonic() >= end:
            raise Fault('VPN state timeout: ' + name)
        time.sleep(.5)

def pending():
    p = ROOT / 'pending.json'
    if not p.exists():
        return None
    d = read(p)
    cfg = profiles()
    if (d.get('version') != 2 or not ID.fullmatch(str(d.get('token', ''))) or
            not ID.fullmatch(str(d.get('request_id', ''))) or
            any(d.get(k) is not None and d[k] not in cfg for k in ('old', 'new')) or
            d.get('old') == d.get('new') or
            any(type(d.get(k)) not in (float, int) for k in ('started', 'deadline', 'mono_start', 'mono_deadline')) or
            not 30 <= d['deadline'] - d['started'] <= 300 or
            not 30 <= d['mono_deadline'] - d['mono_start'] <= 300):
        raise Fault('invalid pending journal; manual recovery required')
    return d

def expired(d):
    return (d['boot'] != boot_id() or now() >= d['deadline'] or now() < d['started'] or
            time.monotonic() >= d['mono_deadline'] or time.monotonic() < d['mono_start'])

def recovery_event(d, outcome):
    write(ROOT / 'last_recovery.json', {'token': d['token'], 'request_id': d['request_id'],
          'outcome': outcome, 'at': iso(now()), 'previous_country': d['old']})

def restore(d):
    cfg = profiles()
    # Refuse to touch other services, and retain journal on failure.
    s = snapshot(cfg, allow_transition=True)
    if any(v != 'Disconnected' for k, v in s.items() if k not in (d['old'], d['new'])):
        raise Fault('unexpected managed VPN; manual recovery required')
    if d['new']:
        name = cfg[d['new']]
        if state(name) not in ('Disconnected', 'Disconnecting'):
            sc('stop', name)
        wait(name, 'Disconnected')
    if d['old']:
        name = cfg[d['old']]
        status = state(name)
        if status == 'Disconnecting':
            wait(name, 'Disconnected'); status = 'Disconnected'
        if status == 'Disconnected':
            sc('start', name)
        wait(name, 'Connected')
    s = snapshot(cfg)
    if any(v != ('Connected' if k == d['old'] else 'Disconnected') for k, v in s.items()):
        raise Fault('rollback verification failed')
    recovery_event(d, 'restored')
    remove(ROOT / 'pending.json')
    return s

def watchdog_healthy():
    h = read(ROOT / 'watchdog-heartbeat.json')
    if h.get('boot') != boot_id() or not 0 <= time.monotonic() - h['monotonic'] <= 5:
        raise Fault('watchdog not healthy')
    try:
        os.kill(h['pid'], 0)
    except OSError:
        raise Fault('watchdog not running') from None

def consume_arm():
    p = ROOT / 'armed.json'
    if not p.exists():
        raise Fault('live switch not armed; use GUI Terminal arm')
    a = read(p)
    if a.get('boot') != boot_id() or not 0 < a['deadline'] - now() <= 300:
        raise Fault('live switch not armed or expired')
    remove(p)

def validate(q, rid):
    keys = {'version', 'request_id', 'action', 'country', 'lease_seconds', 'created_at', 'expires_at', 'lease_token', 'verified_country', 'muse_reachable'}
    if set(q) - keys or q.get('version') != 1 or q.get('request_id') != rid or not ID.fullmatch(rid) or q.get('action') not in ACTIONS:
        raise Fault('invalid request')
    t, e = epoch(q['created_at']), epoch(q['expires_at'])
    if not 0 < e - t <= 60 or not t - 2 <= now() < e:
        raise Fault('request expired or invalid timestamp')
    a = q['action']
    if a in ('connect', 'disconnect'):
        if type(q.get('lease_seconds')) is not int or not 30 <= q['lease_seconds'] <= 300:
            raise Fault('lease must be 30-300 seconds')
        if a == 'connect' and q.get('country') not in profiles():
            raise Fault('country not allowed')
    if a == 'confirm' and (not ID.fullmatch(str(q.get('lease_token', ''))) or q.get('muse_reachable') is not True):
        raise Fault('confirmation requires token and MUSE connectivity verification')
    if a == 'rollback' and 'lease_token' in q and not ID.fullmatch(str(q['lease_token'])):
        raise Fault('invalid rollback token')

def execute(q):
    a = q['action']; cfg = profiles(); d = pending()
    if a in ('list', 'status'):
        return {'profiles': cfg, 'status': snapshot(cfg, allow_transition=True),
                'pending': bool(d), 'lease_expires_at': iso(d['deadline']) if d else None}
    if a == 'rollback':
        if not d:
            return {'state': 'no_pending'}
        if q.get('lease_token', d['token']) != d['token']:
            raise Fault('wrong rollback token')
        return {'state': 'restored', 'status': restore(d)}
    if a == 'confirm':
        if not d or q['lease_token'] != d['token']:
            raise Fault('no matching pending lease')
        if expired(d):
            restore(d); raise Fault('lease expired; restored')
        watchdog_healthy()
        if q.get('verified_country') != (d['new'] or 'NONE'):
            raise Fault('exit country or disconnected state not verified')
        s = snapshot(cfg)
        if any(v != ('Connected' if k == d['new'] else 'Disconnected') for k, v in s.items()):
            raise Fault('connection state does not match lease')
        if expired(d):
            restore(d); raise Fault('lease expired; restored')
        remove(ROOT / 'pending.json')
        return {'state': 'confirmed', 'status': s}
    if d:
        raise Fault('pending switch; confirm or rollback first')
    s = snapshot(cfg)
    old = next((k for k, v in s.items() if v == 'Connected'), None)
    new = q.get('country') if a == 'connect' else None
    if old == new:
        return {'state': 'unchanged', 'status': s}
    watchdog_healthy(); consume_arm()
    t, m, lease = now(), time.monotonic(), q['lease_seconds']
    d = {'version': 2, 'request_id': q['request_id'], 'token': uuid.uuid4().hex,
         'old': old, 'new': new, 'boot': boot_id(), 'started': t, 'deadline': t + lease,
         'mono_start': m, 'mono_deadline': m + lease}
    # Durable journal before any network change; independent watchdog sees it.
    write(ROOT / 'pending.json', d)
    try:
        if expired(d):
            raise Fault('lease expired before switch')
        if old:
            sc('stop', cfg[old]); wait(cfg[old], 'Disconnected', d['mono_deadline'])
        if expired(d):
            raise Fault('lease expired before connect')
        if new:
            sc('start', cfg[new]); wait(cfg[new], 'Connected', d['mono_deadline'])
        s = snapshot(cfg)
        if expired(d) or any(v != ('Connected' if k == new else 'Disconnected') for k, v in s.items()):
            raise Fault('switch not verified before deadline')
    except Exception:
        try:
            restore(d)
        except Exception:
            recovery_event(d, 'retry_required')
            raise Fault('switch failed; recovery pending; do not issue another switch') from None
        raise Fault('switch failed; previous state restored') from None
    return {'state': 'awaiting_confirmation', 'previous_country': old, 'current_country': new,
            'status': s, 'lease_token': d['token'], 'lease_expires_at': iso(d['deadline'])}

def result(rid, **data):
    write(ROOT / 'results' / (rid + '.json'), {'version': 1, 'request_id': rid, 'at': iso(now()), **data})

def process(p):
    rid = p.stem
    if not ID.fullmatch(rid):
        return
    dest = ROOT / 'processing' / p.name
    if (ROOT / 'results' / p.name).exists():
        remove(p); return
    if dest.exists():
        raise Fault('duplicate in processing')
    os.replace(p, dest); sync_dir(dest.parent); sync_dir(p.parent)
    try:
        q = read(dest); validate(q, rid)
        with locked(seconds=2):
            validate(q, rid)
            data = execute(q)
        result(rid, ok=True, action=q['action'], **data)
    except Exception as e:
        result(rid, ok=False, error=str(e) if isinstance(e, Fault) else type(e).__name__)
    remove(dest)

def log(msg):
    print(iso(now()), msg, file=sys.stderr, flush=True)

def agent():
    with locked('agent.lock', .1):
        # Never replay an interrupted mutation. Watchdog handles the journal.
        for p in sorted((ROOT / 'processing').glob('*.json')):
            if ID.fullmatch(p.stem):
                if not (ROOT / 'results' / p.name).exists():
                    result(p.stem, ok=False, error='interrupted; inspect status and last_recovery; not replayed')
                remove(p)
        while True:
            write(ROOT / 'heartbeat.json', {'pid': os.getpid(), 'at': iso(now())})
            for p in sorted((ROOT / 'requests').glob('*.json')):
                try:
                    process(p)
                except Exception as e:
                    log('queue error: ' + type(e).__name__)
            time.sleep(1)

def watchdog_tick():
    write(ROOT / 'watchdog-heartbeat.json', {'pid': os.getpid(), 'boot': boot_id(), 'monotonic': time.monotonic()})
    if not (ROOT / 'pending.json').exists():
        return
    with locked(seconds=.2):
        d = pending()
        if d and expired(d):
            try:
                restore(d)
            except Exception:
                recovery_event(d, 'retry_required')
                raise

def watchdog():
    with locked('watchdog.lock', .1):
        while True:
            try:
                watchdog_tick()
            except Exception as e:
                log('watchdog: ' + (str(e) if isinstance(e, Fault) else type(e).__name__))
            time.sleep(1)

def arm():
    if not sys.stdin.isatty() or os.stat('/dev/console').st_uid != os.getuid() or command(['/bin/launchctl', 'managername']) != 'Aqua':
        raise Fault('arm from the logged-in Mac GUI Terminal only')
    if input('I am at the Mac and can restore networking. Type ARM: ') != 'ARM':
        raise Fault('not armed')
    with locked(seconds=2):
        if pending():
            raise Fault('pending recovery; do not arm')
        watchdog_healthy(); snapshot(profiles())
        write(ROOT / 'armed.json', {'boot': boot_id(), 'deadline': now() + 300})
    print('Armed for one switch within 5 minutes. Do not leave the Mac.')

def client(argv=None):
    p = argparse.ArgumentParser(); p.add_argument('action', choices=sorted(ACTIONS | {'arm', 'result'})); p.add_argument('country', nargs='?')
    p.add_argument('--lease', type=int, default=90); p.add_argument('--token'); p.add_argument('--verified-country'); p.add_argument('--muse-reachable', action='store_true'); p.add_argument('--wait', type=int, default=75)
    a = p.parse_args(argv)
    if a.action == 'arm':
        arm(); return 0
    if a.action == 'result':
        if not a.country or not ID.fullmatch(a.country):
            raise Fault('result requires request id')
        print(json.dumps(read(ROOT / 'results' / (a.country + '.json')), indent=2)); return 0
    if not 0 <= a.wait <= 300:
        raise Fault('invalid wait')
    t = now(); rid = uuid.uuid4().hex
    q = {'version': 1, 'request_id': rid, 'action': a.action, 'created_at': iso(t), 'expires_at': iso(t + 30)}
    if a.action == 'connect':
        q['country'] = (a.country or '').upper()
    elif a.country:
        raise Fault('unexpected country')
    if a.action in ('connect', 'disconnect'):
        q['lease_seconds'] = a.lease
    if a.token:
        q['lease_token'] = a.token
    if a.action == 'confirm':
        q.update(verified_country=(a.verified_country or '').upper(), muse_reachable=a.muse_reachable)
    validate(q, rid)
    write(ROOT / 'requests' / (rid + '.json'), q)
    end = time.monotonic() + a.wait
    path = ROOT / 'results' / (rid + '.json')
    while True:
        if path.exists():
            r = read(path); print(json.dumps(r, indent=2)); return 0 if r['ok'] else 1
        if time.monotonic() >= end:
            print(json.dumps({'ok': False, 'state': 'queued_or_in_progress', 'request_id': rid, 'message': 'Check result by ID; do not resubmit blindly.'})); return 2
        time.sleep(.25)

def entry(mode='client'):
    try:
        setup()
        if mode == 'agent':
            agent()
        elif mode == 'watchdog':
            watchdog()
        else:
            return client()
    except Exception as e:
        log(str(e) if isinstance(e, Fault) else type(e).__name__)
        return 1
    return 0

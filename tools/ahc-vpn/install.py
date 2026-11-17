#!/usr/bin/env python3
"""Install only from the logged-in Mac GUI Terminal; never switch a VPN."""
import os
import pathlib
import plistlib
import shutil
import subprocess
import sys
import tempfile

import controller as c

SOURCE = pathlib.Path(__file__).resolve().parent
LABELS = ('com.ahc.vpn.watchdog', 'com.ahc.vpn.agent')
FILES = ('controller.py', 'ahc-vpn', 'client.py', 'agent.py', 'watchdog.py')

def launch(*args, check=True):
    return subprocess.run(['/bin/launchctl', *args], check=check, capture_output=True, text=True)

def main():
    if sys.platform != 'darwin' or sys.version_info < (3, 9) or os.getuid() == 0:
        raise c.Fault('requires macOS, Python 3.9+, non-root GUI user')
    if os.stat('/dev/console').st_uid != os.getuid() or c.command(['/bin/launchctl', 'managername']) != 'Aqua':
        raise c.Fault('run in logged-in Mac GUI Terminal')
    domain = 'gui/' + str(os.getuid())
    if launch('print', domain, check=False).returncode:
        raise c.Fault('GUI launchd domain unavailable')
    c.setup()
    with c.locked(seconds=2):
        if (c.ROOT / 'pending.json').exists():
            raise c.Fault('pending switch; restore using current version before installation')
        for label in LABELS:
            if launch('print', domain + '/' + label, check=False).returncode == 0:
                raise c.Fault('already running; follow README update procedure first')
        if (c.ROOT / 'armed.json').exists():
            c.remove(c.ROOT / 'armed.json')
        if not (c.ROOT / 'profiles.json').exists():
            c.write(c.ROOT / 'profiles.json', {'DE': 'AHC DE', 'US': 'AHC US'})
        c.profiles()  # preserve existing configuration; verify before replacing code
        for f in FILES:
            target = c.ROOT / 'bin' / f
            fd, tmp = tempfile.mkstemp(dir=target.parent)
            with os.fdopen(fd, 'wb') as w:
                w.write((SOURCE / f).read_bytes()); w.flush(); os.fsync(w.fileno())
            os.chmod(tmp, 0o700); os.replace(tmp, target)
        c.sync_dir(c.ROOT / 'bin')
        folder = pathlib.Path.home() / 'Library' / 'LaunchAgents'
        folder.mkdir(parents=True, exist_ok=True)
        for label in LABELS:
            data = plistlib.loads((SOURCE / (label + '.plist')).read_bytes())
            data['ProgramArguments'] = [sys.executable, str(c.ROOT / 'bin' / data['ProgramArguments'][1])]
            data['WorkingDirectory'] = str(c.ROOT)
            for key in ('StandardOutPath', 'StandardErrorPath'):
                data[key] = str(c.ROOT / 'logs' / pathlib.Path(data[key]).name)
            path = folder / (label + '.plist')
            fd, tmp = tempfile.mkstemp(dir=folder)
            with os.fdopen(fd, 'wb') as w:
                plistlib.dump(data, w); w.flush(); os.fsync(w.fileno())
            subprocess.run(['/usr/bin/plutil', '-lint', tmp], check=True)
            os.replace(tmp, path)
    started = []
    try:
        for label in LABELS:
            launch('bootstrap', domain, str(folder / (label + '.plist')))
            started.append(label)
    except Exception:
        for label in reversed(started):
            launch('bootout', domain + '/' + label, check=False)
        raise c.Fault('bootstrap failed; check launchctl and logs; no VPN switch attempted') from None
    print('Installed. Read-only by default. Run:')
    print(str(c.ROOT / 'bin' / 'ahc-vpn') + ' list')
    print('Use the same Python interpreter if python3 is not on PATH: ' + sys.executable)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(str(e) if isinstance(e, c.Fault) else type(e).__name__, file=sys.stderr)
        raise SystemExit(1)

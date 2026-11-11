#!/usr/bin/env python3
"""Connectivity probe (stdlib only): DNS + one HTTPS GET + robots.txt per shop.
Run on the iMac. Writes results to probe-report.json next to this script."""
import socket, ssl, json, urllib.request, urllib.error
from pathlib import Path

UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 '
      '(KHTML, like Gecko) Version/17.4 Safari/605.1.15')
SHOPS = [
    ('bstn', 'www.bstn.com', 'https://www.bstn.com/'),
    ('footlocker', 'www.footlocker.com', 'https://www.footlocker.com/'),
    ('zalando_de', 'www.zalando.de', 'https://www.zalando.de/'),
]
HERE = Path(__file__).resolve().parent


def fetch(url, limit):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read(limit)
            return {'ok': True, 'status': r.status, 'final_url': r.geturl(),
                    'content_type': r.headers.get('Content-Type', ''), 'bytes': len(body),
                    'body': body}
    except urllib.error.HTTPError as e:
        body = e.read(limit) if e.fp else b''
        return {'ok': False, 'status': e.code, 'final_url': url,
                'content_type': '', 'bytes': len(body), 'body': body,
                'error': f'HTTPError {e.code} {e.reason}'}
    except Exception as e:
        return {'ok': False, 'status': None, 'final_url': url, 'content_type': '',
                'bytes': 0, 'body': b'', 'error': f'{type(e).__name__}: {e}'}


report = {'python_env': {}, 'shops': []}
try:
    import platform
    report['python_env'] = {'version': platform.python_version(),
                            'platform': platform.platform()}
except Exception as e:
    report['python_env'] = {'error': str(e)}

for name, host, url in SHOPS:
    entry = {'shop': name, 'host': host, 'url': url}
    try:
        entry['dns_ip'] = socket.gethostbyname(host)
        entry['dns'] = 'OK'
    except Exception as e:
        entry['dns'] = f'FAIL {type(e).__name__}: {e}'
    res = fetch(url, 4096)
    entry['https'] = {k: res[k] for k in ('ok', 'status', 'final_url', 'content_type', 'bytes')}
    if 'error' in res:
        entry['https']['error'] = res['error']
    entry['html_sniff'] = res['body'][:200].decode('utf-8', 'replace').replace('\n', ' ')
    rob = fetch(f'https://{host}/robots.txt', 32768)
    entry['robots'] = {k: rob[k] for k in ('ok', 'status', 'bytes')}
    if 'error' in rob:
        entry['robots']['error'] = rob['error']
    if rob['body']:
        (HERE / f'robots-{name}.txt').write_bytes(rob['body'])
    report['shops'].append(entry)

(HERE / 'probe-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
print(json.dumps({'done': True, 'shops': [s['shop'] for s in report['shops']]}))

"""Offline six-page acceptance runner; Python 3.9, standard library only."""
import argparse
import csv
import hashlib
import json
import sqlite3
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

HOSTS = {'bstn.com': 2, 'notre-shop.com': 2, 'patta.nl': 2}

def prepare(manifests, target):
    target = Path(target).resolve()
    if target.exists():
        raise ValueError('new manifest required')
    entries = {}
    for source in manifests:
        source = Path(source).resolve()
        if source.parent != target.parent:
            raise ValueError('source and merged manifests must share directory')
        with source.open(encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            if not {'html_file', 'product_url'}.issubset(reader.fieldnames or []):
                raise ValueError('manifest requires html_file,product_url')
            for row in reader:
                url = row['product_url'].strip()
                u = urlparse(url)
                host = (u.hostname or '').removeprefix('www.')
                if u.scheme != 'https' or host not in HOSTS or u.username or u.password or u.fragment:
                    raise ValueError('invalid source URL')
                path = (source.parent / row['html_file']).resolve()
                if source.parent not in path.parents or not path.is_file():
                    raise ValueError('missing HTML or path outside input directory')
                if path.stat().st_size > 3000000:
                    raise ValueError('HTML exceeds parser limit')
                if url in entries and entries[url] != path:
                    raise ValueError('same URL references different files')
                entries[url] = path
    if len(entries) != 6 or Counter((urlparse(u).hostname or '').removeprefix('www.') for u in entries) != Counter(HOSTS):
        raise ValueError('requires exactly six distinct URLs: BSTN 2, Notre 2, Patta 2')
    if len(set(entries.values())) != 6:
        raise ValueError('six distinct saved HTML files required')
    with target.open('x', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['html_file', 'product_url'])
        writer.writeheader()
        writer.writerows({'html_file': str(p.relative_to(target.parent)), 'product_url': u} for u, p in entries.items())
    return entries

def execute(manifests, manifest, db, out):
    from collector import parse
    from merchant_to_channels import run
    db, out = Path(db).resolve(), Path(out).resolve()
    if db.exists() or out.exists():
        raise ValueError('DB and output must both be new')
    entries = prepare(manifests, manifest)
    pages = []
    expected = {}
    for index, (url, path) in enumerate(entries.items(), 1):
        rows = parse(path.read_text(encoding='utf-8'), url)
        if not rows or any(not r.get('brand', '').strip() for r in rows):
            raise ValueError('page has zero rows or missing brand: page %s' % index)
        keys = {(r.get('product_url'), r.get('sku'), r.get('size')) for r in rows}
        if len(keys) != len(rows):
            raise ValueError('duplicate stage identity: page %s' % index)
        expected[url] = keys
        pages.append({'page': index, 'host': urlparse(url).hostname, 'html_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'parsed': len(rows)})
    result = run(manifest, db, out)
    stats = result.get('db_stage', result.get('stage', {}))
    failures = []
    with sqlite3.connect(str(db)) as conn:
        actual = conn.execute('SELECT source_url,merchant_sku,size,brand,decision FROM merchant_evidence').fetchall()
    for page, url in zip(pages, entries):
        saved = [r for r in actual if r[0] == url]
        page['stored'] = len(saved)
        page['pass'] = ({r[:3] for r in saved} == expected[url] and all(r[3].strip() and r[4] == 'HOLD' for r in saved))
        if not page['pass']:
            failures.append('page_identity_or_hold_mismatch:%s' % page['page'])
    total = sum(p['parsed'] for p in pages)
    if stats.get('accepted') != total or stats.get('rejected') != 0 or len(actual) != total:
        failures.append('stage_counts')
    if result.get('published') != 0 or result.get('approved_for_import') is not False:
        failures.append('publication_gate')
    report = {'verdict': 'FAIL' if failures else 'PASS', 'scope': 'six pages parse AND stage only', 'pages': pages, 'parsed': total, 'stage': stats, 'published': result.get('published'), 'approved_for_import': result.get('approved_for_import'), 'failures': failures}
    (out / 'six_page_acceptance.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-manifest', action='append', required=True)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--db', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    report = execute(args.source_manifest, args.manifest, args.db, args.out)
    print(json.dumps(report))
    raise SystemExit(0 if report['verdict'] == 'PASS' else 1)

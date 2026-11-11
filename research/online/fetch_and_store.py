#!/usr/bin/env python3
"""BSTN single-product verification on the iMac (stdlib only).
1) Read BSTN's published sitemap -> one real product URL.
2) Fetch that product page once; save HTML.
3) Parse with collector.py (JSON-LD) -> candidates.csv.
4) Load CSV rows into SQLite, read back count (chain verification).
Writes fetch-report.json with all outcomes."""
import gzip, io, json, re, sqlite3, urllib.request, urllib.error, csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 '
      '(KHTML, like Gecko) Version/17.4 Safari/605.1.15')
rep = {'steps': {}}


def get(url, limit):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read(limit)
        if r.headers.get('Content-Encoding') == 'gzip' or url.endswith('.gz'):
            try:
                data = gzip.GzipFile(fileobj=io.BytesIO(data)).read(limit)
            except Exception:
                pass
        return r.status, r.geturl(), data


# 1) sitemap -> product URL
status, _, idx = get('https://media.bstn.com/sitemap/eu_en/sitemap.xml', 2_000_000)
locs = re.findall(r'<loc>([^<]+)</loc>', idx.decode('utf-8', 'replace'))
rep['steps']['sitemap_index'] = {'status': status, 'children': len(locs)}
product_url = None
tried = []
for child in locs:
    if product_url:
        break
    if not child.endswith(('.xml', '.xml.gz')):
        continue
    tried.append(child)
    try:
        s2, _, body = get(child, 6_000_000)
    except Exception as e:
        rep['steps'].setdefault('child_errors', []).append(f'{child}: {type(e).__name__} {e}')
        continue
    urls = re.findall(r'<loc>([^<]+)</loc>', body.decode('utf-8', 'replace'))
    rep['steps'].setdefault('sample_urls', urls[:15])
    for u in urls:
        if u.startswith('https://www.bstn.com/') and '/p/' in u:
            product_url = u
            rep['steps']['child_sitemap'] = {'url': child, 'status': s2, 'urls': len(urls)}
            break
rep['steps']['child_tried'] = tried[:5]
rep['product_url'] = product_url

if product_url:
    # 2) fetch product page once
    status, final_url, html = get(product_url, 4_000_000)
    (HERE / 'bstn_product.html').write_bytes(html)
    text = html.decode('utf-8', 'replace')
    rep['steps']['product_fetch'] = {
        'status': status, 'final_url': final_url, 'bytes': len(html),
        'ld_json_blocks': text.count('application/ld+json'),
        'has_product_type': '"@type":"Product"' in text.replace(' ', '') or '"@type": "Product"' in text,
    }
    # 3) parse with collector.py
    import collector
    rows = collector.parse(text, product_url)
    out_csv = HERE / 'candidates.csv'
    fields = ['product_id', 'shop', 'brand', 'sku', 'name', 'color', 'size', 'price',
              'currency', 'availability_claim', 'product_url', 'source_url',
              'observed_utc', 'source_mode', 'gate', 'hold_reasons', 'auto_publish']
    with open(out_csv, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows([{k: collector.csvsafe(r[k]) for k in fields} for r in rows])
    rep['steps']['parse'] = {'rows': len(rows),
                             'sample': rows[:3]}
    # 4) SQLite sink + readback
    db = HERE / 'nexus_collect.db'
    if db.exists():
        db.unlink()
    con = sqlite3.connect(db)
    con.execute('CREATE TABLE candidates (product_id TEXT, shop TEXT, brand TEXT, sku TEXT,'
                ' name TEXT, color TEXT, size TEXT, price TEXT, currency TEXT,'
                ' availability_claim TEXT, product_url TEXT, source_url TEXT,'
                ' observed_utc TEXT, source_mode TEXT, gate TEXT, hold_reasons TEXT,'
                ' auto_publish TEXT)')
    with open(out_csv, encoding='utf-8-sig', newline='') as f:
        for row in csv.DictReader(f):
            con.execute('INSERT INTO candidates VALUES (%s)' % ','.join('?' * len(fields)),
                        [row[k] for k in fields])
    con.commit()
    cnt = con.execute('SELECT COUNT(*) FROM candidates').fetchone()[0]
    gate = con.execute('SELECT DISTINCT gate FROM candidates').fetchall()
    con.close()
    rep['steps']['sqlite'] = {'db_rows': cnt, 'gates': [g[0] for g in gate]}

(HERE / 'fetch-report.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding='utf-8')
print(json.dumps({'done': True, 'product_url': product_url,
                  'rows': rep.get('steps', {}).get('parse', {}).get('rows')}))

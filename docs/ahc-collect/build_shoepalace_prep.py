#!/usr/bin/env python3
"""Shoe Palace 3ファイル -> WooCommerceインポート用CSV（準備用）変換スクリプト。
見本: woo-products-import.csv の20列形式に合わせる。
価格式: 仕入総額 = USD*158*1.02 + 2200 + 1500 + 60 / 出品価格 = 仕入総額/0.745 を100円単位で切り上げ
"""
import csv, json, math, os

BASE = os.path.expanduser('~/workspace/fl-scrape')
FILES = [
    ('shoepalace-ugg_raw.json', 'shoepalace-ugg-all.csv', 'UGG'),
    ('shoepalace-hoka_raw.json', 'shoepalace-hoka-all.csv', 'HOKA'),
    ('shoepalace-vans-premium-old-skool-36_raw.json', 'shoepalace-vans-premium-old-skool-36-all.csv', 'Vans'),
]
COLUMNS = ['ID','Type','SKU','Name','Published','Visibility in catalog','Short description',
           'Description','Regular price','Categories','Images','Attribute 1 name',
           'Attribute 1 value(s)','Attribute 1 visible','Attribute 1 global','Parent',
           'Attribute 1 value','Stock','In stock?','Brand']
BRAND_FIX = {'VANS': 'Vans'}

def to_jpy(usd):
    total = usd * 158 * 1.02 + 2200 + 1500 + 60
    return int(math.ceil((total / 0.745) / 100.0) * 100), total

out_rows = []
stats = {}
details = {'oos_products': [], 'flash': [], 'examples': [], 'mismatch': []}

for raw_name, csv_name, _ in FILES:
    with open(os.path.join(BASE, raw_name)) as f:
        products = json.load(f)['products']
    with open(os.path.join(BASE, csv_name), newline='', encoding='utf-8-sig') as f:
        csv_by_id = {r['productId']: r for r in csv.DictReader(f)}
    st = {'products': 0, 'in_stock_products': 0, 'oos_products': 0,
          'variants': 0, 'variants_avail': 0, 'sale': 0}
    for p in products:
        pid = str(p['id'])
        crow = csv_by_id.get(pid)
        if crow is None:
            details['mismatch'].append(f"{raw_name}: productId {pid} がCSVに無い")
            continue
        variants = sorted(p['variants'], key=lambda v: v['position'])
        avail = [v for v in variants if v['available']]
        # CSV側との整合チェック
        if int(crow['variantsAvailable']) != len(avail):
            details['mismatch'].append(
                f"{p['title']}: CSV variantsAvailable={crow['variantsAvailable']} vs raw実数={len(avail)}")
        usd = float(variants[0]['price'])
        if abs(float(crow['priceMin']) - usd) > 0.001:
            details['mismatch'].append(f"{p['title']}: CSV priceMin={crow['priceMin']} vs raw price={usd}")
        is_sale = any(v['compare_at_price'] not in (None, '', '0.00') and float(v['compare_at_price']) > float(v['price']) for v in variants)
        jpy, total = to_jpy(usd)
        parent_sku = 'SP-' + pid
        brand = BRAND_FIX.get(p['vendor'], p['vendor'])
        sizes = ['US ' + v['option1'] for v in variants]
        images = ','.join(img['src'] for img in p['images'])
        flash_tags = [t.replace('Code_', '') for t in p['tags'] if t.startswith('Code_FLASH')]
        if flash_tags:
            details['flash'].append({'title': p['title'], 'pid': pid, 'codes': flash_tags,
                                     'handle': p['handle']})
        st['products'] += 1
        st['variants'] += len(variants)
        st['variants_avail'] += len(avail)
        if is_sale:
            st['sale'] += 1
        if avail:
            st['in_stock_products'] += 1
        else:
            st['oos_products'] += 1
            details['oos_products'].append({'file': raw_name, 'title': p['title'],
                                            'pid': pid, 'url': crow['url'],
                                            'variants': len(variants), 'usd': usd, 'jpy': jpy})
        if len(details['examples']) < 100:  # 後で選ぶため全件候補を保持
            details['examples'].append({'file': raw_name, 'title': p['title'], 'usd': usd,
                                        'total': round(total, 2), 'jpy': jpy, 'sale': is_sale,
                                        'compare': variants[0]['compare_at_price']})
        # 親行
        row = {c: '' for c in COLUMNS}
        row.update({'Type': 'variable', 'SKU': parent_sku, 'Name': p['title'],
                    'Published': '1', 'Visibility in catalog': 'visible',
                    'Description': crow['description_en'], 'Regular price': str(jpy),
                    'Images': images, 'Attribute 1 name': 'サイズ',
                    'Attribute 1 value(s)': ','.join(sizes),
                    'Attribute 1 visible': '1', 'Attribute 1 global': '1',
                    'Brand': brand})
        out_rows.append(row)
        # バリエーション行
        for v, sz in zip(variants, sizes):
            vr = {c: '' for c in COLUMNS}
            vr.update({'Type': 'variation', 'SKU': v['sku'], 'Published': '1',
                       'Visibility in catalog': 'visible', 'Regular price': str(jpy),
                       'Attribute 1 name': 'サイズ', 'Attribute 1 value(s)': sz,
                       'Parent': parent_sku, 'Attribute 1 value': sz,
                       'In stock?': '1' if v['available'] else '0'})
            out_rows.append(vr)
    stats[raw_name] = st

out_path = os.path.join(BASE, 'shoepalace-woo-import-prep.csv')
with open(out_path, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=COLUMNS)
    w.writeheader()
    w.writerows(out_rows)

print("output rows:", len(out_rows), "->", out_path)
print(json.dumps(stats, ensure_ascii=False, indent=1))
print("mismatches:", details['mismatch'])
print("flash count:", len(details['flash']))
with open(os.path.join(BASE, '_prep_details.json'), 'w') as f:
    json.dump(details, f, ensure_ascii=False, indent=1)

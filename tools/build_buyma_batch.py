#!/usr/bin/env python3
"""Offline BUYMA batch generator. Explicit local schema mapping; never publishes.
Usage: python3 build_buyma_batch.py --input selected.csv --output new_dir --config local.json
See build_buyma_batch.md for configuration. No third-party dependencies.
"""
import argparse
import csv
import json
import re
import sys
import tempfile
from pathlib import Path
from decimal import Decimal

ROOT=Path(__file__).resolve().parents[1]
CM=ROOT/'collector/cm-v8'

def read(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:
        r=csv.DictReader(f)
        if not r.fieldnames or len(set(r.fieldnames))!=len(r.fieldnames):
            raise ValueError('invalid header: '+str(path))
        rows=list(r)
        if any(None in x or None in x.values() for x in rows):
            raise ValueError('malformed CSV: '+str(path))
        return r.fieldnames,rows

def required(row,key):
    value=row.get(key,'').strip()
    if not value:
        raise ValueError('missing '+key)
    return value

def norm(s):
    s=re.sub(r'^US\s*','',s.strip().upper())
    m=re.fullmatch(r'(\d+(?:\.\d+)?)([CY]?)',s)
    if not m:
        raise ValueError('unsupported US size: '+s)
    return format(Decimal(m[1]).normalize(),'f')+m[2]

def dept(s):
    v={'men':'Men','women':'Women','kids':'Kids'}.get(s.strip().lower())
    if not v:
        raise ValueError('unknown department: '+s)
    return v

def chart_add(index,key,row):
    cm=Decimal(required(row,'cm'))
    if not cm.is_finite() or cm<=0:
        raise ValueError('invalid cm')
    source=required(row,'source_url')
    if not source.startswith('https://'):
        raise ValueError('invalid size source')
    val=(format(cm.normalize(),'f'),source)
    if key in index and index[key][0]!=val[0]:
        raise ValueError('conflicting size chart: '+str(key))
    index[key]=val

def charts(brand,cfg):
    generic={}
    scoped={}
    age={}
    quarantine=set()
    if brand=='UGG':
        for r in read(CM/'ugg-adults-official-chart-v8.csv')[1]:
            chart_add(generic,(dept(r['department']),norm(r['size_original'])),r)
        for r in read(CM/'cm-generic-combined-v8.csv')[1]:
            if r['brand']=='UGG' and r['department']=='Kids':
                chart_add(generic,('Kids',norm(r['size_original'])),r)
        for r in read(CM/'ugg-kids-age-evidence-v8.csv')[1]:
            if r['verdict']=='CONSISTENT':
                age[r['product_id']]=set(r['matched_sizes'].split())
        for r in read(CM/'ugg-kids-quarantine-v8.csv')[1]:
            quarantine.add(required(r,'variant_id'))
    else:
        for r in read(cfg['size_chart'])[1]:
            if r['brand'].upper()!=brand:
                continue
            key=(dept(r['department']),norm(r['size_original']))
            if r.get('product_id','').strip():
                chart_add(scoped,(r['product_id'],)+key,r)
            else:
                chart_add(generic,key,r)
    return generic,scoped,age,quarantine

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--config',required=True,type=Path)
    a=p.parse_args()
    config=json.loads(a.config.read_text(encoding='utf-8'))
    selected=read(a.input)[1]
    skus=[required(r,config.get('selection_sku','sku')) for r in selected]
    if not skus or len(set(skus))!=len(skus):
        raise ValueError('empty or duplicate selection')
    products={}
    for brand,cfg in config['brands'].items():
        brand=brand.upper()
        if brand=='CONVERSE':
            raise ValueError('CONVERSE BUYMA disabled')
        if brand=='UGG' and str(cfg['brand_id'])!='89':
            raise ValueError('UGG brand ID must be 89')
        if not str(cfg['brand_id']).isdigit():
            raise ValueError('invalid brand ID')
        fields,rows=read(cfg['source'])
        mapping=cfg['columns']
        needed=('sku','product_id','variant_id','department','size','stock','category_key','price')
        if any(k not in mapping or mapping[k] not in fields for k in needed):
            raise ValueError('missing source column mapping: '+brand)
        g,s,age,q=charts(brand,cfg)
        for row in rows:
            sku=required(row,mapping['sku'])
            if sku not in skus:
                continue
            d=dept(required(row,mapping['department']))
            pid=required(row,mapping['product_id'])
            vid=required(row,mapping['variant_id'])
            size=norm(required(row,mapping['size']))
            stock=required(row,mapping['stock'])
            if stock not in cfg['stock_values']:
                raise ValueError('unknown stock value: '+stock)
            if not cfg['stock_values'][stock]:
                continue
            if vid in q:
                raise ValueError('quarantined variant: '+vid)
            if brand=='UGG' and d=='Kids' and size not in age.get(pid,set()):
                raise ValueError('UGG Kids age/size not verified: '+pid+' '+size)
            cm,source=s.get((pid,d,size),g.get((d,size),(None,None)))
            if cm is None:
                raise ValueError('missing official size: '+sku+' '+size)
            category=str(cfg['categories'][required(row,mapping['category_key'])])
            if not category.isdigit():
                raise ValueError('invalid category ID')
            price=Decimal(required(row,mapping['price']))
            if not price.is_finite() or price<=0 or price!=price.to_integral_value():
                raise ValueError('invalid approved JPY price: '+sku)
            search=cfg['search_sizes'].get(d,{}).get(cm)
            if search is None or not str(search).strip():
                raise ValueError('missing BUYMA search-size mapping: '+d+' '+cm)
            derived={'sku':sku,'brand':brand,'brand_id':str(cfg['brand_id']),
                     'category_id':category,'size_original':size,'size_cm':cm,
                     'search_size':str(search),'size_source':source,'price_jpy':str(int(price)),
                     'product_id':pid,'variant_id':vid}
            output={}
            for field,spec in config['output_columns'].items():
                if 'derived' in spec:
                    output[field]=derived[spec['derived']]
                elif 'source' in spec:
                    output[field]=required(row,spec['source'])
                elif 'literal' in spec:
                    output[field]=str(spec['literal'])
                else:
                    raise ValueError('invalid output mapping: '+field)
            products.setdefault(sku,[]).append((derived,output))
    if set(products)!=set(skus):
        raise ValueError('missing sellable SKU: '+str(set(skus)-set(products)))
    ordered=[pair for sku in skus for pair in products[sku]]
    keys=[(d['sku'],d['variant_id']) for d,_ in ordered]
    if len(keys)!=len(set(keys)):
        raise ValueError('duplicate variant')
    for sku in skus:
        if len({(d['brand'],d['product_id'],d['category_id'],d['price_jpy']) for d,_ in products[sku]})!=1:
            raise ValueError('inconsistent product identity/category/price: '+sku)
    if a.output.exists():
        raise ValueError('output already exists')
    with tempfile.TemporaryDirectory(dir=a.output.parent) as tmp:
        folder=Path(tmp)/'result'
        folder.mkdir()
        for name,fields,rows in [('listing.csv',list(config['output_columns']),[o for _,o in ordered]),
                                  ('size_evidence.csv',list(ordered[0][0]),[d for d,_ in ordered])]:
            with (folder/name).open('w',encoding='utf-8-sig',newline='') as f:
                w=csv.DictWriter(f,fieldnames=fields)
                w.writeheader()
                w.writerows(rows)
        folder.rename(a.output)
    print(json.dumps({'products':len(skus),'variants':len(ordered),'output':str(a.output)},ensure_ascii=False))

if __name__=='__main__':
    try:
        main()
    except (ValueError,KeyError,OSError,ArithmeticError) as e:
        sys.exit(str(e))

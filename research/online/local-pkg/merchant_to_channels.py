"""One command: locally saved permitted merchant HTML -> evidence -> both channel review exports.
No network, account access, publication or WooCommerce writes. Python 3.9 stdlib.
"""
import argparse
import csv
import json
import sqlite3
from pathlib import Path
from collector import parse
from production_pipeline import stage, profit_review
from channel_ready_v4 import export as channel_export

FIELDS = ['product_url','product_id','shop','brand','name','sku','manufacturer_sku','color','size','price','currency','availability_claim','observed_utc','image_urls','description','category','ship_from','shipping_cost','import_tax','partner_fee','international_shipping','platform_fee_rate','fx_jpy','selling_price_jpy','image_rights']

def run(manifest, db, out):
    manifest=Path(manifest).resolve(); out=Path(out).resolve(); db=Path(db).resolve()
    if not manifest.is_file():raise FileNotFoundError(str(manifest))
    with manifest.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or not {'html_file','product_url'}.issubset(reader.fieldnames):
            raise ValueError('manifest requires html_file,product_url')
        entries=list(reader)
    if not entries:raise ValueError('empty manifest')
    out.mkdir(parents=True,exist_ok=True)
    records=[]; pages=[]
    for i,item in enumerate(entries,2):
        try:
            p=(manifest.parent/item['html_file']).resolve()
            if manifest.parent not in p.parents:raise ValueError('HTML path outside manifest directory')
            if p.stat().st_size>3_000_000:raise ValueError('HTML exceeds 3MB')
            rows=parse(p.read_text(encoding='utf-8'),item['product_url'])
            for r in rows:
                # Merchant-specific SKU is never promoted to manufacturer style code.
                rec={k:'' for k in FIELDS}
                rec.update({k:r.get(k,'') for k in FIELDS})
                rec['manufacturer_sku']='';rec['image_rights']=''
                records.append(rec)
            pages.append({'line':i,'url':item['product_url'],'sizes':len(rows),'status':'parsed' if rows else 'no_structured_product'})
        except (OSError,UnicodeError,ValueError,KeyError) as e:
            pages.append({'line':i,'status':'error','error':type(e).__name__+': '+str(e)[:200]})
    if not records:raise ValueError('No product rows extracted; see manifest/HTML and supported shops')
    staging=out/'extracted_evidence.csv'
    with staging.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(records)
    db.parent.mkdir(parents=True,exist_ok=True)
    conn=sqlite3.connect(str(db))
    try:
        saved=stage(conn,staging)
        profits=profit_review(conn,out)
    finally:conn.close()
    channels=channel_export(db,out)
    result={'pages':pages,'parsed_size_rows':len(records),'db_stage':saved,'products':channels['products'], 'woo_rows':channels['woocommerce_rows'],'buyma_rows':channels['buyma_rows'],'profit_rows':profits,'published':0,'approved_for_import':False,'status':'REVIEW_ONLY'}
    (out/'end_to_end_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--db',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    print(json.dumps(run(a.manifest,a.db,a.out),ensure_ascii=False))

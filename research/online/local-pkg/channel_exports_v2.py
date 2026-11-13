"""Conservative grouped, review-only WooCommerce and BUYMA exports. Python 3.9+."""
import argparse, csv, hashlib, json, sqlite3
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse
from channel_exports import records, safe

WOO = ['Type','SKU','Name','Published','Visibility in catalog','Description','Tax status','In stock?','Stock','Regular price','Categories','Images','Parent','Attribute 1 name','Attribute 1 value(s)','Attribute 1 visible','Attribute 1 global','Attribute 2 name','Attribute 2 value(s)','Attribute 2 visible','Attribute 2 global','Meta: _nexus_source_url','Meta: _nexus_verification']
BUYMA = ['review_id','source_url','merchant','brand','manufacturer_style_code','merchant_sku','product_name','color','sizes','size_stock_claims','price_source','currency','image_urls','description_draft','buyma_sale_price_jpy','listing_status','missing_information']


def key_for(r):
    # Without manufacturer identity and color, keep distinct merchant URLs apart.
    if r.get('manufacturer_sku') and r.get('color'):
        return ('verified_identity_candidate', r['brand'].casefold(), r['manufacturer_sku'].casefold(), r['color'].casefold())
    return ('source_only',r.get('url',''),r.get('merchant_sku',''))


def stable_id(group_key):
    return hashlib.sha256(json.dumps(group_key,ensure_ascii=False).encode()).hexdigest()[:16].upper()


def export(db, out):
    conn=sqlite3.connect('file:'+str(Path(db).resolve())+'?mode=ro',uri=True)
    try: source=list(records(conn))
    finally: conn.close()
    groups=defaultdict(list)
    for r in source: groups[key_for(r)].append(r)
    woo=[]; buyma=[]; issues=[]
    for k, rows in sorted(groups.items(),key=lambda x:str(x[0])):
        first=rows[0]; ident=stable_id(k); parent_sku='NX-REVIEW-'+ident
        sizes=sorted({str(r.get('size','')).strip() for r in rows if r.get('size')})
        missing=set()
        for r in rows:
            for field in ('manufacturer_sku','name','color','size','price'):
                if not r.get(field): missing.add(field)
            if r.get('verified')!='MANUALLY_VERIFIED':missing.add('verified_stock')
        missing.update(('image_rights','image_urls','description','shipping_cost','import_tax','selling_price','platform_fees'))
        name=' '.join(x for x in (first.get('brand',''),first.get('name','')) if x)
        # Only one hidden, unpublished parent per merchant product. No unsafe variation import.
        woo.append({'Type':'variable' if sizes else 'simple','SKU':parent_sku,'Name':name,'Published':'0','Visibility in catalog':'hidden','Tax status':'taxable','In stock?':'0','Stock':'0','Regular price':'','Images':'','Attribute 1 name':'Size' if sizes else '', 'Attribute 1 value(s)':', '.join(sizes),'Attribute 1 visible':'1' if sizes else '', 'Attribute 1 global':'0' if sizes else '', 'Meta: _nexus_source_url':first.get('url',''), 'Meta: _nexus_verification':'HOLD:'+','.join(sorted(missing))})
        for size in sizes:
            woo.append({'Type':'variation','SKU':parent_sku+'-'+hashlib.sha256(size.encode()).hexdigest()[:8].upper(),'Name':name+' '+size,'Published':'0','Visibility in catalog':'hidden','In stock?':'0','Stock':'0','Regular price':'','Parent':parent_sku,'Attribute 1 name':'Size','Attribute 1 value(s)':size,'Attribute 1 global':'0','Meta: _nexus_source_url':first.get('url',''),'Meta: _nexus_verification':'HOLD:unverified_stock_and_price'})
        buyma.append({'review_id':parent_sku,'source_url':first.get('url',''),'merchant':urlparse(first.get('url','')).hostname or '', 'brand':first.get('brand',''),'manufacturer_style_code':first.get('manufacturer_sku',''),'merchant_sku':first.get('merchant_sku',''),'product_name':first.get('name',''),'color':first.get('color',''),'sizes':' | '.join(sizes),'size_stock_claims':json.dumps({size:[r.get('stock','') for r in rows if r.get('size')==size] for size in sizes},ensure_ascii=False),'price_source':' | '.join(sorted({str(r.get('price','')) for r in rows if r.get('price')})),'currency':' | '.join(sorted({str(r.get('currency','')) for r in rows if r.get('currency')})),'listing_status':'HOLD','missing_information':','.join(sorted(missing))})
        issues.append({'review_id':parent_sku,'size_rows':len(rows),'unique_sizes':len(sizes),'missing':sorted(missing),'source_url':first.get('url','')})
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    for filename,fields,data in [('woocommerce_variation_review.csv',WOO,woo),('buyma_product_review.csv',BUYMA,buyma)]:
        with (out/filename).open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows([{field:safe(r.get(field,'')) for field in fields} for r in data])
    report={'source_size_rows':len(source),'grouped_products':len(groups),'woo_rows':len(woo),'buyma_products':len(buyma),'published':0,'import_approved':False,'warning':'WooCommerce variations are REVIEW ONLY. Validate WooCommerce CSV import on staging and confirm product identity, size, stock, price and image rights before use.','issues':issues}
    (out/'report_v2.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--db',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    r=export(a.db,a.out);print(json.dumps({k:v for k,v in r.items() if k!='issues'},ensure_ascii=False))

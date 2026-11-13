"""Read-only exports for WooCommerce staging and BUYMA listing preparation.
No auto listing. All items remain drafts; missing facts remain empty.
Python 3.9+ standard library only.
"""
import argparse,csv,sqlite3,json
from pathlib import Path
from urllib.parse import urlparse

WOO=['Type','SKU','Name','Published','Visibility in catalog','Short description','Description','Tax status','In stock?','Stock','Regular price','Categories','Images','Parent','Attribute 1 name','Attribute 1 value(s)','Attribute 1 visible','Attribute 1 global','Attribute 2 name','Attribute 2 value(s)','Attribute 2 visible','Attribute 2 global','Meta: _nexus_source_url','Meta: _nexus_verification']
BUYMA=['source_url','merchant','brand','manufacturer_style_code','merchant_sku','product_name','color','size','price_source','currency','stock_claim','image_urls','description_draft','category','buyma_sale_price_jpy','ship_from','delivery_estimate','listing_status','missing_information']

def safe(s):
 s=str(s or '')
 return "'"+s if s.lstrip().startswith(('=','+','-','@','\t','\r','\n')) else s

def table_exists(c,name):
 return bool(c.execute('SELECT 1 FROM sqlite_master WHERE type="table" AND name=?',(name,)).fetchone())

def records(c):
 if table_exists(c,'merchant_evidence'):
  for r in c.execute('SELECT source_url,merchant_sku,size,brand,name,color_claim,price_claim,currency,stock_claim,manufacturer_sku,verification_state FROM merchant_evidence'):
   yield dict(zip(('url','merchant_sku','size','brand','name','color','price','currency','stock','manufacturer_sku','verified'),r))
 if table_exists(c,'online_products') and table_exists(c,'online_offers'):
  for r in c.execute('''SELECT o.url,p.sku,p.size,p.brand,'',p.color,o.price,o.currency,o.availability_claim,'',o.verification_state FROM online_offers o JOIN online_products p ON p.id=o.product_id'''):
   yield dict(zip(('url','merchant_sku','size','brand','name','color','price','currency','stock','manufacturer_sku','verified'),r))

def make_exports(db,out):
 c=sqlite3.connect('file:'+str(Path(db).resolve())+'?mode=ro',uri=True)
 rows=list(records(c));c.close()
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 woo=[];buyma=[]
 for r in rows:
  # Merchant SKU is not necessarily a manufacturer style code. Never use it as a product SKU.
  missing=[k for k in ('manufacturer_sku','name','color','size','price') if not r.get(k)]
  if r.get('verified')!='MANUALLY_VERIFIED':missing.append('verified_stock')
  missing+=['image_rights','image_urls','description','shipping_cost','import_tax','selling_price','platform_fees']
  name=(r.get('brand','')+' '+r.get('name','')).strip()
  # No parent/variation rows unless reliable manufacturer identity + color are available.
  # Draft simple item is for manual review, never published.
  sku=('NEXUS-REVIEW-'+str(len(woo)+1).zfill(6))
  woo.append({'Type':'simple','SKU':sku,'Name':name,'Published':'0','Visibility in catalog':'hidden','Tax status':'taxable','In stock?':'0','Stock':'0','Regular price':'','Categories':'','Images':'','Meta: _nexus_source_url':r.get('url',''),'Meta: _nexus_verification':'HOLD:'+','.join(missing)})
  buyma.append({'source_url':r.get('url',''),'merchant':urlparse(r.get('url','')).hostname or '', 'brand':r.get('brand',''), 'manufacturer_style_code':r.get('manufacturer_sku',''), 'merchant_sku':r.get('merchant_sku',''),'product_name':r.get('name',''),'color':r.get('color',''),'size':r.get('size',''),'price_source':r.get('price',''),'currency':r.get('currency',''),'stock_claim':r.get('stock',''),'image_urls':'','description_draft':'','category':'','buyma_sale_price_jpy':'','ship_from':'','delivery_estimate':'','listing_status':'HOLD','missing_information':','.join(missing)})
 for filename,fields,data in [('woocommerce_drafts.csv',WOO,woo),('buyma_review.csv',BUYMA,buyma)]:
  with (out/filename).open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows([{k:safe(row.get(k,'')) for k in fields} for row in data])
 result={'rows':len(rows),'woocommerce_drafts':len(woo),'buyma_review':len(buyma),'published':0,'warning':'Review-only. WooCommerce draft CSV is not a validated variation import; do not import into production without staging verification.'}
 (out/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 return result

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--db',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 print(json.dumps(make_exports(a.db,a.out),ensure_ascii=False))

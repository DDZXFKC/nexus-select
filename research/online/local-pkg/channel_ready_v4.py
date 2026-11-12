"""Safe channel-specific review exports from V3 evidence DB. Python 3.9 stdlib."""
import argparse,csv,hashlib,json,sqlite3
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse
from channel_exports import safe

WOO=['Type','SKU','Name','Published','Visibility in catalog','Description','In stock?','Stock','Regular price','Categories','Images','Parent','Attribute 1 name','Attribute 1 value(s)','Attribute 1 visible','Attribute 1 global','Meta: _nexus_source_url','Meta: _nexus_review_status']
BUYMA=['review_id','source_url','merchant','brand','manufacturer_style_code','merchant_sku','product_name','color','sizes','size_stock_claims','source_price','currency','description_draft','image_urls','category','buyma_sale_price_jpy','listing_status','missing_information']

def _write(path, fields, rows):
 with path.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for row in rows:w.writerow({k:safe(row.get(k,'')) for k in fields})

def export(db,out):
 c=sqlite3.connect('file:'+str(Path(db).resolve())+'?mode=ro',uri=True)
 try:
  rows=c.execute('''SELECT m.source_url,m.merchant_sku,m.size,m.brand,m.name,m.color_claim,m.price_claim,m.currency,m.stock_claim,m.manufacturer_sku,m.verification_state,
  COALESCE(e.image_urls,''),COALESCE(e.description,''),COALESCE(e.category,''),COALESCE(e.image_rights,''),COALESCE(m.product_id,'')
  FROM merchant_evidence m LEFT JOIN product_enrichment e ON m.source_url=e.source_url AND m.merchant_sku=e.merchant_sku AND m.size=e.size ORDER BY m.source_url,m.merchant_sku,m.size''').fetchall()
 finally:c.close()
 groups=defaultdict(list)
 pid_by_url={}
 for r in rows:pid_by_url.setdefault(r[0],set()).add(r[15])
 for r in rows:
  # Never combine shops merely because a manufacturer SKU is claimed.
  # Page identity only when one non-empty product_id covers the whole page;
  # variant-level or legacy rows keep the merchant-SKU discriminator.
  disc=r[15] if len(pid_by_url[r[0]])==1 and r[15] else r[1]
  groups[(r[0],disc,r[5])].append(r)
 woo=[];buyma=[];audit=[]
 for key,items in sorted(groups.items()):
  r=items[0]; url,sku,_,brand,name,color,price,currency,_,mfr,verified,images,desc,category,rights,_pid=r
  ident=hashlib.sha256(json.dumps(key,ensure_ascii=False).encode()).hexdigest()[:16].upper(); parent='NX-HOLD-'+ident
  sizes=sorted({x[2] for x in items if x[2]})
  missing=set()
  if not mfr:missing.add('manufacturer_style_code')
  if not color:missing.add('color')
  if not name:missing.add('product_name')
  if not category:missing.add('category')
  if not desc:missing.add('description')
  if not images:missing.add('images')
  if rights.strip().upper() not in ('LICENSED','OWNED','PERMISSION_GRANTED'):missing.add('image_usage_permission')
  if any(x[10]!='MANUALLY_VERIFIED' for x in items):missing.add('verified_size_stock')
  missing.update(('channel_specific_price','shipping_and_tax_confirmation','platform_import_validation'))
  allowed_images=images if 'image_usage_permission' not in missing else ''
  title=' '.join(x for x in (brand,name,color) if x)
  woo.append({'Type':'variable' if sizes else 'simple','SKU':parent,'Name':title,'Published':'0','Visibility in catalog':'hidden','Description':desc,'In stock?':'0','Stock':'0','Regular price':'','Categories':category,'Images':allowed_images,'Attribute 1 name':'Size' if sizes else '', 'Attribute 1 value(s)':', '.join(sizes),'Attribute 1 visible':'1' if sizes else '', 'Attribute 1 global':'0' if sizes else '', 'Meta: _nexus_source_url':url,'Meta: _nexus_review_status':'HOLD'})
  for size in sizes:
   woo.append({'Type':'variation','SKU':parent+'-'+hashlib.sha256(size.encode()).hexdigest()[:8].upper(),'Name':title+' '+size,'Published':'0','Visibility in catalog':'hidden','In stock?':'0','Stock':'0','Regular price':'','Parent':parent,'Attribute 1 name':'Size','Attribute 1 value(s)':size,'Attribute 1 global':'0','Meta: _nexus_source_url':url,'Meta: _nexus_review_status':'HOLD'})
  claims={size:[{'stock_claim':x[8],'price':x[6],'currency':x[7]} for x in items if x[2]==size] for size in sizes}
  buyma.append({'review_id':parent,'source_url':url,'merchant':urlparse(url).hostname or '', 'brand':brand,'manufacturer_style_code':mfr,'merchant_sku':sku,'product_name':name,'color':color,'sizes':' | '.join(sizes),'size_stock_claims':json.dumps(claims,ensure_ascii=False),'source_price':price,'currency':currency,'description_draft':desc,'image_urls':allowed_images,'category':category,'buyma_sale_price_jpy':'','listing_status':'HOLD','missing_information':' | '.join(sorted(missing))})
  audit.append({'review_id':parent,'source_url':url,'size_count':len(sizes),'missing':sorted(missing),'rights_claim':rights,'note':'Not approved for upload or publication'})
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 _write(out/'woocommerce_review_v4.csv',WOO,woo);_write(out/'buyma_review_v4.csv',BUYMA,buyma)
 report={'input_size_rows':len(rows),'products':len(groups),'woocommerce_rows':len(woo),'buyma_rows':len(buyma),'published':0,'approved_for_import':False,'review':audit}
 (out/'channel_report_v4.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--db',required=True);p.add_argument('--out',required=True);a=p.parse_args();r=export(a.db,a.out);print(json.dumps({k:v for k,v in r.items() if k!='review'},ensure_ascii=False))

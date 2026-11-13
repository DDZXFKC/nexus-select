"""Stage 3 evidence gate. Offline only; never authorizes publication/import."""
import argparse,json,csv,re
from pathlib import Path
from datetime import datetime,timezone,timedelta
from collections import defaultdict
from stage2_review import digest,cost,COST_FIELDS,money
from stage2_integrate import require
from channel_ready_v4 import _write

def proof(p,now,max_age=None):
 if not isinstance(p,dict):return False
 if not all(isinstance(p.get(k),str) and p[k].strip() for k in ('source','reviewer','checked_at','reference')):return False
 try:
  t=datetime.fromisoformat(p['checked_at'].replace('Z','+00:00'))
  return t.tzinfo is not None and t<=now and (max_age is None or now-t<=max_age)
 except (ValueError,TypeError):return False

def evaluate(rows,evidence,now):
 ids={r['source_variant_id'] for r in rows}
 require(len(ids)==len(rows),'duplicate input variant')
 require(set(evidence)<=ids,'unknown evidence variant')
 result=[];identity={};variants={}
 for r in rows:
  require(r['decision']=='HOLD','unsafe input')
  e=evidence.get(r['source_variant_id'],{});missing=[];canonical=''
  i=e.get('identity',{})
  if proof(i,now) and i.get('authority')=='MANUFACTURER' and all(isinstance(i.get(k),str) and i[k].strip() for k in ('brand','style_code','colorway_code','size_system','size')):
   require(i['brand'].casefold()==r['brand'].casefold(),'brand conflict')
   require(i.get('source_variant_id')==r['source_variant_id'],'identity scope conflict')
   require(i.get('observed_size')==r['size'] and i.get('observed_color')==r['color'],'identity observation conflict')
   canonical=digest([i['brand'].strip().casefold(),i['style_code'].strip(),i['colorway_code'].strip()])
   key=(r['source_product_id'],r['color'])
   require(identity.setdefault(key,canonical)==canonical,'canonical identity conflict')
   vk=(canonical,i['size_system'],i['size'])
   require(variants.setdefault((r['source_product_id'],vk),r['source_variant_id'])==r['source_variant_id'],'canonical variant collision')
  else:missing.append('identity')
  s=e.get('stock',{})
  stock='UNKNOWN'
  if proof(s,now,timedelta(hours=24)) and s.get('method')=='PURCHASABILITY_CHECK':
   require(s.get('source_variant_id')==r['source_variant_id'],'stock scope conflict')
   require(s.get('state') in ('IN_STOCK','OUT_OF_STOCK'),'invalid stock state')
   claim=r['stock_claim'].rsplit('/',1)[-1]
   require(not (claim=='InStock' and s['state']=='OUT_OF_STOCK' or claim=='OutOfStock' and s['state']=='IN_STOCK'),'stock conflict')
   stock=s['state']
  if stock!='IN_STOCK':missing.append('purchasable_stock')
  image=r['detail']['fields'].get('image',{}).get('value')
  rights=e.get('image_rights',{})
  allowed=proof(rights,now) and rights.get('status') in ('OWNED','LICENSED','PERMISSION_GRANTED') and rights.get('image')==image and bool(image) and set(rights.get('channels',[]))>={'WooCommerce','BUYMA'}
  if not allowed:missing.append('image_rights')
  c=e.get('cost',{});calc={'cost_jpy':'','profit_jpy':''}
  if proof(c,now,timedelta(hours=24)) and c.get('currency')==r['currency'] and c.get('source_variant_id')==r['source_variant_id']:
   inputs=c.get('inputs',{})
   if all(k in inputs for k in COST_FIELDS):
    require(money(inputs['price'])==money(r['price']),'cost price conflict')
    calc=cost(inputs)
  if not calc['cost_jpy']:missing.append('cost')
  elif money(calc['cost_jpy'])>=money(c['inputs']['selling_price_jpy']) or float(calc['profit_jpy'])<=0:missing.append('positive_profit')
  for channel in ('WooCommerce','BUYMA'):
   p=e.get('platform',{}).get(channel,{})
   if not (proof(p,now) and p.get('source_variant_id')==r['source_variant_id'] and p.get('status')=='VALIDATED' and p.get('artifact_hash')==digest(r) and p.get('category') and p.get('size_guide_reference')):missing.append(channel+'_validation')
  result.append(dict(source_variant_id=r['source_variant_id'],canonical_product_id=canonical,stock=stock,image_rights='EVIDENCE_RECORDED' if allowed else 'UNKNOWN',**calc,missing=missing,decision='HOLD',review_complete=not missing))
 return result

def validate_exports(rows,woo,buyma,mapping):
 require(len(mapping)==len(rows),'mapping count')
 ids={r['source_variant_id'] for r in rows}
 require({m['source_variant_id'] for m in mapping}==ids,'mapping mismatch')
 bysku={r['SKU']:r for r in woo}
 require(len(bysku)==len(woo) and all(bysku),'duplicate SKU')
 for r in woo:
  require(r['Published']=='0' and r['Visibility in catalog']=='hidden' and not r['Regular price'] and not r['Images'],'unsafe Woo row')
  if r['Type']=='variation':require(r['Parent'] in bysku and bysku[r['Parent']]['Type']=='variable','invalid parent')
 for m in mapping:
  require(m['new_sku'] in bysku and m['new_parent'] in bysku,'mapping SKU missing')
  r=bysku[m['new_sku']]
  require((r['Type']=='simple' and m['new_sku']==m['new_parent']) or (r['Type']=='variation' and r['Parent']==m['new_parent']),'mapping parent mismatch')
 require(len({r['review_id'] for r in buyma})==len(buyma),'duplicate BUYMA')
 require({r['review_id'] for r in buyma}=={m['new_parent'] for m in mapping},'BUYMA group mismatch')
 require(all(r['listing_status']=='HOLD' and not r['buyma_sale_price_jpy'] and not r['image_urls'] for r in buyma),'unsafe BUYMA row')
 return {'woo_rows':len(woo),'buyma_rows':len(buyma),'structural_validation':'PASS','actual_import':'NOT_RUN'}

def run(directory,evidence,out):
 d=Path(directory);out=Path(out)
 require(not out.exists(),'fresh output required')
 def load(n):return json.loads((d/n).read_text(encoding='utf-8'))
 def read(n):
  with (d/n).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
 rows=load('integrated_evidence.json')
 checks=validate_exports(rows,read('woocommerce_review.csv'),read('buyma_review.csv'),load('id_mapping.json'))
 e=json.loads(Path(evidence).read_text(encoding='utf-8')) if evidence else {}
 result=evaluate(rows,e,datetime.now(timezone.utc))
 out.mkdir()
 (out/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 report=dict(checks,rows=len(rows),hold=len(result),review_complete=sum(r['review_complete'] for r in result),canonical_verified=sum(bool(r['canonical_product_id']) for r in result),published=0,approved_for_import=False)
 (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--directory',required=True);p.add_argument('--evidence');p.add_argument('--out',required=True);a=p.parse_args();print(json.dumps(run(a.directory,a.evidence,a.out)))

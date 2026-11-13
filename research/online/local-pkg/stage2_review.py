"""Stage 2 review-only sidecar. Preserve baseline; no network or publication."""
import csv,json,hashlib,sqlite3,decimal,argparse
from pathlib import Path
from urllib.parse import urlparse
D=decimal.Decimal
def digest(x):
 return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def money(x):
 if x is None or x=='': raise ValueError('missing money')
 v=D(str(x))
 if not v.is_finite() or v<0: raise ValueError('invalid money')
 return v
COST_FIELDS=('price','local_tax','domestic_shipping','fx_jpy','fx_fee_jpy','international_shipping_jpy','duty_jpy','import_consumption_tax_jpy','partner_fee_jpy','channel_rate','channel_fixed_jpy','selling_price_jpy')
def cost(r):
 try:
  v={k:money(r.get(k)) for k in COST_FIELDS}
  if v['fx_jpy']<=0 or v['channel_rate']>1: raise ValueError('invalid rate')
  c=(v['price']+v['local_tax']+v['domestic_shipping'])*v['fx_jpy']+sum(v[k] for k in ('fx_fee_jpy','international_shipping_jpy','duty_jpy','import_consumption_tax_jpy','partner_fee_jpy'))
  p=v['selling_price_jpy']*(1-v['channel_rate'])-v['channel_fixed_jpy']-c
  return {'cost_jpy':str(c.quantize(D('.01'))),'profit_jpy':str(p.quantize(D('.01')))}
 except (ValueError,decimal.InvalidOperation,TypeError): return {'cost_jpy':'','profit_jpy':''}
def normalize(r):
 url=r['product_url']; host=urlparse(url).hostname
 if urlparse(url).scheme!='https' or not host: raise ValueError('invalid source')
 # Page scope is provisional, never a verified cross-store identity.
 product=digest([host,url])
 variant=digest([product,r.get('sku',''),r.get('color',''),r.get('size','')])
 name=r.get('name',''); brand=r.get('brand','')
 title=name if name.casefold().startswith(brand.casefold()+' ') else ' '.join(x for x in (brand,name) if x)
 return dict(r,source_product_id=product,source_variant_id=variant,canonical_product_id='',display_name=title,decision='HOLD')
def store(conn,r,capture_hash,captured_utc=None):
 conn.execute('CREATE TABLE IF NOT EXISTS observations (id TEXT PRIMARY KEY, variant TEXT NOT NULL, capture_hash TEXT NOT NULL, captured_utc TEXT, payload TEXT NOT NULL)')
 n=normalize(r)
 # Parse timestamps are not capture evidence and must not defeat replay dedup.
 payload={k:v for k,v in n.items() if k!='observed_utc'}
 key=digest([capture_hash,captured_utc,payload])
 conn.execute('INSERT OR IGNORE INTO observations VALUES (?,?,?,?,?)',(key,n['source_variant_id'],capture_hash,captured_utc,json.dumps(payload,ensure_ascii=False,sort_keys=True)))
 return n
def run(csvpath,manifest,db,out):
 from collections import Counter
 db=Path(db);out=Path(out)
 if db.exists() or out.exists():raise ValueError('new output paths required')
 manifest=Path(manifest).resolve()
 with manifest.open(encoding='utf-8-sig',newline='') as f:
  hashes={}
  for x in csv.DictReader(f):
   p=(manifest.parent/x['html_file']).resolve()
   if manifest.parent not in p.parents:raise ValueError('invalid path')
   hashes[x['product_url']]=hashlib.sha256(p.read_bytes()).hexdigest()
 with open(csvpath,encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
 if not rows:raise ValueError('empty input')
 out.mkdir(parents=True)
 with sqlite3.connect(str(db)) as conn:
  normalized=[store(conn,r,hashes[r['product_url']]) for r in rows]
  count=conn.execute('SELECT count(*) FROM observations').fetchone()[0]
  for r in rows:store(conn,r,hashes[r['product_url']])
  replay=conn.execute('SELECT count(*) FROM observations').fetchone()[0]
 report={'rows':len(rows),'observations':count,'replay_observations':replay,'variant_ids':len({r['source_variant_id'] for r in normalized}),'coverage':{k:sum(bool(r.get(k)) for r in rows) for k in rows[0]},'capture_time':'UNKNOWN','published':0,'approved_for_import':False,'status':'REVIEW_ONLY'}
 (out/'identity_review.json').write_text(json.dumps(normalized,ensure_ascii=False,indent=2),encoding='utf-8')
 (out/'stage2_sidecar_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser()
 for k in ('csv','manifest','db','out'):p.add_argument('--'+k,required=True)
 a=p.parse_args();print(json.dumps(run(a.csv,a.manifest,a.db,a.out)))

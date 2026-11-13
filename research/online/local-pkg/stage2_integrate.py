"""Stage 2 offline integration. Review artifacts only; no import or network."""
import argparse,csv,json,sqlite3,hashlib,re
from pathlib import Path
from collections import defaultdict
from urllib.parse import urlparse
from stage2_review import digest,cost,COST_FIELDS,money
from stage2_detail import extract
from channel_ready_v4 import WOO,BUYMA,_write

def require(ok,msg):
 if not ok:raise ValueError(msg)
def value(d,k):
 return d['fields'].get(k,{}).get('value')
def key(url,sku,size):return (url,str(sku or ''),str(size or ''))
def join(baseline,pages,hashes):
 index={}
 for b in baseline:
  k=key(b['product_url'],b['sku'],b['size'])
  require(k not in index,'duplicate baseline key');index[k]=b
 seen=set();out=[]
 for page in pages:
  url=page['url'];host=urlparse(url).hostname
  require(url in hashes,'unknown page')
  for d in page['rows']:
   require(d['decision']=='HOLD' and not d['canonical_product_id'] and d['image_rights']=='UNKNOWN','unsafe detail')
   require(all(f['source_url']==url and f['html_sha256']==hashes[url] for f in d['fields'].values()),'provenance mismatch')
   bstn=host in ('bstn.com','www.bstn.com')
   k=key(url,d['source_product_id'] if bstn else value(d,'merchant_sku'),value(d,'size') if bstn else value(d,'raw_title'))
   require(k in index and k not in seen,'unmatched or duplicate detail');seen.add(k);b=index[k]
   require(money(b['price'])==money(value(d,'price')) and b['currency']==value(d,'currency'),'price/currency mismatch')
   require(d['source_product_id'] and d['source_variant_id'],'missing source ID')
   pid=digest([host,d['source_product_id']]);vid=digest([pid,d['source_variant_id']])
   color=value(d,'color') or value(d,'color_candidate') or b.get('color') or ''
   require(not b.get('color') or not color or b['color']==color,'color conflict')
   stock=value(d,'stock_claim') or ''
   require(not b.get('availability_claim') or stock.rsplit('/',1)[-1]==b['availability_claim'].rsplit('/',1)[-1],'stock conflict')
   name=b['name'];brand=b['brand'];title=name if name.casefold().startswith(brand.casefold()+' ') else brand+' '+name
   out.append(dict(source_url=url,source_product_id=pid,source_variant_id=vid,merchant_product_id=d['source_product_id'],merchant_variant_id=d['source_variant_id'],legacy_product_id=b['product_id'],legacy_sku=b['sku'],legacy_size=b['size'],brand=brand,name=name,title=title,color=color,size=value(d,'size') or '',price=str(value(d,'price')),currency=b['currency'],stock_claim=stock,detail=d,canonical_product_id='',decision='HOLD',capture_hash=hashes[url],capture_time=None))
 require(seen==set(index),'missing baseline rows')
 require(len({r['source_variant_id'] for r in out})==len(out),'duplicate scoped variant')
 return out

def history(conn,rows):
 conn.execute('CREATE TABLE IF NOT EXISTS observations (id TEXT PRIMARY KEY, variant_id TEXT NOT NULL, capture_hash TEXT NOT NULL, payload TEXT NOT NULL)')
 for r in rows:
  conn.execute('INSERT OR IGNORE INTO observations VALUES (?,?,?,?)',(digest(r),r['source_variant_id'],r['capture_hash'],json.dumps(r,ensure_ascii=False,sort_keys=True)))
 return conn.execute('SELECT count(*) FROM observations').fetchone()[0]

def size_key(s):
 apparel={'XXS':0,'XS':1,'S':2,'M':3,'L':4,'XL':5,'XXL':6,'XXXL':7}
 if s.upper() in apparel:return (0,apparel[s.upper()],s)
 m=re.search(r'\d+(?:\.\d+)?',s)
 return (1,float(m.group()),s) if m else (2,0,s)

def exports(rows):
 groups=defaultdict(list)
 for r in rows:groups[(r['source_product_id'],r['color'])].append(r)
 woo=[];buyma=[];profits=[];mapping=[]
 for (pid,color),items in sorted(groups.items()):
  r=items[0]
  for field in ('brand','name','currency','source_url'):
   require(len({x[field] for x in items})==1,'group conflict '+field)
  # Explicit reviewed accessory identity only; no generic ONE SIZE inference.
  simple=(len(items)==1 and urlparse(r['source_url']).hostname in ('bstn.com','www.bstn.com') and r['merchant_product_id']=='0012650' and r['brand']=='Jason Markk' and r['size']=='ONE SIZE')
  sizes=sorted([x['size'] for x in items],key=size_key) if not simple else []
  require(simple or (all(sizes) and len(set(sizes))==len(sizes)),'ambiguous sizes')
  parent='NX2-'+digest([pid,color])[:24].upper()
  common={'Published':'0','Visibility in catalog':'hidden','In stock?':'0','Stock':'0','Regular price':'','Images':'','Meta: _nexus_source_url':r['source_url'],'Meta: _nexus_review_status':'HOLD'}
  woo.append(dict(common,Type='simple' if simple else 'variable',SKU=parent,Name=r['title'],**{'Attribute 1 name':'Size' if sizes else '', 'Attribute 1 value(s)':', '.join(sizes),'Attribute 1 visible':'1' if sizes else '', 'Attribute 1 global':'0' if sizes else ''}))
  claims=[]
  for x in items:
   sku=parent if simple else parent+'-'+x['source_variant_id'][:16].upper()
   if not simple:woo.append(dict(common,Type='variation',SKU=sku,Name=x['title']+' '+x['size'],Parent=parent,**{'Attribute 1 name':'Size','Attribute 1 value(s)':x['size'],'Attribute 1 global':'0'}))
   claims.append({'variant_id':x['source_variant_id'],'size':None if simple else x['size'],'price':x['price'],'currency':x['currency'],'stock_claim':x['stock_claim']})
   mapping.append({'legacy_product_id':x['legacy_product_id'],'legacy_sku':x['legacy_sku'],'legacy_size':x['legacy_size'],'source_url':x['source_url'],'new_parent':parent,'new_sku':sku,'source_variant_id':x['source_variant_id']})
   inputs={k:'' for k in COST_FIELDS};inputs['price']=x['price']
   profits.append(dict(source_variant_id=x['source_variant_id'],currency=x['currency'],**inputs,**cost(inputs),status='HOLD'))
  buyma.append(dict(review_id=parent,source_url=r['source_url'],merchant=urlparse(r['source_url']).hostname,brand=r['brand'],product_name=r['name'],color=color,sizes=' | '.join(sizes),size_stock_claims=json.dumps(claims,ensure_ascii=False),currency=r['currency'],listing_status='HOLD',missing_information='verified_identity | verified_stock | image_rights | description_rights | category_mapping | cost | channel_price | import_validation'))
 require(len({x['SKU'] for x in woo})==len(woo),'duplicate export SKU')
 return woo,buyma,profits,mapping

def run(manifest,baseline,detail,db,out):
 manifest=Path(manifest).resolve();db=Path(db);out=Path(out)
 require(not db.exists() and not out.exists(),'fresh paths required')
 hashes={};pages=[]
 with manifest.open(encoding='utf-8-sig',newline='') as f:
  for m in csv.DictReader(f):
   p=(manifest.parent/m['html_file']).resolve();url=m['product_url']
   require(manifest.parent in p.parents and url not in hashes,'invalid manifest')
   require(p.stat().st_size<=3000000,'HTML too large')
   raw=p.read_bytes();hashes[url]=hashlib.sha256(raw).hexdigest()
   rr=extract(raw,url);require(bool(rr),'empty extraction')
   pages.append({'url':url,'rows':rr,'count':len(rr)})
 require(pages==json.loads(Path(detail).read_text(encoding='utf-8')),'detail artifact differs from re-extraction')
 with open(baseline,encoding='utf-8-sig',newline='') as f:rows=join(list(csv.DictReader(f)),pages,hashes)
 woo,buyma,profits,mapping=exports(rows)
 out.mkdir()
 with sqlite3.connect(str(db)) as conn:
  n=history(conn,rows);replay=history(conn,rows)
 require(n==replay==len(rows),'history replay mismatch')
 _write(out/'woocommerce_review.csv',WOO,woo)
 _write(out/'buyma_review.csv',BUYMA,buyma)
 _write(out/'profit_review.csv',list(profits[0]),profits)
 for name,data in [('integrated_evidence',rows),('id_mapping',mapping)]:
  (out/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 report=dict(rows=len(rows),observations=n,replay=replay,products=len(buyma),woo_rows=len(woo),variable=sum(x['Type']=='variable' for x in woo),variations=sum(x['Type']=='variation' for x in woo),simple=sum(x['Type']=='simple' for x in woo),buyma_rows=len(buyma),profit_rows=len(profits),published=0,approved_for_import=False,status='REVIEW_ONLY')
 (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser()
 for k in ('manifest','baseline','detail','db','out'):p.add_argument('--'+k,required=True)
 a=p.parse_args();print(json.dumps(run(a.manifest,a.baseline,a.detail,a.db,a.out)))

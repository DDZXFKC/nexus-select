"""NEXUS SELECT evidence-first product catalog. Python >=3.9, stdlib only.
Saved HTML only: acquisition permission must be checked separately.
No publication, image copying, or network requests.
"""
import argparse
import csv
import datetime
import hashlib
import json
import re
import sqlite3
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
 id INTEGER PRIMARY KEY, brand TEXT NOT NULL, style_code TEXT NOT NULL,
 name TEXT, status TEXT NOT NULL DEFAULT 'HOLD',
 UNIQUE(brand,style_code)
);
CREATE TABLE IF NOT EXISTS evidence (
 id INTEGER PRIMARY KEY, product_id INTEGER, source_url TEXT NOT NULL,
 source_tier TEXT NOT NULL, fetched_at TEXT NOT NULL,
 payload TEXT NOT NULL, sha256 TEXT NOT NULL,
 FOREIGN KEY(product_id) REFERENCES products(id),
 UNIQUE(source_url,sha256)
);
CREATE TABLE IF NOT EXISTS offers (
 id INTEGER PRIMARY KEY, evidence_id INTEGER NOT NULL,
 seller TEXT, sku TEXT, size TEXT, price TEXT, currency TEXT,
 availability_claim TEXT, FOREIGN KEY(evidence_id) REFERENCES evidence(id)
);
"""
FIELDS = ['brand','style_code','name','status','source_url','source_tier',
          'fetched_at','merchant','merchant_sku','size','price','currency',
          'availability_claim','image_urls','description','category','color',
          'release_date','gender','needs_review']
TIERS = {'brand_official':0,'authorized_retailer':1,'other_retailer':2}

class Scripts(HTMLParser):
 def __init__(self):
  super().__init__();self.active=False;self.parts=[];self.current=[]
 def handle_starttag(self,tag,attrs):
  if tag=='script' and dict(attrs).get('type','').lower()=='application/ld+json':
   self.active=True;self.current=[]
 def handle_data(self,data):
  if self.active:self.current.append(data)
 def handle_endtag(self,tag):
  if tag=='script' and self.active:
   self.parts.append(''.join(self.current));self.active=False

def objects(value):
 if isinstance(value,list):
  for v in value:yield from objects(v)
 elif isinstance(value,dict):
  if value.get('@type')=='Product' or 'Product' in (value.get('@type') if isinstance(value.get('@type'),list) else []):
   yield value
  for key in ('@graph','mainEntity','itemListElement'):
   if key in value:yield from objects(value[key])

def plain(v):
 if isinstance(v,dict):return str(v.get('name') or v.get('value') or '')
 if isinstance(v,list):return ', '.join(filter(None,(plain(x) for x in v)))
 return str(v) if v is not None else ''

def extract(html):
 parser=Scripts();parser.feed(html);found=[]
 for raw in parser.parts:
  try:doc=json.loads(raw)
  except (ValueError,TypeError):continue
  for p in objects(doc):
   brand=plain(p.get('brand')).strip()
   offers=p.get('offers') or []
   if isinstance(offers,dict):offers=[offers]
   if not isinstance(offers,list):offers=[]
   if not offers:offers=[{}]
   for offer in offers:
    if not isinstance(offer,dict):continue
    image=p.get('image') or []
    if isinstance(image,str):image=[image]
    if not isinstance(image,list):image=[]
    found.append({'brand':brand,'name':plain(p.get('name')),
     'merchant_sku':plain(p.get('sku')),'style_code':'',
     'size':plain(offer.get('size') or p.get('size')),
     'price':plain(offer.get('price')),'currency':plain(offer.get('priceCurrency')),
     'availability_claim':plain(offer.get('availability')),
     'image_urls':json.dumps(image,ensure_ascii=False),
     'description':plain(p.get('description')),'category':plain(p.get('category')),
     'color':plain(p.get('color')),'release_date':plain(p.get('releaseDate')),
     'gender':plain(p.get('audience'))})
 return found

def valid_url(url):
 p=urlparse(url)
 if p.scheme!='https' or not p.hostname or p.username or p.password or p.port:
  raise ValueError('HTTPS merchant URL with hostname required')
 if p.hostname in ('localhost',) or p.hostname.endswith(('.local','.internal')):
  raise ValueError('private hostname')
 return p.hostname.lower()

def run(manifest,db,out):
 manifest=Path(manifest).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
 with manifest.open(newline='',encoding='utf-8-sig') as f:
  reader=csv.DictReader(f);required={'html_file','product_url','source_tier'}
  if not required.issubset(reader.fieldnames or []):raise ValueError('manifest requires '+','.join(sorted(required)))
  entries=list(reader)
 conn=sqlite3.connect(str(db));conn.executescript(SCHEMA)
 rows=[];errors=[];skipped=0
 try:
  for entry in entries:
   try:
    host=valid_url(entry['product_url'])
    tier=entry['source_tier']
    if tier not in TIERS:raise ValueError('invalid source_tier')
    path=(manifest.parent/entry['html_file']).resolve()
    if manifest.parent not in path.parents or not path.is_file():raise ValueError('missing or unsafe html_file')
    if path.stat().st_size>3000000:raise ValueError('HTML too large')
    html=path.read_text(encoding='utf-8');digest=hashlib.sha256(html.encode()).hexdigest()
    if conn.execute('SELECT 1 FROM evidence WHERE source_url=? AND sha256=?',(entry['product_url'],digest)).fetchone():
     skipped+=1;continue
    parsed=extract(html)
    if not parsed:raise ValueError('no JSON-LD Product found')
    fetched=datetime.datetime.now(datetime.timezone.utc).isoformat()
    for p in parsed:
     # Manufacturer style code must be independently confirmed; merchant SKU is not proof.
     style=(entry.get('verified_style_code') or '').strip().upper()
     brand=p['brand'].strip().casefold()
     product_id=None
     if brand and style:
      conn.execute('INSERT OR IGNORE INTO products(brand,style_code,name) VALUES(?,?,?)',(brand,style,p['name']))
      product_id=conn.execute('SELECT id FROM products WHERE brand=? AND style_code=?',(brand,style)).fetchone()[0]
     payload=json.dumps(p,ensure_ascii=False,sort_keys=True)
     # One evidence per page+hash; multiple size offers reference it.
     ev=conn.execute('SELECT id FROM evidence WHERE source_url=? AND sha256=?',(entry['product_url'],digest)).fetchone()
     if ev:ev_id=ev[0]
     else:
      ev_id=conn.execute('INSERT INTO evidence(product_id,source_url,source_tier,fetched_at,payload,sha256) VALUES(?,?,?,?,?,?)',
       (product_id,entry['product_url'],tier,fetched,payload,digest)).lastrowid
     conn.execute('INSERT INTO offers(evidence_id,seller,sku,size,price,currency,availability_claim) VALUES(?,?,?,?,?,?,?)',
      (ev_id,host,p['merchant_sku'],p['size'],p['price'],p['currency'],p['availability_claim']))
     rows.append({'brand':p['brand'],'style_code':style,'name':p['name'],'status':'HOLD',
      'source_url':entry['product_url'],'source_tier':tier,'fetched_at':fetched,'merchant':host,
      **{k:p[k] for k in ('merchant_sku','size','price','currency','availability_claim','image_urls','description','category','color','release_date','gender')},
      'needs_review':'YES' if not (brand and style) else 'YES: channel costs, image rights and stock not verified'})
    conn.commit()
   except (OSError,ValueError,UnicodeError,sqlite3.Error) as exc:
    conn.rollback();errors.append({'url':entry.get('product_url',''),'error':str(exc)})
  with (out/'evidence_review.csv').open('w',newline='',encoding='utf-8-sig') as f:
   w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
  report={'pages_requested':len(entries),'size_rows':len(rows),'skipped_unchanged_pages':skipped,
   'errors':errors,'products_identified':conn.execute('SELECT count(*) FROM products').fetchone()[0],
   'offers_total':conn.execute('SELECT count(*) FROM offers').fetchone()[0],
   'published':0,'approved_for_import':False}
  (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
  return report
 finally:conn.close()

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--manifest',required=True);a.add_argument('--db',required=True);a.add_argument('--out',required=True);v=a.parse_args()
 print(json.dumps(run(v.manifest,v.db,v.out),ensure_ascii=False))

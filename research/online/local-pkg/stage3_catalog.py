"""Permission-gated, resumable sitemap collector. No publication or external writes."""
import argparse,json,sqlite3,hashlib,time,re,urllib.request,urllib.error,urllib.robotparser
from urllib.parse import urlsplit,parse_qsl,urlencode,urlunsplit
from html.parser import HTMLParser
from pathlib import Path
from datetime import datetime,timezone
import xml.etree.ElementTree as ET
import io
from stage2_detail import extract as detail_extract,merge_candidates
from shopify_variants import ScriptReader,ld_products
from stage2_review import digest,money
from stage2_integrate import exports,require
from stage3_verify import evaluate,validate_exports
from channel_ready_v4 import WOO,BUYMA,_write
AGENT='AHC-CatalogReview/1.0'
class Stop(ValueError):pass
class ProductDataError(ValueError):pass
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*a,**kw):raise Stop('redirect: review required')
def utc():return datetime.now(timezone.utc).isoformat()
def scope(url,host):
 p=urlsplit(url)
 require(p.scheme=='https' and p.netloc==host and not p.fragment and not p.query,'URL outside approved scope')
 return url
SITEMAP_CAP=50*1024*1024
PRODUCT_CAP=10000000
def sitemap_scope(url,host):
 p=urlsplit(url)
 if host=='www.bstn.com' and p.netloc=='media.bstn.com':
  scope(url,'media.bstn.com')
  require(p.path.endswith('.xml') and not any(x in p.path for x in ('..','%','\\')),'invalid media sitemap path')
  return url
 return scope(url,host)
def listing_scope(url,host):
 p=urlsplit(url)
 require(host=='www.bstn.com' and p.scheme=='https' and p.netloc==host and not p.fragment,'listing host outside scope')
 require(re.fullmatch(r'/eu_en/(men|women|kids)/all-products',p.path),'listing path outside scope')
 q=parse_qsl(p.query,keep_blank_values=True,strict_parsing=True);d=dict(q)
 require(len(q)==len(d) and set(d)<= {'categories','page'},'listing query outside scope')
 require(re.fullmatch(r'(Men|Women|Kids)~All Products(?:~[A-Za-z0-9 &/-]+)*',d.get('categories','')),'invalid category')
 require(d['categories'].split('~')[0].lower()==p.path.split('/')[2],'gender mismatch')
 require('page' not in d or re.fullmatch(r'[1-9][0-9]{0,3}',d['page']),'invalid page')
 return url
def listing_page(seed,n):
 p=urlsplit(seed);q=dict(parse_qsl(p.query));q['page']=str(n)
 return urlunsplit((p.scheme,p.netloc,p.path,urlencode(q),''))
class NextData(HTMLParser):
 def __init__(self):
  super().__init__();self.active=False;self.parts=[];self.count=0
 def handle_starttag(self,tag,attrs):
  if tag=='script' and dict(attrs).get('id')=='__NEXT_DATA__':self.active=True;self.count+=1
 def handle_endtag(self,tag):
  if tag=='script':self.active=False
 def handle_data(self,data):
  if self.active:self.parts.append(data)
def listing_hits(raw,expected):
 p=NextData();p.feed(raw.decode('utf-8-sig'));require(p.count==1,'missing or duplicate NEXT_DATA')
 results=json.loads(''.join(p.parts))['props']['pageProps']['serverState']['initialResults']['magento2_eu_products']['results']
 require(isinstance(results,list) and len(results) in (1,2,3),'unexpected listing results shape')
 require(all(isinstance(x,dict) for x in results),'invalid listing result')
 if len(results)>1:
  require(all(type(x.get('page')) is int and x['page']==0 for x in results[1:]),'auxiliary listing pagination changed')
 r=results[0];n=r['nbHits'];pages=r['nbPages'];size=r['hitsPerPage'];hits=r['hits']
 require(all(type(x) is int for x in (n,pages,size,r['page'])) and size==96 and 0<n<=96000 and pages==(n+size-1)//size and r['page']==expected-1 and 1<=expected<=pages,'invalid pagination')
 require(isinstance(hits,list) and len(hits)==min(size,n-(expected-1)*size),'incomplete listing page')
 urls=[]
 for h in hits:
  u=h['url'];require(isinstance(u,str) and re.fullmatch(r'[pr]/[A-Za-z0-9._~-]+',u) and '..' not in u,'invalid product hit')
  urls.append('https://www.bstn.com/eu_en/'+u)
 require(len(set(urls))==len(urls),'duplicate page hits')
 return urls,n,pages
def discover_listings(cfg,fetch):
 products=set();excluded=set();count=0
 for seed in cfg['listing_seeds']:
  seen=set();total=None;pages=1;page=1
  while page<=pages:
   u=listing_page(seed,page);listing_scope(u,cfg['host'])
   urls,n,p=listing_hits(fetch.listing(u),page);count+=1
   if total is None:total=n;pages=p
   require((n,p)==(total,pages) and not seen.intersection(urls),'listing changed during discovery')
   seen.update(urls);page+=1
  require(len(seen)==total,'listing coverage mismatch')
  for u in seen:
   if urlsplit(u).path.startswith('/eu_en/r/'):
    excluded.add(u);continue
   require(re.fullmatch(cfg['product_path_regex'],urlsplit(u).path),'product outside configured scope')
   products.add(u)
 require(products,'no matching products')
 return sorted(products),count,len(excluded)
def policy(cfg):
 require(cfg['host'] in ('www.bstn.com','www.notre-shop.com','patta.nl'),'unsupported host')
 require(cfg.get('enabled') is True and cfg.get('permission_reference') and cfg.get('reviewer'),'permission not recorded')
 t=datetime.fromisoformat(cfg['reviewed_at'].replace('Z','+00:00'))
 require(t.tzinfo is not None and 0<=(datetime.now(timezone.utc)-t).total_seconds()<=86400,'permission stale')
 require(cfg['interval_seconds']>=5 and 1<=cfg['request_budget']<=10000,'unsafe limits')
 require(cfg.get('product_path_regex') and bool(cfg.get('sitemap_seeds'))!=bool(cfg.get('listing_seeds')),'choose exactly one discovery mode')
 for u in cfg.get('sitemap_seeds',[]):sitemap_scope(u,cfg['host'])
 for u in cfg.get('listing_seeds',[]):
  listing_scope(u,cfg['host']);require('page' not in dict(parse_qsl(urlsplit(u).query)),'seed must omit page')
class Fetch:
 def __init__(self,cfg):
  policy(cfg);self.cfg=cfg;self.n=0;self.last=0;self.opener=urllib.request.build_opener(NoRedirect());self.robots={};self.listed=set()
 def __call__(self,url):
  return self.read(url,'product')
 def sitemap(self,url):
  return self.read(url,'sitemap')
 def listing(self,url):
  return self.read(url,'listing')
 def read(self,url,kind):
  host=urlsplit(url).netloc
  if kind=='sitemap':
   sitemap_scope(url,self.cfg['host'])
   require(url in self.listed,'sitemap not discovered from approved index')
  elif kind=='listing':listing_scope(url,self.cfg['host'])
  elif kind=='robots':
   require(host==self.cfg['host'] or (self.cfg['host']=='www.bstn.com' and host=='media.bstn.com'),'robots host outside scope')
   scope(url,host);require(urlsplit(url).path=='/robots.txt','invalid robots path')
  else:scope(url,self.cfg['host'])
  if kind!='robots':
   require(host in self.robots and self.robots[host].can_fetch(AGENT,url),'robots disallows URL')
  require(self.n<self.cfg['request_budget'],'request budget reached')
  time.sleep(max(0,self.cfg['interval_seconds']-(time.monotonic()-self.last)))
  self.n+=1;self.last=time.monotonic()
  cap=SITEMAP_CAP if kind=='sitemap' else PRODUCT_CAP
  try:
   with self.opener.open(urllib.request.Request(url,headers={'User-Agent':AGENT,'Accept-Encoding':'identity'}),timeout=30) as r:
    require(r.status==200 and r.geturl()==url,'unexpected response')
    require(r.headers.get('Content-Encoding','identity').lower()=='identity','unsupported encoding')
    length=r.headers.get('Content-Length')
    if length is not None:require(0<=int(length)<=cap,'response too large')
    raw=r.read(cap+1);require(len(raw)<=cap,'response too large')
    if length is not None:require(len(raw)==int(length),'truncated response')
    return raw
  except urllib.error.HTTPError as e:raise Stop('HTTP '+str(e.code)+' '+url) from e
 def init_robots(self):
  hosts=[self.cfg['host']]
  if self.cfg['host']=='www.bstn.com' and not self.cfg.get('listing_seeds'):hosts.append('media.bstn.com')
  for host in hosts:
   raw=self.read('https://'+host+'/robots.txt','robots')
   lines=raw.decode('utf-8-sig').splitlines()
   require(any(line.lower().startswith('user-agent:') for line in lines),'invalid robots response')
   rp=urllib.robotparser.RobotFileParser();rp.parse(lines);self.robots[host]=rp
   delay=rp.crawl_delay(AGENT) or rp.crawl_delay('*') or 0
   self.cfg['interval_seconds']=max(self.cfg['interval_seconds'],delay)
   require(not rp.request_rate(AGENT) and not rp.request_rate('*'),'robots request-rate needs manual review')
   if host==self.cfg['host']:
    self.listed.update(line.split(':',1)[1].strip() for line in lines if line.lower().startswith('sitemap:'))
  for u in self.cfg.get('sitemap_seeds',[]):
   if urlsplit(u).netloc=='media.bstn.com':require(u in self.listed,'media seed not listed in storefront robots')
   self.listed.add(u)
def sitemap(raw):
 require(len(raw)<=SITEMAP_CAP,'sitemap too large')
 require(b'\x00' not in raw and b'<!DOCTYPE' not in raw.upper() and b'<!ENTITY' not in raw.upper(),'unsafe XML')
 root=None;kind=None;urls=[];depth=0
 for event,node in ET.iterparse(io.BytesIO(raw),events=('start','end')):
  if event=='start':
   depth+=1
   if depth==1:
    root=node;kind=node.tag.split('}')[-1]
    require(kind in ('sitemapindex','urlset'),'unknown sitemap format')
  else:
   if depth==2:
    expected='sitemap' if kind=='sitemapindex' else 'url'
    require(node.tag.split('}')[-1]==expected,'unexpected sitemap entry')
    loc=[x.text for x in node if x.tag.split('}')[-1]=='loc']
    require(len(loc)==1 and loc[0] and loc[0].strip(),'invalid sitemap loc')
    urls.append(loc[0].strip());require(len(urls)<=50000,'too many sitemap entries')
    root.remove(node);node.clear()
   depth-=1
 require(root is not None,'empty XML')
 return kind,urls
def discover(cfg,fetch):
 if cfg.get('listing_seeds'):return discover_listings(cfg,fetch)
 pending=list(cfg['sitemap_seeds']);seen=set();products=set();excluded=set()
 while pending:
  u=pending.pop(0);sitemap_scope(u,cfg['host'])
  if u in seen:continue
  seen.add(u);require(len(seen)<=1000,'too many sitemap files');kind,urls=sitemap(fetch.sitemap(u) if isinstance(fetch,Fetch) else fetch(u))
  for v in urls:
   if kind=='sitemapindex':
    sitemap_scope(v,cfg['host']);pending.append(v)
    if isinstance(fetch,Fetch):fetch.listed.add(v)
   elif urlsplit(v).netloc==cfg['host'] and re.fullmatch(cfg['product_path_regex'],urlsplit(v).path):
    products.add(scope(v,cfg['host']))
   else:excluded.add(v)
 require(products,'no matching products')
 return sorted(products),len(seen),len(excluded)
def extract(raw,url):
 rows=detail_extract(raw,url)
 if not rows:return rows
 p=ScriptReader();p.feed(raw.decode('utf-8-sig'))
 host=urlsplit(url).hostname;meta={}
 if host=='www.bstn.com':
  for x in ld_products(p.scripts):
   brand=x.get('brand');brand=brand.get('name') if isinstance(brand,dict) else brand
   k=str(x.get('sku') or '');pair=(brand,x.get('name'))
   require(k not in meta or meta[k]==pair,'metadata conflict');meta[k]=pair
 else:
  candidates={};decoder=json.JSONDecoder()
  for s in p.scripts:
   for m in re.finditer(r'\{',s):
    try:x,_=decoder.raw_decode(s[m.start():])
    except ValueError:continue
    if isinstance(x,dict) and x.get('id') and x.get('vendor') and isinstance(x.get('variants'),list) and x['variants']:
     candidates[json.dumps(x,sort_keys=True)]=x
  x=merge_candidates(list(candidates.values()))
  require(x is not None,'metadata ambiguity')
  meta[str(x['id'])]=(x.get('vendor'),x.get('title'))
 sha=hashlib.sha256(raw).hexdigest()
 for r in rows:
  brand,name=meta[r['source_product_id']]
  for k,v in [('brand',brand),('name',name)]:
   require(isinstance(v,str) and v.strip(),'missing metadata')
   r['fields'][k]=dict(value=v,path='Product metadata' if host=='www.bstn.com' else 'parent metadata',source_url=url,html_sha256=sha,status='OBSERVED')
 return rows
def init(c):
 c.executescript("""CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,host TEXT,scope_hash TEXT,complete INTEGER DEFAULT 0);
 CREATE TABLE IF NOT EXISTS queue(run TEXT,url TEXT,state TEXT DEFAULT 'PENDING',error TEXT,PRIMARY KEY(run,url));
 CREATE TABLE IF NOT EXISTS captures(run TEXT,url TEXT,hash TEXT,at TEXT,raw BLOB,PRIMARY KEY(run,url));
 CREATE TABLE IF NOT EXISTS observations(id TEXT PRIMARY KEY,variant TEXT,payload TEXT);
 CREATE TABLE IF NOT EXISTS latest(run TEXT,variant TEXT,url TEXT,payload TEXT,PRIMARY KEY(run,variant));""")
def prepare(c,run,cfg,urls):
 sig=digest([cfg['host'],cfg['product_path_regex'],cfg.get('listing_seeds') or cfg['sitemap_seeds'],urls])
 old=c.execute('SELECT scope_hash FROM runs WHERE id=?',(run,)).fetchone()
 require(not old or old[0]==sig,'run scope changed')
 with c:
  c.execute('INSERT OR IGNORE INTO runs(id,host,scope_hash) VALUES(?,?,?)',(run,cfg['host'],sig))
  c.executemany('INSERT OR IGNORE INTO queue(run,url) VALUES(?,?)',[(run,u) for u in urls])
def process(c,run,fetch,parser,limit):
 pending=c.execute("SELECT url FROM queue WHERE run=? AND state!='DONE' ORDER BY url",(run,)).fetchall()
 for (url,) in pending[:limit]:
  try:
   raw=fetch(url);sha=hashlib.sha256(raw).hexdigest();at=utc()
   rows=parser(raw,url);require(rows,'empty or contradictory extraction')
   host=urlsplit(url).hostname;ids=set()
   with c:
    for d in rows:
     require(d['source_product_id'] and d['source_variant_id'] and d['decision']=='HOLD','unsafe detail')
     require(all(f['html_sha256']==sha and f['source_url']==url for f in d['fields'].values()),'provenance mismatch')
     v=lambda k:d['fields'].get(k,{}).get('value')
     money(v('price'));require(re.fullmatch('[A-Z]{3}',v('currency') or ''),'invalid currency')
     pid=digest([host,d['source_product_id']]);vid=digest([pid,d['source_variant_id']])
     require(vid not in ids,'duplicate variant');ids.add(vid)
     r=dict(source_url=url,source_product_id=pid,source_variant_id=vid,merchant_product_id=d['source_product_id'],merchant_variant_id=d['source_variant_id'],legacy_product_id='',legacy_sku='',legacy_size='',brand=v('brand') or '',name=v('name') or '',title=v('name') or '',color=v('color') or v('color_candidate') or '',size=v('size') or '',price=str(v('price')),currency=v('currency'),stock_claim=v('stock_claim') or '',detail=d,canonical_product_id='',decision='HOLD',capture_hash=sha,capture_time=at)
     if not (r['brand'] and r['name']):raise ProductDataError('missing brand/name')
     payload=json.dumps(r,ensure_ascii=False,sort_keys=True)
     stable=dict(r);stable.pop('capture_time')
     c.execute('INSERT OR IGNORE INTO observations VALUES(?,?,?)',(digest(stable),vid,payload))
     c.execute('INSERT INTO latest VALUES(?,?,?,?)',(run,vid,url,payload))
    c.execute('INSERT INTO captures VALUES(?,?,?,?,?)',(run,url,sha,at,raw))
    c.execute("UPDATE queue SET state='DONE',error=NULL WHERE run=? AND url=?",(run,url))
  except Exception as e:
   with c:c.execute("UPDATE queue SET state='ERROR',error=? WHERE run=? AND url=?",(str(e)[:500],run,url))
   if not isinstance(e,ProductDataError):raise
   continue
 with c:
  c.execute("UPDATE runs SET complete=NOT EXISTS(SELECT 1 FROM queue WHERE run=? AND state!='DONE') WHERE id=?",(run,run))
def report(c,run,out):
 counts=dict(c.execute('SELECT state,count(*) FROM queue WHERE run=? GROUP BY state',(run,)))
 rows=[json.loads(x[0]) for x in c.execute('SELECT payload FROM latest WHERE run=? ORDER BY variant',(run,))]
 complete=c.execute('SELECT complete FROM runs WHERE id=?',(run,)).fetchone()[0]
 result=dict(queue=counts,rows=len(rows),complete=bool(complete),published=0,approved_for_import=False)
 (out/'partial-evidence.json').write_text(json.dumps(rows,ensure_ascii=False),encoding='utf-8')
 if complete:
  woo,buyma,profits,mapping=exports(rows)
  for b in buyma:b.setdefault('buyma_sale_price_jpy','');b.setdefault('image_urls','')
  result.update(validate_exports(rows,woo,buyma,mapping))
  verified=evaluate(rows,{},datetime.now(timezone.utc))
  _write(out/'woo.csv',WOO,woo);_write(out/'buyma.csv',BUYMA,buyma);_write(out/'profit.csv',list(profits[0]),profits)
  for name,data in [('evidence',rows),('verification',verified),('mapping',mapping)]:
   (out/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
  previous=c.execute('SELECT id FROM runs WHERE host=(SELECT host FROM runs WHERE id=?) AND complete=1 AND id!=? ORDER BY rowid DESC LIMIT 1',(run,run)).fetchone()
  if previous:
   old={x[0]:json.loads(x[1]) for x in c.execute('SELECT variant,payload FROM latest WHERE run=?',(previous[0],))}
   new={r['source_variant_id']:r for r in rows}
   result['delta']={'new':len(new.keys()-old.keys()),'missing_candidates':len(old.keys()-new.keys()),'price_or_stock_changed':sum((new[k]['price'],new[k]['currency'],new[k]['stock_claim'])!=(old[k]['price'],old[k]['currency'],old[k]['stock_claim']) for k in new.keys()&old.keys())}
 (out/'report.json').write_text(json.dumps(result,indent=2),encoding='utf-8');return result
def main():
 p=argparse.ArgumentParser()
 for k in ('config','db','run','out'):p.add_argument('--'+k,required=True)
 p.add_argument('--limit',type=int,default=5);p.add_argument('--resume',action='store_true');a=p.parse_args()
 cfg=json.loads(Path(a.config).read_text());policy(cfg);require(a.limit>0,'invalid limit')
 out=Path(a.out);out.mkdir()
 with sqlite3.connect(a.db) as c:
  init(c);f=Fetch(cfg);f.init_robots()
  if a.resume:
   require(c.execute('SELECT host FROM runs WHERE id=?',(a.run,)).fetchone()==(cfg['host'],),'unknown run')
   require(not c.execute("SELECT 1 FROM queue WHERE run=? AND state='ERROR'",(a.run,)).fetchone(),'error requires review')
   urls=[x[0] for x in c.execute('SELECT url FROM queue WHERE run=? ORDER BY url',(a.run,))]
   prepare(c,a.run,cfg,urls)
  else:
   require(not c.execute('SELECT 1 FROM runs WHERE id=?',(a.run,)).fetchone(),'run already exists')
   urls,n,excluded=discover(cfg,f);prepare(c,a.run,cfg,urls)
   (out/'discovery.json').write_text(json.dumps(dict(urls=urls,sitemaps=0 if cfg.get('listing_seeds') else n,listing_pages=n if cfg.get('listing_seeds') else 0,excluded=excluded)),encoding='utf-8')
  try:process(c,a.run,f,extract,a.limit)
  finally:print(json.dumps(report(c,a.run,out)))
if __name__=='__main__':main()

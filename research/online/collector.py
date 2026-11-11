"""Offline-first merchant JSON-LD Product parser; no network fetching."""
import argparse,csv,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal,InvalidOperation
from html.parser import HTMLParser
from urllib.parse import urlparse
ALLOWED={'www.bstn.com','bstn.com','www.footlocker.com','www.footlocker.de','www.zalando.de','www.zalando.com'}
class Scripts(HTMLParser):
 def __init__(self):super().__init__();self.active=False;self.parts=[];self.scripts=[]
 def handle_starttag(self,tag,attrs):
  if tag=='script':self.active=dict(attrs).get('type','').lower()=='application/ld+json';self.parts=[]
 def handle_data(self,data):
  if self.active:self.parts.append(data)
 def handle_endtag(self,tag):
  if tag=='script' and self.active:self.scripts.append(''.join(self.parts));self.active=False
def nodes(x):
 if isinstance(x,list):
  for v in x:yield from nodes(v)
 elif isinstance(x,dict):
  if '@graph' in x:yield from nodes(x['@graph'])
  yield x
def scalar(x):
 if isinstance(x,dict):return x.get('name') or x.get('value') or ''
 if isinstance(x,list):return ', '.join(str(scalar(v)) for v in x)
 return x or ''
def parse(html,source_url,observed=None):
 p=urlparse(source_url)
 if p.scheme!='https' or p.hostname not in ALLOWED or p.username or p.password:raise ValueError('approved HTTPS merchant URL required')
 parser=Scripts();parser.feed(html);out=[];seen=set()
 for script in parser.scripts:
  try:objects=json.loads(script)
  except json.JSONDecodeError:continue
  for obj in nodes(objects):
   typ=obj.get('@type',[]);types=typ if isinstance(typ,list) else [typ]
   if 'Product' not in types:continue
   brand=str(scalar(obj.get('brand',''))).strip();sku=str(scalar(obj.get('sku',''))).strip()
   name=str(scalar(obj.get('name',''))).strip();color=str(scalar(obj.get('color',''))).strip()
   offers=obj.get('offers',[]);offers=offers if isinstance(offers,list) else [offers]
   for offer in offers:
    if not isinstance(offer,dict):continue
    spec=offer.get('priceSpecification')
    price=offer.get('price') or (spec.get('price') if isinstance(spec,dict) else None)
    try:money=Decimal(str(price));valid=money.is_finite() and money>0
    except (InvalidOperation,TypeError,ValueError):valid=False
    currency=str(offer.get('priceCurrency') or '').upper()
    availability=str(offer.get('availability','')).rsplit('/',1)[-1]
    size=str(scalar(offer.get('size') or obj.get('size') or '')).strip()
    offer_url=str(offer.get('url') or source_url);op=urlparse(offer_url)
    if op.scheme!='https' or op.hostname not in ALLOWED:offer_url=source_url
    reasons=[]
    if not brand:reasons.append('BRAND_MISSING')
    if not sku:reasons.append('SKU_MISSING')
    if not color:reasons.append('COLOR_MISSING')
    if not size:reasons.append('SIZE_MISSING')
    if not valid:reasons.append('PRICE_MISSING_OR_INVALID')
    if currency not in ('EUR','USD','GBP'):reasons.append('CURRENCY_UNVERIFIED')
    if availability!='InStock':reasons.append('STOCK_UNVERIFIED')
    reasons.append('SIZE_STOCK_REQUIRES_MANUAL_CONFIRMATION')
    key=(brand,sku,color,size,offer_url,str(price))
    if key in seen:continue
    seen.add(key)
    out.append({'product_id':hashlib.sha256('|'.join((brand,sku,color,size)).casefold().encode()).hexdigest()[:18] if brand and sku else '', 'shop':p.hostname,'brand':brand,'sku':sku,'name':name,'color':color,'size':size,'price':str(price) if valid else '', 'currency':currency,'availability_claim':availability,'product_url':offer_url,'source_url':source_url,'observed_utc':observed or datetime.now(timezone.utc).isoformat(),'source_mode':'manual_html_jsonld','gate':'HOLD','hold_reasons':';'.join(reasons),'auto_publish':'disabled'})
 return out
def csvsafe(value):
 s=str(value)
 return "'"+s if s.lstrip().startswith(('=','+','-','@','\t','\r','\n')) else s
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--html',required=True);ap.add_argument('--url',required=True);ap.add_argument('--output',required=True);args=ap.parse_args()
 rows=parse(Path(args.html).read_text(encoding='utf-8'),args.url)
 fields=['product_id','shop','brand','sku','name','color','size','price','currency','availability_claim','product_url','source_url','observed_utc','source_mode','gate','hold_reasons','auto_publish']
 Path(args.output).parent.mkdir(parents=True,exist_ok=True)
 with open(args.output,'w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows([{k:csvsafe(r[k]) for k in fields} for r in rows])
 print(json.dumps({'products':len(rows),'auto_publish':False,'status':'manual_review_only'}))
if __name__=='__main__':main()

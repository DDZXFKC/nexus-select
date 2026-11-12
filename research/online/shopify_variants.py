"""Offline Shopify inline-variant extractor. No fetching, no publishing."""
import json,re,hashlib
from html.parser import HTMLParser
from urllib.parse import urlparse
from datetime import datetime,timezone
HOSTS={'www.notre-shop.com','notre-shop.com','patta.nl','www.patta.nl'}
class ScriptReader(HTMLParser):
 def __init__(self):super().__init__();self.active=False;self.buf=[];self.scripts=[]
 def handle_starttag(self,tag,attrs):
  if tag=='script':self.active=True;self.buf=[]
 def handle_data(self,data):
  if self.active:self.buf.append(data)
 def handle_endtag(self,tag):
  if tag=='script' and self.active:self.scripts.append(''.join(self.buf));self.active=False
def arrays(source):
 decoder=json.JSONDecoder()
 for match in re.finditer(r'(?:["\']variants["\']|\bvariants)\s*:\s*(?=\[)',source):
  try:value,_=decoder.raw_decode(source[match.end():].lstrip())
  except (ValueError,TypeError):continue
  if isinstance(value,list) and value and all(isinstance(x,dict) for x in value):yield value
def ld_products(scripts):
 for script in scripts:
  try:value=json.loads(script)
  except ValueError:continue
  stack=[value]
  while stack:
   item=stack.pop()
   if isinstance(item,list):stack.extend(item)
   elif isinstance(item,dict):
    typ=item.get('@type',[])
    if typ=='Product' or isinstance(typ,list) and 'Product' in typ:yield item
    if '@graph' in item:stack.append(item['@graph'])
def text(value):
 if isinstance(value,dict):return str(value.get('name') or value.get('value') or '')
 return str(value or '')
def vendor_candidates(script):
 """Only accept a single unambiguous vendor string from the script containing variants."""
 matches=re.findall(r'"vendor"\s*:\s*"([^"]+)"',script)
 return {m.strip() for m in matches if m.strip()}
def title_from_variants(scripts):
 """Use only the title of a parent object containing vendor and variants."""
 values=set()
 decoder=json.JSONDecoder()
 for script in scripts:
  for match in re.finditer(r'\{',script):
   try:obj,_=decoder.raw_decode(script[match.start():])
   except (ValueError,TypeError):continue
   if not isinstance(obj,dict):continue
   variants=obj.get('variants')
   if not isinstance(variants,list) or not variants or not obj.get('vendor'):continue
   title=obj.get('title')
   if isinstance(title,str) and title.strip():values.add(title.strip())
 return next(iter(values)) if len(values)==1 else ''
def brand_from_variants(scripts):
 values=set()
 for script in scripts:
  if not any(True for _ in arrays(script)):continue
  values.update(vendor_candidates(script))
 return next(iter(values)) if len(values)==1 else ''
def parse(html,url):
 parsed_url=urlparse(url);host=parsed_url.hostname
 if parsed_url.scheme!='https' or host not in HOSTS or parsed_url.username or parsed_url.password:raise ValueError('unapproved Shopify source')
 parser=ScriptReader();parser.feed(html)
 products=list(ld_products(parser.scripts));product=products[0] if products else {}
 name=text(product.get('name'));brand=text(product.get('brand')) or brand_from_variants(parser.scripts);color=text(product.get('color'))
 if not name:name=title_from_variants(parser.scripts)
 candidates=[]
 for script in parser.scripts:
  candidates.extend(arrays(script))
  try:
   decoded=json.loads(script)
   if isinstance(decoded,str):candidates.extend(arrays(decoded))
  except ValueError:pass
 if not candidates:raise ValueError('No parseable Shopify variants JSON array; inspect saved HTML structure')
 best=max(candidates,key=lambda arr:sum(isinstance(v,dict) and ('sku' in v or 'price' in v) for v in arr))
 out=[];seen=set()
 for v in best:
  if not isinstance(v,dict):continue
  size=text(v.get('public_title') or v.get('title') or v.get('option1'))
  sku=text(v.get('sku'));raw_price=v.get('price')
  offer=product.get('offers')
  currency=text(v.get('currencyCode') or v.get('currency') or (raw_price.get('currencyCode') if isinstance(raw_price,dict) else '') or (offer.get('priceCurrency') if isinstance(offer,dict) else ''))
  price='' if raw_price is None else text(raw_price.get('amount') if isinstance(raw_price,dict) else raw_price)
  key=(sku,size,price)
  if key in seen:continue
  seen.add(key)
  out.append({'product_id':hashlib.sha256(('merchant-page|'+url.split('#')[0]).encode('utf-8')).hexdigest()[:18],'shop':host,'brand':brand,'sku':sku,'name':name,'color':color,'size':size,'price':price,'currency':currency,'availability_claim':'','product_url':url,'source_url':url,'observed_utc':datetime.now(timezone.utc).isoformat(),'source_mode':'shopify_inline_variants_unverified','gate':'HOLD','hold_reasons':'MANUFACTURER_CODE_UNVERIFIED;PRICE_UNIT_UNVERIFIED;SIZE_STOCK_UNVERIFIED;IMAGE_RIGHTS_UNVERIFIED','auto_publish':'disabled'})
 return out

"""Offline detail evidence extraction; review only, no network."""
import re,json,hashlib
from decimal import Decimal, InvalidOperation
from shopify_variants import ScriptReader,ld_products
from urllib.parse import urlparse
def merge_candidates(candidates):
 """Merge only identical parent IDs and compatible projected fields."""
 def present(v):return v not in (None,'',[],{})
 def merge(dst,src,keys):
  for k in keys:
   v=src.get(k)
   if not present(v):continue
   if present(dst.get(k)) and dst[k]!=v:raise ValueError('conflict: '+k)
   dst[k]=v
 if not candidates:return None
 ids={str(x['id']) for x in candidates}
 if len(ids)!=1:return None
 parent={'id':next(iter(ids))};variants={};prices={}
 try:
  for x in candidates:
   merge(parent,x,('vendor','title','type','handle'))
   for v in x['variants']:
    if not isinstance(v,dict) or not v.get('id'):raise ValueError('missing variant id')
    key=str(v['id']);target=variants.setdefault(key,{'id':key})
    merge(target,v,('sku','title'))
    price=v.get('price')
    if price is not None:prices.setdefault(key,[]).append(price)
    for field,keys in (('image',('src',)),):
     obj=v.get(field)
     if obj is None:continue
     if not isinstance(obj,dict):raise ValueError('invalid '+field)
     merge(target.setdefault(field,{}),obj,keys)
  for key,values in prices.items():
   major=[];minor=[];currencies=set()
   for value in values:
    if type(value) is int:
     if value<0:raise ValueError('negative minor price')
     minor.append(Decimal(value))
    elif isinstance(value,dict):
     amount=value.get('amount');currency=value.get('currencyCode')
     if type(amount) not in (int,float,str) or not isinstance(currency,str) or not re.fullmatch('[A-Z]{3}',currency):
      raise ValueError('invalid money')
     n=Decimal(str(amount))
     if not n.is_finite() or n<0:raise ValueError('invalid amount')
     major.append(n);currencies.add(currency)
    else:raise ValueError('invalid price representation')
   if len(currencies)!=1 or not major:raise ValueError('missing or conflicting currency')
   currency=next(iter(currencies))
   if minor and currency not in ('USD','EUR'):raise ValueError('unsupported minor unit')
   if any(n!=major[0] for n in major) or any(n!=major[0]*100 for n in minor):
    raise ValueError('price conflict')
   # Preserve the original major-unit representation; comparison uses Decimal.
   original=next(v for v in values if isinstance(v,dict))
   variants[key]['price']={'amount':original['amount'],'currencyCode':currency}
 except (ValueError,InvalidOperation,TypeError):return None
 parent['variants']=list(variants.values())
 return parent

def extract(html,url):
 # Strings are supported for synthetic fixtures; production CLI passes bytes.
 raw=html if isinstance(html,bytes) else html.encode('utf-8')
 sha=hashlib.sha256(raw).hexdigest()
 p=ScriptReader();p.feed(raw.decode('utf-8-sig')); host=urlparse(url).hostname or ''
 def field(value,path):
  return {'value':value,'path':path,'source_url':url,'html_sha256':sha,'status':'OBSERVED' if value not in (None,'',[],{}) else 'UNKNOWN'}
 def record(obj,variant,fields):
  return {'source_product_id':str(obj or ''),'source_variant_id':str(variant or ''),'fields':{k:field(v,path) for k,(v,path) in fields.items()},'decision':'HOLD','canonical_product_id':'','image_rights':'UNKNOWN'}
 out=[]
 if host in ('bstn.com','www.bstn.com'):
  for x in ld_products(p.scripts):
   offers=x.get('offers',[])
   if isinstance(offers,dict):offers=[offers]
   for o in offers:
    if not isinstance(o,dict):continue
    out.append(record(x.get('sku'),o.get('sku'),{
     'manufacturer_code_candidate':(x.get('mpn'),'Product.mpn'),'category':(x.get('category'),'Product.category'),'image':(x.get('image'),'Product.image'),'description':(x.get('description'),'Product.description'),'size':(o.get('size'),'Offer.size'),'price':(o.get('price'),'Offer.price'),'currency':(o.get('priceCurrency'),'Offer.priceCurrency'),'stock_claim':(o.get('availability'),'Offer.availability'),'gtin':(o.get('gtin13') or o.get('gtin12'),'Offer.gtin13/gtin12'),'color':(x.get('color'),'Product.color')}))
 elif host in ('notre-shop.com','www.notre-shop.com','patta.nl','www.patta.nl'):
  candidates={}
  decoder=json.JSONDecoder()
  for s in p.scripts:
   for m in re.finditer(r'\{',s):
    try:x,_=decoder.raw_decode(s[m.start():])
    except ValueError:continue
    if isinstance(x,dict) and x.get('id') and x.get('vendor') and isinstance(x.get('variants'),list) and x['variants']:
     candidates[json.dumps(x,sort_keys=True)]=x
  x=merge_candidates(list(candidates.values()))
  if x is None:return []
  title=x.get('title','')
  for v in x['variants']:
   if not isinstance(v,dict):continue
   raw=v.get('title','');size=raw;color=''
   if 'notre-shop.com' in host and ' / ' in raw:
    a,b=raw.split(' / ',1)
    if title.endswith(' in '+b):size,color=a,b
   elif 'patta.nl' in host:
    m=re.search(r'\(([^()]+)\)$',title)
    if m:color=m.group(1)
   price=v.get('price');price=price if isinstance(price,dict) else {}
   img=v.get('image');img=img if isinstance(img,dict) else {}
   out.append(record(x['id'],v.get('id'),{'category':(x.get('type'),'parent.type'),'image':(img.get('src'),'variant.image.src'),'size':(size,'variant.title'),'raw_title':(raw,'variant.title'),'color_candidate':(color,'parent.title + variant.title'),'price':(price.get('amount'),'variant.price.amount'),'currency':(price.get('currencyCode'),'variant.price.currencyCode'),'stock_claim':(None,'not present in observed variant object'),'merchant_sku':(v.get('sku'),'variant.sku')}))
 return out
if __name__=='__main__':
 import argparse,csv
 from pathlib import Path
 a=argparse.ArgumentParser();a.add_argument('--manifest',required=True);a.add_argument('--out',required=True);args=a.parse_args()
 m=Path(args.manifest).resolve();out=Path(args.out)
 result=[]
 with m.open(encoding='utf-8-sig',newline='') as f:
  for r in csv.DictReader(f):
   p=(m.parent/r['html_file']).resolve()
   if m.parent not in p.parents:raise ValueError('path outside manifest')
   rows=extract(p.read_bytes(),r['product_url'])
   result.append({'url':r['product_url'],'rows':rows,'count':len(rows)})
 with out.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
 print(json.dumps({'counts':[x['count'] for x in result],'total':sum(x['count'] for x in result),'published':0}))

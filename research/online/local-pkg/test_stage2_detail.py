import unittest,json
from stage2_detail import extract
def html(x):return '<script type="application/json">'+json.dumps(x)+'</script>'
def parent(title='Sneaker in Black/White',variant='8 M / Black/White'):
 return {'id':'p1','vendor':'Brand','title':title,'type':'Sneakers','variants':[{'id':'v1','sku':'s1','title':variant,'price':{'amount':180,'currencyCode':'USD'},'image':{'src':'https://example.com/i.jpg'}}]}
class DetailTests(unittest.TestCase):
 def test_bstn(self):
  x={'@type':'Product','sku':'p','mpn':'candidate','category':{'name':'Shoes'},'image':'https://example.com/i.jpg','description':'Synthetic','offers':[{'sku':'v','size':'8','price':27.99,'priceCurrency':'EUR','availability':'OutOfStock','gtin13':'123'}]}
  r=extract(html(x),'https://www.bstn.com/p')[0]
  self.assertEqual(r['source_variant_id'],'v')
  self.assertEqual(r['fields']['manufacturer_code_candidate']['value'],'candidate')
  self.assertEqual(r['canonical_product_id'],'')
  self.assertEqual(r['decision'],'HOLD')
  self.assertEqual(r['image_rights'],'UNKNOWN')
 def test_notre(self):
  r=extract(html(parent()),'https://notre-shop.com/p')[0]
  self.assertEqual(r['fields']['size']['value'],'8 M')
  self.assertEqual(r['fields']['color_candidate']['value'],'Black/White')
  self.assertEqual(r['fields']['stock_claim']['status'],'UNKNOWN')
  self.assertEqual(r['fields']['price']['value'],180)
 def test_patta(self):
  r=extract(html(parent('Jacket (Black)','XS')),'https://patta.nl/p')[0]
  self.assertEqual(r['fields']['color_candidate']['value'],'Black')
  self.assertEqual(r['fields']['size']['value'],'XS')
 def test_mismatch(self):
  r=extract(html(parent('Sneaker in Red')),'https://notre-shop.com/p')[0]
  self.assertEqual(r['fields']['color_candidate']['status'],'UNKNOWN')
 def test_ambiguous(self):
  x=parent();y=dict(x,id='p2')
  self.assertEqual(extract(html(x)+html(y),'https://notre-shop.com/p'),[])
 def test_provenance(self):
  r=extract(html(parent()),'https://notre-shop.com/p')[0]
  for f in r['fields'].values():
   self.assertEqual(f['source_url'],'https://notre-shop.com/p')
   self.assertEqual(len(f['html_sha256']),64)
 def test_same_parent(self):
  x=parent();y=dict(x,extra='different')
  self.assertEqual(len(extract(html(x)+html(y),'https://notre-shop.com/p')),1)
 def test_missing_title(self):
  x=parent();y=dict(x);del y['title']
  r=extract(html(y)+html(x),'https://notre-shop.com/p')[0]
  self.assertEqual(r['fields']['color_candidate']['value'],'Black/White')
 def test_parent_conflict(self):
  x=parent();y=dict(x,vendor='Other')
  self.assertEqual(extract(html(x)+html(y),'https://notre-shop.com/p'),[])
 def test_variant_conflict(self):
  x=parent();y=parent();y['variants'][0]['price']['amount']=181
  self.assertEqual(extract(html(x)+html(y),'https://notre-shop.com/p'),[])
 def test_raw_hash(self):
  import hashlib
  raw=(html(parent())+'\r\n').encode('utf-8')
  r=extract(raw,'https://notre-shop.com/p')[0]
  self.assertEqual(r['fields']['size']['html_sha256'],hashlib.sha256(raw).hexdigest())
 def test_duplicate_variant(self):
  x=parent();x['variants'].append(dict(x['variants'][0]))
  self.assertEqual(len(extract(html(x),'https://notre-shop.com/p')),1)
 def test_distinct_parent_same_variant(self):
  x=parent();y=dict(x,id='p2',title='')
  self.assertEqual(extract(html(x)+html(y),'https://notre-shop.com/p'),[])
if __name__=='__main__':unittest.main()


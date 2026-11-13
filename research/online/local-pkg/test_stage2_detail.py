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
if __name__=='__main__':unittest.main()

import unittest
from collector import parse,csvsafe
class Tests(unittest.TestCase):
 def setUp(self):
  self.html='''<script type="application/ld+json">{"@context":"https://schema.org","@type":"Product","name":"Test Shoe","brand":{"name":"Demo"},"sku":"AB-123","color":"Black","offers":{"@type":"Offer","price":"120.00","priceCurrency":"EUR","availability":"https://schema.org/InStock","url":"https://www.bstn.com/test","size":"US 9"}}</script>'''
  self.url='https://www.bstn.com/test'
 def test_parse(self):
  r=parse(self.html,self.url);self.assertEqual(len(r),1);self.assertEqual(r[0]['sku'],'AB-123');self.assertEqual(r[0]['gate'],'HOLD')
 def test_no_sku(self):
  r=parse(self.html.replace('"sku":"AB-123",',''),self.url)[0];self.assertEqual(r['product_id'],'');self.assertIn('SKU_MISSING',r['hold_reasons'])
 def test_no_size(self):
  r=parse(self.html.replace(',"size":"US 9"',''),self.url)[0];self.assertIn('SIZE_MISSING',r['hold_reasons'])
 def test_invalid_price(self):
  r=parse(self.html.replace('120.00','-10'),self.url)[0];self.assertIn('PRICE_MISSING_OR_INVALID',r['hold_reasons'])
 def test_out_of_stock(self):
  r=parse(self.html.replace('InStock','OutOfStock'),self.url)[0];self.assertIn('STOCK_UNVERIFIED',r['hold_reasons'])
 def test_unapproved_url(self):
  with self.assertRaises(ValueError):parse(self.html,'https://example.com/test')
 def test_no_scripts(self):self.assertEqual(parse('<h1>none</h1>',self.url),[])
 def test_csv(self):self.assertEqual(csvsafe('=1+1'),"'=1+1")
 def test_no_auto_publish(self):self.assertEqual(parse(self.html,self.url)[0]['auto_publish'],'disabled')
 def test_bad_json(self):self.assertEqual(parse('<script type="application/ld+json">{broken</script>',self.url),[])
if __name__=='__main__':unittest.main()

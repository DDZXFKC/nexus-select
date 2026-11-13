import unittest,sqlite3
from stage2_review import normalize,store,cost,COST_FIELDS
class Review(unittest.TestCase):
 def setUp(self):
  self.r=dict(product_url='https://example.com/p',sku='A',size='8',color='Black',brand='Patta',name='Patta Jacket',price='100',observed_utc='parse1')
 def test_identity(self):
  a=normalize(self.r)
  self.assertNotEqual(a['source_variant_id'],normalize(dict(self.r,color='White'))['source_variant_id'])
  self.assertNotEqual(a['source_variant_id'],normalize(dict(self.r,product_url='https://other.example/p'))['source_variant_id'])
  self.assertEqual(a['canonical_product_id'],'')
  self.assertEqual(a['display_name'],'Patta Jacket')
 def test_history(self):
  with sqlite3.connect(':memory:') as c:
   store(c,self.r,'hash1')
   store(c,dict(self.r,observed_utc='parse2'),'hash1')
   self.assertEqual(c.execute('select count(*) from observations').fetchone()[0],1)
   store(c,dict(self.r,price='120'),'hash2')
   self.assertEqual(c.execute('select count(*) from observations').fetchone()[0],2)
 def test_cost(self):
  r=dict.fromkeys(COST_FIELDS,'0')
  r.update(price='100',local_tax='10',domestic_shipping='5',fx_jpy='150',fx_fee_jpy='100',international_shipping_jpy='2000',duty_jpy='500',import_consumption_tax_jpy='1000',partner_fee_jpy='1000',channel_rate='.1',channel_fixed_jpy='40',selling_price_jpy='30000')
  self.assertEqual(cost(r),{'cost_jpy':'21850.00','profit_jpy':'5110.00'})
  self.assertEqual(cost(dict(r,duty_jpy=''))['cost_jpy'],'')
  self.assertEqual(cost(dict(r,fx_jpy='0'))['cost_jpy'],'')
if __name__=='__main__':unittest.main()

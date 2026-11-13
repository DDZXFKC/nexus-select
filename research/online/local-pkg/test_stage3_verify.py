import unittest,copy
from datetime import datetime,timezone
from stage3_verify import evaluate,validate_exports
from stage2_integrate import join,exports
from test_stage2_integrate import fixture
NOW=datetime(2026,11,13,tzinfo=timezone.utc)
class Stage3(unittest.TestCase):
 def setUp(self):
  self.rows=join(*fixture());self.r=self.rows[0];self.id=self.r['source_variant_id']
 def proof(self,**kw):
  return dict(source='synthetic fixture',reviewer='test',checked_at=NOW.isoformat(),reference='fixture',source_variant_id=self.id,**kw)
 def test_empty(self):
  r=evaluate(self.rows,{},NOW)[0]
  self.assertEqual(r['decision'],'HOLD');self.assertFalse(r['review_complete']);self.assertEqual(r['cost_jpy'],'')
 def test_identity(self):
  i=self.proof(authority='MANUFACTURER',brand='Brand',style_code='STYLE',colorway_code='BLACK',size_system='US',size='8',observed_size=self.r['size'],observed_color=self.r['color'])
  a=evaluate(self.rows,{self.id:{'identity':i}},NOW)[0]
  self.assertTrue(a['canonical_product_id'])
  i['colorway_code']='RED'
  self.assertNotEqual(a['canonical_product_id'],evaluate(self.rows,{self.id:{'identity':i}},NOW)[0]['canonical_product_id'])
  i['brand']='Other'
  with self.assertRaises(ValueError):evaluate(self.rows,{self.id:{'identity':i}},NOW)
 def test_stock(self):
  s=self.proof(method='PURCHASABILITY_CHECK',state='IN_STOCK')
  self.assertEqual(evaluate(self.rows,{self.id:{'stock':s}},NOW)[0]['stock'],'IN_STOCK')
  self.r['stock_claim']='https://schema.org/OutOfStock'
  with self.assertRaises(ValueError):evaluate(self.rows,{self.id:{'stock':s}},NOW)
 def test_stale(self):
  s=self.proof(method='PURCHASABILITY_CHECK',state='IN_STOCK');s['checked_at']='2020-01-01T00:00:00Z'
  self.assertEqual(evaluate(self.rows,{self.id:{'stock':s}},NOW)[0]['stock'],'UNKNOWN')
 def test_cost(self):
  from stage2_review import COST_FIELDS
  v={k:0 for k in COST_FIELDS};v.update(price=180,fx_jpy=150,selling_price_jpy=35000,channel_rate='0.1')
  c=self.proof(currency='USD',inputs=v)
  r=evaluate(self.rows,{self.id:{'cost':c}},NOW)[0]
  self.assertEqual(r['cost_jpy'],'27000.00');self.assertEqual(r['profit_jpy'],'4500.00')
  v['price']=181
  with self.assertRaises(ValueError):evaluate(self.rows,{self.id:{'cost':c}},NOW)
 def test_rights(self):
  p=self.proof(status='LICENSED',image='https://example.com/i.jpg',channels=['WooCommerce','BUYMA'])
  self.assertEqual(evaluate(self.rows,{self.id:{'image_rights':p}},NOW)[0]['image_rights'],'EVIDENCE_RECORDED')
  p['channels']=['WooCommerce']
  self.assertEqual(evaluate(self.rows,{self.id:{'image_rights':p}},NOW)[0]['image_rights'],'UNKNOWN')
 def test_exports(self):
  w,b,p,m=exports(self.rows)
  # CSV reader supplies empty optional columns.
  for x in b:x.setdefault('buyma_sale_price_jpy','');x.setdefault('image_urls','')
  self.assertEqual(validate_exports(self.rows,w,b,m)['actual_import'],'NOT_RUN')
  w[1]['Parent']='bad'
  with self.assertRaises(ValueError):validate_exports(self.rows,w,b,m)
 def test_unknown(self):
  with self.assertRaises(ValueError):evaluate(self.rows,{'unknown':{}},NOW)
if __name__=='__main__':unittest.main()

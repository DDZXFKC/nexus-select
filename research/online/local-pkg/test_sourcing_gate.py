import unittest
from datetime import datetime, timezone, timedelta
from sourcing_gate import evaluate, run
NOW=datetime(2026,11,14,8,tzinfo=timezone.utc)
TARGET=dict(candidate_id='fixture',brand='ASICS',style_code='TEST-001',color_code='CREAM',size_system='US',size='9',condition='NEW')
BASE=dict(TARGET,checked_at=NOW.isoformat(),source_url='https://example.test/product',price_status='OBSERVED')
OFFER=dict(BASE,role='PURCHASE_OFFER',offer_id='o1',seller_verified=True,stock='IN_STOCK',stock_verified=True,currency='JPY',price='10000')
SALE=dict(BASE,role='COMPLETED_SALE',reference_id='s1',currency='JPY',price='20000')
COST=dict(offer_id='o1',currency='JPY',price='10000',cost_status='VERIFIED',cost_reference='fixture',local_tax='0',domestic_shipping='0',fx_jpy='1',fx_fee_jpy='0',international_shipping_jpy='2000',duty_jpy='500',import_consumption_tax_jpy='500',partner_fee_jpy='1000',channel_rate='0.1',channel_fixed_jpy='0',selling_price_jpy='20000',japan_shipping_jpy='1000')
class GateTest(unittest.TestCase):
 def e(self, offers=None, refs=None, costs=None, target=None):
  return evaluate(TARGET if target is None else target,[OFFER] if offers is None else offers,[SALE] if refs is None else refs,COST if costs is None else costs,NOW)
 def test_positive(self):
  r=self.e();self.assertEqual(r['profit_jpy'],'3000.00');self.assertTrue(r['review_ready']);self.assertFalse(r['approved_for_import'])
 def test_identity(self):
  for key in ('brand','style_code','color_code','size_system','size','condition'):
   with self.subTest(key=key):
    r=self.e(refs=[dict(SALE,**{key:'different'})]);self.assertEqual(r['matched_sales'],0);self.assertIsNone(r['profit_jpy'])
 def test_buyma_fallback(self):
  r=self.e(offers=[dict(OFFER,role='ASK',price='7360')]);self.assertIsNone(r['buy_price']);self.assertIsNone(r['profit_jpy'])
 def test_expected(self): self.assertIsNone(self.e(offers=[dict(OFFER,price_status='EXPECTED')])['buy_price'])
 def test_no_stock(self): self.assertIsNone(self.e(offers=[dict(OFFER,stock='UNKNOWN')])['buy_price'])
 def test_ask_separate(self):
  r=self.e(refs=[dict(SALE,role='ASK')]);self.assertEqual(r['matched_asks'],1);self.assertIsNone(r['profit_jpy'])
 def test_median(self):
  r=self.e(refs=[SALE,dict(SALE,reference_id='s2',price='22000'),dict(SALE,reference_id='s3',price='63000')]);self.assertEqual(r['market_median_jpy'],'22000')
 def test_duplicate(self): self.assertEqual(self.e(refs=[SALE,SALE])['matched_sales'],1)
 def test_missing_cost(self):
  c=dict(COST);c.pop('duty_jpy');self.assertIsNone(self.e(costs=c)['profit_jpy'])
 def test_mismatch_cost(self): self.assertIsNone(self.e(costs=dict(COST,price='1'))['profit_jpy'])
 def test_negative(self):
  r=self.e(costs=dict(COST,international_shipping_jpy='10000'));self.assertEqual(r['profit_jpy'],'-5000.00');self.assertFalse(r['review_ready'])
 def test_stale(self): self.assertIsNone(self.e(offers=[dict(OFFER,checked_at=(NOW-timedelta(days=2)).isoformat())])['buy_price'])
 def test_missing_identity(self): self.assertFalse(self.e(target=dict(TARGET,style_code=''))['review_ready'])
 def test_batch_continues(self):
  r=run([{'candidate':None},{'candidate':TARGET,'offers':[OFFER],'references':[SALE],'cost_inputs':COST}],NOW);self.assertEqual(len(r),2);self.assertEqual(r[1]['profit_jpy'],'3000.00')
if __name__=='__main__': unittest.main()

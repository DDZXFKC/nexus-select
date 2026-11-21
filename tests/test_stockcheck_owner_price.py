import unittest
from decimal import Decimal, ROUND_CEILING
from tools.stockcheck_owner_price import owner_price_from_usd

class TestOwnerPrice(unittest.TestCase):
 def test_100_usd(self):
  p=owner_price_from_usd("100")
  self.assertEqual(p.total_cost_unrounded_jpy,Decimal("19876.00"))
  self.assertEqual(p.total_cost_rounded_jpy,19876)
  self.assertEqual(p.sale_price_jpy,25400)
 def test_float_rejected(self):
  with self.assertRaises(ValueError): owner_price_from_usd(99.99)
 def test_unknown_fee_gates(self):
  for x in ({"confirmed_inputs":False},{"complete_cost":False}):
   with self.assertRaises(ValueError): owner_price_from_usd("130",**x)
 def test_coupons_only_confirmed_in_caller(self):
  p=owner_price_from_usd("100",coupon_applied_usd="90")
  self.assertEqual(p.sale_price_jpy,23300)
 def test_exact_boundary(self):
  p=owner_price_from_usd("0.01")
  self.assertEqual(p.sale_price_jpy,4800)
 def test_rounding_uses_raw_cost(self):
  for src in ("10.01","47.005","126.99","165","1234.567"):
   p=owner_price_from_usd(src)
   expected=int((p.total_cost_unrounded_jpy/Decimal("0.785")/Decimal("100")).to_integral_value(rounding=ROUND_CEILING)*100)
   self.assertEqual(p.sale_price_jpy,expected)
 def test_invalid(self):
  for v in ("0","-1","NaN","Infinity",None):
   with self.assertRaises(ValueError): owner_price_from_usd(v)
if __name__=="__main__":unittest.main()

import importlib.util
import sys
import unittest
from pathlib import Path

path=Path(__file__).resolve().parents[1]/"tools/stockcheck_inline_price_policy.py"
spec=importlib.util.spec_from_file_location("stockcheck_inline_price_policy",path)
policy=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=policy
spec.loader.exec_module(policy)

class InlineCartPricePolicyTests(unittest.TestCase):
    def test_cheaper_price_keeps_listing(self):
        r=policy.resolve_price_case(30000,28000)
        self.assertEqual((r.status,r.checkout_jpy,r.requires_customer_confirmation),
                         ("LISTED",30000,False))
    def test_equal_price_keeps_listing(self):
        self.assertEqual(policy.resolve_price_case(30000,30000).checkout_jpy,30000)
    def test_plus_399_absorb(self):
        r=policy.resolve_price_case(30000,30399)
        self.assertEqual((r.status,r.checkout_jpy),("LISTED",30000))
    def test_plus_400_requires_explicit_acceptance(self):
        r=policy.resolve_price_case(30000,30400)
        self.assertEqual((r.status,r.checkout_jpy,r.requires_customer_confirmation),
                         ("QUOTE_CONFIRM_REQUIRED",30400,True))
    def test_plus_900_checkout_quote(self):
        r=policy.resolve_price_case(30000,30900)
        self.assertEqual(r.checkout_jpy,30900)
    def test_unknown_cost_cannot_unlock_cart(self):
        r=policy.resolve_price_case(30000,None)
        self.assertEqual((r.status,r.checkout_jpy),("PRICE_UNKNOWN",None))
    def test_bad_or_float_prices_rejected(self):
        for x in [0,-1,1.2,"30000",True]:
            with self.assertRaises(ValueError):
                policy.resolve_price_case(30000,x)
        with self.assertRaises(ValueError):
            policy.resolve_price_case(0,31000)

if __name__ == "__main__":
    unittest.main()

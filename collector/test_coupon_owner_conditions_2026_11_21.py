"""Owner 2026-11-21 coupon conditions -> indicative price; old select unchanged."""
import tempfile
import unittest
from pathlib import Path
from coupon_bridge import CouponBridge, indicative_discount, context

NOW = "2026-11-21T09:00:00+09:00"
LATER = "2026-11-21T09:05:00+09:00"
URL = "https://example.org/coupon"
FACTS = dict(brand="Nike", category="Shoes", on_sale=False, is_first_order=True)
RULES = dict(eligible_brands=["Nike"], eligible_categories=["Shoes"],
             sale_exclusion=False, first_order_only=False,
             ship_region="US-OR", min_spend_minor=0, min_spend_currency="USD")
SCOPE = context(shop_code="fl", variant_id="nike-001", currency="USD",
                destination="US-OR", account_scope="account-1",
                quantity=1, base_minor=10000, basket_key="basket1")

class OwnerConditionPricingTests(unittest.TestCase):
    def test_matching_percentage_estimate(self):
        result = indicative_discount(SCOPE, "TAKE20", FACTS,
                     dict(RULES, discount_type="percent", discount_value="20"), now=NOW)
        self.assertEqual((result["status"], result["effective_minor"],
                          result["discount_minor"],result["verification"],
                          result["sale_approved"]),
                         ("CONDITION_MATCH_ESTIMATE", 8000, 2000, "NOT_CHECKED", False))

    def test_exclusion_unknown_and_unsupported_fail_closed(self):
        self.assertEqual(indicative_discount(SCOPE, "A", dict(FACTS, brand="Vans"),
                            dict(RULES, discount_type="percent", discount_value=20),
                            now=NOW)["status"], "EXCLUDED")
        self.assertIsNone(indicative_discount(SCOPE, "A", FACTS,
                            dict(RULES, eligible_brands=None, discount_type="percent",
                                 discount_value=20),now=NOW)["effective_minor"])
        self.assertIsNone(indicative_discount(SCOPE, "A", FACTS,
                            dict(RULES, discount_type="percent", discount_value=20,
                                 undocumented_condition=True),now=NOW)["effective_minor"])

    def test_fixed_currency_cap_and_no_invented_discount(self):
        fixed = indicative_discount(SCOPE,"B",FACTS,dict(RULES,discount_type="fixed",
                        discount_value="2500",discount_currency="USD",
                        max_discount_minor=1000),now=NOW)
        self.assertEqual((fixed["discount_minor"],fixed["effective_minor"]),(1000,9000))
        wrong = indicative_discount(SCOPE,"B",FACTS,dict(RULES,discount_type="fixed",
                        discount_value="2500",discount_currency="EUR"),now=NOW)
        self.assertEqual(wrong["status"],"UNKNOWN")
        self.assertIsNone(wrong["effective_minor"])
        self.assertIsNone(indicative_discount(SCOPE,"B",FACTS,RULES,now=NOW)["effective_minor"])

    def test_saved_discovery_estimates_and_preserves_verified_path(self):
        with tempfile.TemporaryDirectory() as d:
            bridge = CouponBridge(Path(d)/"coupons.db", allowed_shops={"fl"})
            bridge.initialize()
            bridge.record_discovery(shop_code="fl",campaign="TAKE20",
                source_url=URL,observed_at=NOW,
                conditions=dict(RULES,discount_type="percent",discount_value=20),
                evidence_type="OFFICIAL",official_status="ACTIVE")
            estimate=bridge.estimate_from_conditions(SCOPE,now=LATER,product_facts=FACTS)
            self.assertEqual(len(estimate),1)
            self.assertEqual(estimate[0]["effective_minor"],8000)
            self.assertEqual(bridge.select(SCOPE,now=LATER,max_age_seconds=600,
                                           product_facts=FACTS)["status"],
                             "NO_VERIFIED_DISCOUNT")
            bridge.record_check(scope=SCOPE,campaign="TAKE20",source_url=URL,
                                checked_at=LATER,expires_at="2026-11-21T10:00:00+09:00",
                                status="NOT_APPLICABLE",post_minor=None,
                                evidence_ref="cart-negative")
            self.assertIsNone(bridge.estimate_from_conditions(
                SCOPE,now=LATER,product_facts=FACTS)[0]["effective_minor"])

    def test_shop_gate_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            bridge=CouponBridge(Path(d)/"coupons.db",allowed_shops=[])
            bridge.initialize()
            self.assertEqual(bridge.estimate_from_conditions(
                SCOPE,now=LATER,product_facts=FACTS),[])

if __name__ == "__main__":
    unittest.main()

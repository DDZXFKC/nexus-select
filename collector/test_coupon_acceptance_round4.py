"""Offline regression tests for round 4 blockers. No external I/O."""
import tempfile
import unittest
from pathlib import Path
from coupon_bridge import CouponBridge, context, assess_campaigns, evaluate_eligibility, rank_candidates

NOW = "2026-11-18T06:00:00+00:00"
BEFORE = "2026-11-18T05:55:00+00:00"
EXP = "2026-11-18T07:00:00+00:00"
URL = "https://example.com/promo"
SCOPE = context(shop_code="sp", variant_id="v1", currency="USD", destination="US-OR",
                account_scope="fixture", quantity=1, base_minor=10000, basket_key="fixture")
FACTS = dict(brand="Nike", category="Shoes", on_sale=False, is_first_order=True)
RULES = dict(eligible_brands=["Nike"], eligible_categories=["Shoes"], sale_exclusion=False,
             first_order_only=False, ship_region="US-OR", min_spend_minor=0, min_spend_currency="USD")

class Round4(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "test.db"
        self.book = CouponBridge(self.path, allowed_shops={"sp"})
        self.book.initialize()

    def check(self, book=None, **kw):
        args = dict(scope=SCOPE, campaign="X", source_url=URL, checked_at=BEFORE,
                    expires_at=EXP, status="APPLICABLE", post_minor=7000,
                    conditions_confirmed=True, usage_available=True, evidence_ref="fixture")
        args.update(kw)
        return (book or self.book).record_check(**args)

    def assert_blocked_select(self, book):
        try:
            result = book.select(SCOPE, now=NOW, max_age_seconds=600)
        except ValueError:
            return
        self.assertEqual(result["effective_minor"], SCOPE["base_minor"])
        self.assertNotEqual(result["status"], "APPLICABLE")

    def test_denied_check(self):
        with self.assertRaises(ValueError):
            self.check(CouponBridge(self.path, allowed_shops=set()))

    def test_removed_shop_select(self):
        self.check()
        self.assert_blocked_select(CouponBridge(self.path, allowed_shops={"bstn"}))

    def test_removed_shop_candidates(self):
        self.book.record_discovery(shop_code="sp", campaign="X", source_url=URL,
                                   observed_at=BEFORE, conditions=RULES)
        book = CouponBridge(self.path, allowed_shops=set())
        try:
            rows = book.list_candidates(SCOPE, now=NOW, max_age_seconds=600, product_facts=FACTS)
        except ValueError:
            return
        self.assertEqual(rows, [])

    def test_registry_string_is_not_collection(self):
        with self.assertRaises((ValueError, TypeError)):
            CouponBridge(self.path, allowed_shops="sp")

    def test_official_expired_blocks_price(self):
        self.book.record_discovery(shop_code="sp", campaign="X", source_url=URL,
                                   observed_at=BEFORE, conditions=RULES,
                                   evidence_type="OFFICIAL", official_status="EXPIRED")
        self.check()
        self.assert_blocked_select(self.book)

    def test_expired_terms_not_match(self):
        out = evaluate_eligibility("X", SCOPE, FACTS, dict(RULES, valid_until=BEFORE))
        self.assertNotEqual(out["eligibility"], "MATCH")

    def test_future_terms_not_match(self):
        out = evaluate_eligibility("X", SCOPE, FACTS, dict(RULES, valid_from=EXP))
        self.assertNotEqual(out["eligibility"], "MATCH")

    def test_official_status_order_independent(self):
        old = dict(campaign="X", observed_at=BEFORE, evidence_type="OFFICIAL", official_status="ACTIVE", conditions=RULES)
        new = dict(old, observed_at=NOW, official_status="EXPIRED")
        for rows in ([old,new], [new,old]):
            self.assertEqual(assess_campaigns(rows, now=NOW)[0]["campaign_confidence"], "EXPIRED")

    def test_rank_missing_price_and_evidence_not_applicable(self):
        rows = [dict(campaign="X", scope=SCOPE, checked_at=BEFORE, expires_at=EXP,
                     status="APPLICABLE", conditions_confirmed=True, usage_available=True)]
        self.assertNotEqual(rank_candidates([],[],rows,[],scope=SCOPE,now=NOW,max_age_seconds=600)[0]["check_status"], "APPLICABLE")

if __name__ == "__main__":
    unittest.main()

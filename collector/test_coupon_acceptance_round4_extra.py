"""Additional round-4 regression tests requested by GPT audit c74fb500.

Offline only. These cover the cases the round-4 instruction listed beyond
the original 9: same-time official contradictions, RETIRED blocking,
registry type validation on all entry points, explicit-now period
evaluation, and preservation (quarantine, not deletion) of past rows
after a shop leaves the registry.
"""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from coupon_bridge import CouponBridge, context, assess_campaigns, evaluate_eligibility

NOW = "2026-11-18T06:00:00+00:00"
BEFORE = "2026-11-18T05:55:00+00:00"
EXP = "2026-11-18T07:00:00+00:00"
URL = "https://example.com/promo"
SCOPE = context(shop_code="sp", variant_id="v1", currency="USD", destination="US-OR",
                account_scope="fixture", quantity=1, base_minor=10000, basket_key="fixture")
FACTS = dict(brand="Nike", category="Shoes", on_sale=False, is_first_order=True)
RULES = dict(eligible_brands=["Nike"], eligible_categories=["Shoes"], sale_exclusion=False,
             first_order_only=False, ship_region="US-OR", min_spend_minor=0, min_spend_currency="USD")


class Round4Extra(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "test.db"
        self.book = CouponBridge(self.path, allowed_shops={"sp"})
        self.book.initialize()

    def test_official_same_time_contradiction_fails_closed(self):
        active = dict(campaign="X", observed_at=BEFORE, evidence_type="OFFICIAL",
                      official_status="ACTIVE", conditions=RULES)
        expired = dict(active, official_status="EXPIRED")
        for rows in ([active, expired], [expired, active]):
            self.assertEqual(assess_campaigns(rows, now=NOW)[0]["campaign_confidence"], "EXPIRED")

    def test_official_retired_blocks_price(self):
        self.book.record_discovery(shop_code="sp", campaign="X", source_url=URL,
                                   observed_at=BEFORE, conditions=RULES,
                                   evidence_type="OFFICIAL", official_status="RETIRED")
        self.book.record_check(scope=SCOPE, campaign="X", source_url=URL, checked_at=BEFORE,
                               expires_at=EXP, status="APPLICABLE", post_minor=7000,
                               conditions_confirmed=True, usage_available=True,
                               evidence_ref="fixture")
        result = self.book.select(SCOPE, now=NOW, max_age_seconds=600)
        self.assertEqual(result["effective_minor"], SCOPE["base_minor"])
        self.assertNotEqual(result["status"], "APPLICABLE")

    def test_record_check_rejected_with_empty_registry(self):
        book = CouponBridge(self.path, allowed_shops=None)
        with self.assertRaises(ValueError):
            book.record_check(scope=SCOPE, campaign="X", source_url=URL, checked_at=BEFORE,
                              expires_at=EXP, status="APPLICABLE", post_minor=7000,
                              conditions_confirmed=True, usage_available=True,
                              evidence_ref="fixture")

    def test_numeric_registry_entry_rejected(self):
        with self.assertRaises(ValueError):
            CouponBridge(self.path, allowed_shops={123})

    def test_period_evaluated_with_explicit_now(self):
        expired = evaluate_eligibility("X", SCOPE, FACTS, dict(RULES, valid_until=BEFORE), now=NOW)
        self.assertEqual(expired["eligibility"], "EXCLUDED")
        future = evaluate_eligibility("X", SCOPE, FACTS, dict(RULES, valid_from=EXP), now=NOW)
        self.assertEqual(future["eligibility"], "EXCLUDED")
        in_window = evaluate_eligibility("X", SCOPE, FACTS,
                                         dict(RULES, valid_from=BEFORE, valid_until=EXP), now=NOW)
        self.assertEqual(in_window["eligibility"], "MATCH")
        invalid = evaluate_eligibility("X", SCOPE, FACTS, dict(RULES, valid_until="not-a-date"), now=NOW)
        self.assertNotEqual(invalid["eligibility"], "MATCH")

    def test_past_rows_preserved_after_shop_removal(self):
        self.book.record_discovery(shop_code="sp", campaign="X", source_url=URL,
                                   observed_at=BEFORE, conditions=RULES)
        self.book.record_check(scope=SCOPE, campaign="X", source_url=URL, checked_at=BEFORE,
                               expires_at=EXP, status="APPLICABLE", post_minor=7000,
                               conditions_confirmed=True, usage_available=True,
                               evidence_ref="fixture")
        removed = CouponBridge(self.path, allowed_shops=set())
        result = removed.select(SCOPE, now=NOW, max_age_seconds=600)
        self.assertEqual(result["effective_minor"], SCOPE["base_minor"])
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM ahc_coupon_observations_v1").fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM ahc_coupon_checks_v1").fetchone()[0], 1)

    def test_bool_min_spend_is_invalid(self):
        out = evaluate_eligibility("X", SCOPE, FACTS, dict(RULES, min_spend_minor=True), now=NOW)
        self.assertNotEqual(out["eligibility"], "MATCH")
        self.assertIn("MIN_SPEND_INVALID", out["reasons"])

    def test_string_brand_rules_are_not_substring_matched(self):
        out = evaluate_eligibility("X", SCOPE, FACTS, dict(RULES, eligible_brands="Nike"), now=NOW)
        self.assertNotEqual(out["eligibility"], "MATCH")
        self.assertIn("INVALID_TYPE:eligible_brands", out["reasons"])

    def test_list_candidates_applies_terms_period(self):
        self.book.record_discovery(shop_code="sp", campaign="OLD", source_url=URL,
                                   observed_at=BEFORE,
                                   conditions=dict(RULES, valid_from=BEFORE, valid_until=BEFORE))
        self.book.record_discovery(shop_code="sp", campaign="NEW", source_url=URL,
                                   observed_at=BEFORE,
                                   conditions=dict(RULES, valid_from=BEFORE, valid_until=EXP))
        rows = {r["campaign"]: r for r in self.book.list_candidates(
            SCOPE, now=NOW, max_age_seconds=600, product_facts=FACTS)}
        self.assertEqual(rows["OLD"]["eligibility"], "EXCLUDED")
        self.assertEqual(rows["NEW"]["eligibility"], "MATCH")


if __name__ == "__main__":
    unittest.main()

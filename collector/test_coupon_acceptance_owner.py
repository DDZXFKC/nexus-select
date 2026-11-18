"""Independent acceptance tests, synthetic only. Red tests identify blockers.
Run: cd collector && python3 -m unittest test_coupon_acceptance_owner -v
Do not weaken expected results to make an incomplete implementation pass.
"""
import unittest
from coupon_bridge import context, assess_campaigns, evaluate_eligibility, rank_candidates

NOW = "2026-11-18T06:00:00+00:00"
SCOPE = context(shop_code="bstn", variant_id="fixture", currency="USD",
                destination="US-OR", account_scope="fixture", quantity=1,
                base_minor=5000, basket_key="fixture")

class OwnerAcceptance(unittest.TestCase):
    def test_minimum_major_boundaries(self):
        for amount, expected in [(50, None), (99, "EXCLUDED"), (100, "EXCLUDED"), (200, "EXCLUDED")]:
            with self.subTest(amount=amount):
                result = evaluate_eligibility("X", SCOPE, {}, {
                    "min_spend_major": amount, "min_spend_currency": "USD"})
                if expected:
                    self.assertEqual(result["eligibility"], expected)
                else:
                    self.assertNotEqual(result["eligibility"], "EXCLUDED")

    def test_minor_currency_mismatch_is_unknown(self):
        result = evaluate_eligibility("X", SCOPE, {}, {
            "min_spend_minor": 10000, "min_spend_currency": "EUR"})
        self.assertEqual(result["eligibility"], "UNKNOWN")

    def test_negative_minimum_is_unknown(self):
        result = evaluate_eligibility("X", SCOPE, {}, {
            "min_spend_major": -1, "min_spend_currency": "USD"})
        self.assertEqual(result["eligibility"], "UNKNOWN")

    def test_missing_terms_are_unknown(self):
        result = evaluate_eligibility("X", SCOPE, {"brand": "Nike"},
                                      {"eligible_brands": ["Nike"]})
        self.assertEqual(result["eligibility"], "UNKNOWN")

    def test_unknown_does_not_hide_exclusion(self):
        result = evaluate_eligibility("X", SCOPE, {}, {
            "eligible_brands": ["Nike"], "min_spend_minor": 10000,
            "min_spend_currency": "USD"})
        self.assertEqual(result["eligibility"], "EXCLUDED")

    def test_old_single_success_is_not_promising(self):
        rows = [{"campaign": "X", "origin_group": "one",
                 "observed_at": NOW, "success_at": "2026-10-01T00:00:00+00:00",
                 "success_evidence": True}]
        self.assertNotEqual(assess_campaigns(rows, now=NOW)[0]["campaign_confidence"], "PROMISING")

    def test_single_ambiguous_failure_is_not_global_invalid(self):
        rows = [{"campaign": "X", "origin_group": "one", "observed_at": NOW,
                 "negation_evidence": True}]
        self.assertNotEqual(assess_campaigns(rows, now=NOW)[0]["campaign_confidence"], "LIKELY_INVALID")

    def test_missing_check_expiry_is_not_applicable(self):
        rows = [{"campaign": "X", "scope": SCOPE, "checked_at": NOW,
                 "status": "APPLICABLE", "post_minor": 4000,
                 "conditions_confirmed": True, "usage_available": True,
                 "evidence_ref": "fixture", "expires_at": None}]
        ranked = rank_candidates([], [], rows, [], scope=SCOPE,
                                 now=NOW, max_age_seconds=600)
        self.assertNotEqual(ranked[0]["check_status"], "APPLICABLE")

if __name__ == "__main__":
    unittest.main()

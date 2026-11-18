import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from coupon_bridge import CouponBridge, context, assess_campaigns, evaluate_eligibility, rank_candidates

NOW = '2026-11-17T09:00:00+09:00'
LATER = '2026-11-17T09:05:00+09:00'
EXPIRY = '2026-11-17T10:00:00+09:00'
URL = 'https://example.com/promotion'
URL2 = 'https://other.com/promotion'


class CouponBridgeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'collection.db'
        self.book = CouponBridge(self.path)
        self.book.initialize()
        self.scope = context(shop_code='sp', variant_id='v1', currency='USD',
                             destination='US-OR', account_scope='a1', quantity=1,
                             base_minor=10000, basket_key='basket1')

    def check(self, **changes):
        kwargs = dict(scope=self.scope, campaign='FLASH', source_url=URL,
                      checked_at=NOW, expires_at=EXPIRY, status='APPLICABLE',
                      post_minor=7000, conditions_confirmed=True, usage_available=True,
                      evidence_ref='fixture-1')
        kwargs.update(changes)
        return self.book.record_check(**kwargs)

    def select(self, scope=None, now=LATER, max_age=600):
        return self.book.select(scope or self.scope, now=now, max_age_seconds=max_age)

    def test_discovery_only(self):
        self.book.record_discovery(shop_code='sp', campaign='FLASH', source_url=URL,
                                   observed_at=NOW, conditions={'percent': 30})
        self.assertEqual(self.select()['effective_minor'], 10000)

    def test_verified_discount(self):
        key = self.check()
        result = self.select()
        self.assertEqual((result['effective_minor'], result['check_id'], result['sale_approved']), (7000, key, False))

    def test_idempotence_and_reopen(self):
        self.assertEqual(self.check(), self.check())
        self.book = CouponBridge(self.path)
        self.assertEqual(self.select()['effective_minor'], 7000)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM ahc_coupon_checks_v1').fetchone()[0], 1)

    def test_scope_isolation(self):
        self.check()
        for k, v in [('shop_code','kith'), ('variant_id','v2'), ('currency','EUR'),
                     ('destination','US-NY'), ('account_scope','a2'), ('quantity',2),
                     ('base_minor',8000), ('basket_key','basket2')]:
            self.assertEqual(self.select(dict(self.scope, **{k:v}))['status'], 'NO_VERIFIED_DISCOUNT', k)

    def test_expiry_boundary(self):
        self.check()
        self.assertEqual(self.select(now=EXPIRY, max_age=7200)['effective_minor'], 10000)

    def test_staleness(self):
        self.check()
        self.assertEqual(self.select(max_age=299)['effective_minor'], 10000)

    def test_later_failure(self):
        self.check()
        self.check(checked_at=LATER, status='NOT_APPLICABLE', post_minor=None)
        self.assertEqual(self.select()['effective_minor'], 10000)

    def test_conflicting_same_time(self):
        self.check()
        self.check(post_minor=6000)
        self.assertEqual(self.select()['effective_minor'], 10000)

    def test_new_discovery_invalidates(self):
        self.check()
        self.book.record_discovery(shop_code='sp', campaign='FLASH', source_url=URL,
                                   observed_at=LATER, conditions={'changed': True})
        self.assertEqual(self.select()['effective_minor'], 10000)

    def test_no_stacking(self):
        self.check()
        self.check(campaign='OTHER', post_minor=8000)
        self.assertEqual(self.select()['effective_minor'], 7000)

    def test_bad_inputs(self):
        for kwargs in [dict(expires_at=None), dict(expires_at=NOW), dict(conditions_confirmed=False),
                       dict(usage_available=False), dict(post_minor=-1), dict(post_minor=10000),
                       dict(post_minor=7000.0), dict(checked_at='2026-11-17T09:00:00'),
                       dict(source_url='http://example.com'), dict(status='UNKNOWN')]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.check(**kwargs)

    def test_future_check_not_used(self):
        self.check(checked_at=LATER)
        self.assertEqual(self.select(now=NOW)['effective_minor'], 10000)

    def test_raw_adapter_candidate(self):
        raw = SimpleNamespace(store_slug='sp', code='FLASH', source_url=URL, discount_value=30)
        self.book.record_raw(raw, observed_at=NOW)
        self.assertEqual(self.select()['effective_minor'], 10000)
        raw.store_slug = None
        with self.assertRaises(ValueError):
            self.book.record_raw(raw, observed_at=NOW)

    def test_existing_table_preserved(self):
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE TABLE products (id INTEGER)')
            db.execute('INSERT INTO products VALUES (42)')
        self.book.initialize()
        self.check()
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT id FROM products').fetchone()[0], 42)


class AssessCampaignsTest(unittest.TestCase):
    def test_dedup_syndication_and_independent(self):
        discoveries = [
            {"campaign": "C1", "observed_at": "2026-11-15T10:00:00+00:00", "origin_group": "grp1", "report_id": "r1"},
            {"campaign": "C1", "observed_at": "2026-11-15T10:00:00+00:00", "origin_group": "grp1", "report_id": "r1"}, # 同一
            {"campaign": "C1", "observed_at": "2026-11-15T10:00:00+00:00", "report_id": "r1", "origin_group": "grp2"}, # 別origin
            {"campaign": "C1", "observed_at": "2026-11-15T10:00:00+00:00", "source_url": URL}, # 出所不明
        ]
        assessed = assess_campaigns(discoveries, now="2026-11-17T00:00:00+00:00")
        c1 = assessed[0]
        self.assertEqual(c1["roots_count"], 2) # grp1, grp2のみカウント

    def test_future_observation_excluded(self):
        discoveries = [
            {"campaign": "C1", "source_url": URL, "observed_at": "2026-11-18T10:00:00+00:00"},
        ]
        assessed = assess_campaigns(discoveries, now="2026-11-17T00:00:00+00:00")
        self.assertEqual(len(assessed), 0)

    def test_promising_indep_success(self):
        discoveries = [
            {"campaign": "C1", "observed_at": NOW, "origin_group": "g1", "success_evidence": True, "success_at": NOW},
            {"campaign": "C1", "observed_at": NOW, "origin_group": "g2", "success_evidence": True, "success_at": NOW},
        ]
        assessed = assess_campaigns(discoveries, now=LATER)
        self.assertEqual(assessed[0]["campaign_confidence"], "PROMISING")

    def test_promising_after_failure(self):
        discoveries = [
            {"campaign": "C1", "observed_at": NOW, "origin_group": "g1", "negation_evidence": True, "failure_at": NOW},
            {"campaign": "C1", "observed_at": LATER, "origin_group": "g2", "success_evidence": True, "success_at": LATER},
        ]
        assessed = assess_campaigns(discoveries, now=LATER)
        self.assertEqual(assessed[0]["campaign_confidence"], "DISCOVERED")

    def test_official_expired_priority(self):
        discoveries = [
            {"campaign": "C1", "observed_at": NOW, "origin_group": "g1", "success_evidence": True, "success_at": NOW},
            {"campaign": "C1", "observed_at": LATER, "origin_group": "g2", "evidence_type": "OFFICIAL", "official_status": "EXPIRED"},
        ]
        assessed = assess_campaigns(discoveries, now=LATER)
        self.assertEqual(assessed[0]["campaign_confidence"], "EXPIRED")

    def test_single_negation_not_invalid(self):
        discoveries = [
            {"campaign": "C1", "observed_at": NOW, "origin_group": "g1", "negation_evidence": True, "failure_at": NOW},
        ]
        assessed = assess_campaigns(discoveries, now=LATER)
        self.assertEqual(assessed[0]["campaign_confidence"], "DISCOVERED")

    def test_official_priority_over_third_party(self):
        discoveries = [
            {"campaign": "C1", "observed_at": NOW, "origin_group": "g1", "conditions": {"eligible_brands": ["Adidas"]}, "evidence_type": "OFFICIAL", "official_status": "ACTIVE"},
            {"campaign": "C1", "observed_at": LATER, "origin_group": "g2", "conditions": {"eligible_brands": ["Nike"]}},
        ]
        assessed = assess_campaigns(discoveries, now=LATER)
        self.assertEqual(assessed[0]["conditions"], {"eligible_brands": ["Adidas"]})
class EvaluateEligibilityTest(unittest.TestCase):
    def setUp(self):
        self.scope = {"destination": "US-OR", "base_minor": 10000, "currency": "USD"}
        self.facts = {"brand": "Nike", "category": "Shoes", "on_sale": False, "is_first_order": True}

    def test_full_match(self):
        # 規約完全性を証明するfixture（全次元カバー）
        conditions = {
            "eligible_brands": ["Nike"],
            "eligible_categories": ["Shoes"],
            "sale_exclusion": False,
            "first_order_only": False,
            "ship_region": "US-OR",
            "min_spend_major": 100,
            "min_spend_currency": "USD"
        }
        res = evaluate_eligibility("C1", self.scope, self.facts, conditions)
        self.assertEqual(res["eligibility"], "MATCH")
    def test_unknown_brand(self):
        conditions = {"eligible_brands": ["Nike"]}
        res = evaluate_eligibility("C1", self.scope, {"brand": None}, conditions)
        self.assertEqual(res["eligibility"], "UNKNOWN")

    def test_null_excluded_brands_is_unknown(self):
        # null/falseは未知と区別（明示無制限ではない）
        conditions = {"excluded_brands": None}
        res = evaluate_eligibility("C1", self.scope, self.facts, conditions)
        self.assertEqual(res["eligibility"], "UNKNOWN")
        self.assertIn("UNIMPLEMENTED:excluded_brands", res["reasons"]) # 実装上の仕様：Noneは未指定扱いだが、明示無制限ではないためUNKNOWN

    def test_excluded_brand(self):
        conditions = {"excluded_brands": ["Nike"]}
        res = evaluate_eligibility("C1", self.scope, self.facts, conditions)
        self.assertEqual(res["eligibility"], "EXCLUDED")

    def test_first_order_false_excluded(self):
        conditions = {"first_order_only": True}
        res = evaluate_eligibility("C1", self.scope, {"is_first_order": False}, conditions)
        self.assertEqual(res["eligibility"], "EXCLUDED")

    def test_first_order_null_unknown(self):
        conditions = {"first_order_only": True}
        res = evaluate_eligibility("C1", self.scope, {"is_first_order": None}, conditions)
        self.assertEqual(res["eligibility"], "UNKNOWN")

    def test_min_spend_currency_mismatch(self):
        conditions = {"min_spend_major": 50, "min_spend_currency": "EUR"}
        res = evaluate_eligibility("C1", self.scope, self.facts, conditions)
        self.assertEqual(res["eligibility"], "UNKNOWN")
        self.assertIn("CURRENCY_MISMATCH", res["reasons"])

    def test_min_spend_amount_correct_usd(self):
        # GPT基準「一部の条件次元だけでは完全性がないためUNKNOWN」
        conditions = {"min_spend_major": 100, "min_spend_currency": "USD"}
        res = evaluate_eligibility("C1", self.scope, self.facts, conditions)
        self.assertEqual(res["eligibility"], "UNKNOWN")
        self.assertIn("INCOMPLETE_RULES", res["reasons"])
    def test_min_spend_amount_not_met_usd(self):
        # USD 200 -> 20000 minor
        conditions = {"min_spend_major": 200, "min_spend_currency": "USD"}
        res = evaluate_eligibility("C1", self.scope, self.facts, conditions)
        self.assertEqual(res["eligibility"], "EXCLUDED")
        self.assertIn("MIN_SPEND_NOT_MET", res["reasons"])

    def test_unsupported_condition_is_unknown(self):
        conditions = {"eligible_brands": ["Nike"], "max_uses_per_user": 1}
        res = evaluate_eligibility("C1", self.scope, self.facts, conditions)
        self.assertEqual(res["eligibility"], "UNKNOWN")
        self.assertIn("UNIMPLEMENTED:max_uses_per_user", res["reasons"])


class RankCandidatesTest(unittest.TestCase):
    def setUp(self):
        self.scope = context(shop_code='sp', variant_id='v1', currency='USD', destination='US-OR',
                             account_scope='a1', quantity=1, base_minor=10000, basket_key='b1')
        self.assessed = [{"campaign": "C1", "campaign_confidence": "DISCOVERED", "conditions": {}}]
        self.evaluated = [{"campaign": "C1", "eligibility": "UNKNOWN", "reasons": []}]

    def test_no_leak_effective_minor(self):
        ranked = rank_candidates(self.assessed, self.evaluated, [], [], scope=self.scope, now=NOW, max_age_seconds=600)
        self.assertNotIn("effective_minor", ranked[0])
        self.assertNotIn("sale_approved", ranked[0])

    def test_scope_isolation_in_ranking(self):
        other_scope = dict(self.scope, variant_id='v2')
        checks = [{"scope": other_scope, "campaign": "C1", "checked_at": NOW, "expires_at": EXPIRY, "status": "APPLICABLE"}]
        ranked = rank_candidates(self.assessed, self.evaluated, checks, [], scope=self.scope, now=NOW, max_age_seconds=600)
        self.assertEqual(ranked[0]["check_status"], "NOT_CHECKED")

    def test_expired_check_is_stale(self):
        checks = [{"scope": self.scope, "campaign": "C1", "checked_at": NOW, "expires_at": NOW, "status": "APPLICABLE"}]
        ranked = rank_candidates(self.assessed, self.evaluated, checks, [], scope=self.scope, now=LATER, max_age_seconds=600)
        self.assertEqual(ranked[0]["check_status"], "STALE")

    def test_conflicting_same_time_diff_amount(self):
        checks = [
            {"scope": self.scope, "campaign": "C1", "checked_at": NOW, "expires_at": EXPIRY, "status": "APPLICABLE", "post_minor": 7000},
            {"scope": self.scope, "campaign": "C1", "checked_at": NOW, "expires_at": EXPIRY, "status": "APPLICABLE", "post_minor": 6000}
        ]
        ranked = rank_candidates(self.assessed, self.evaluated, checks, [], scope=self.scope, now=LATER, max_age_seconds=600)
        self.assertEqual(ranked[0]["check_status"], "UNKNOWN")

    def test_check_only_candidate(self):
        checks = [{"scope": self.scope, "campaign": "C2", "checked_at": NOW, "expires_at": EXPIRY, "status": "APPLICABLE", "conditions_confirmed": True, "usage_available": True}]
        ranked = rank_candidates([], [], checks, [], scope=self.scope, now=LATER, max_age_seconds=600)
        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0]["campaign"], "C2")
        self.assertEqual(ranked[0]["check_status"], "APPLICABLE")

    def test_expired_isolated(self):
        assessed = [
            {"campaign": "C1", "campaign_confidence": "EXPIRED", "conditions": {}},
            {"campaign": "C2", "campaign_confidence": "DISCOVERED", "conditions": {}}
        ]
        evaluated = [
            {"campaign": "C1", "eligibility": "UNKNOWN", "reasons": []},
            {"campaign": "C2", "eligibility": "UNKNOWN", "reasons": []}
        ]
        ranked = rank_candidates(assessed, evaluated, [], [], scope=self.scope, now=NOW, max_age_seconds=600)
        self.assertEqual(ranked[0]["campaign"], "C2") # EXPIREDは隔離され下位へ
        self.assertEqual(ranked[1]["campaign"], "C1")


class ListCandidatesIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'collection.db'
        self.book = CouponBridge(self.path)
        self.book.initialize()
        self.scope = context(shop_code='sp', variant_id='v1', currency='USD', destination='US-OR',
                             account_scope='a1', quantity=1, base_minor=10000, basket_key='b1')
        self.facts = {"brand": "Nike", "category": "Shoes", "on_sale": False, "is_first_order": True}

    def test_full_flow_ranking(self):
        # 規約完全性の証明
        conditions = {"eligible_brands": ["Nike"], "eligible_categories": ["Shoes"], "sale_exclusion": False}
        self.book.record_discovery(shop_code='sp', campaign='C1', source_url=URL, observed_at=NOW, conditions=conditions)
        self.book.record_check(scope=self.scope, campaign='C1', source_url=URL, checked_at=NOW, expires_at=EXPIRY,
                               status='APPLICABLE', post_minor=8000, conditions_confirmed=True, usage_available=True, evidence_ref='ev1')
        candidates = self.book.list_candidates(self.scope, now=LATER, max_age_seconds=600, product_facts=self.facts)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]['campaign'], 'C1')
        self.assertEqual(candidates[0]['eligibility'], 'MATCH')
        self.assertEqual(candidates[0]['check_status'], 'APPLICABLE')


if __name__ == '__main__':
    unittest.main()

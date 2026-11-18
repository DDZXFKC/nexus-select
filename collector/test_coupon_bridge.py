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
    def test_dedup_syndication(self):
        discoveries = [
            {"campaign": "C1", "source_url": URL, "observed_at": "2026-11-15T10:00:00+00:00", "origin_group": "grp1"},
            {"campaign": "C1", "source_url": URL2, "observed_at": "2026-11-15T10:00:00+00:00", "origin_group": "grp1"},
        ]
        assessed = assess_campaigns(discoveries)
        self.assertEqual(assessed[0]["roots_count"], 1)
        self.assertEqual(assessed[0]["campaign_confidence"], "DISCOVERED")

    def test_independent_sources(self):
        discoveries = [
            {"campaign": "C1", "source_url": URL, "observed_at": "2026-11-15T10:00:00+00:00", "origin_group": "grp1"},
            {"campaign": "C1", "source_url": URL2, "observed_at": "2026-11-15T10:00:00+00:00", "origin_group": "grp2"},
        ]
        assessed = assess_campaigns(discoveries)
        self.assertEqual(assessed[0]["roots_count"], 2)

    def test_conflict_and_negation(self):
        discoveries = [
            {"campaign": "C1", "source_url": URL, "observed_at": "2026-11-15T10:00:00+00:00", "conditions_conflict": True},
            {"campaign": "C2", "source_url": URL, "observed_at": "2026-11-15T10:00:00+00:00", "negation_evidence": True},
        ]
        assessed = assess_campaigns(discoveries)
        self.assertEqual([a["campaign_confidence"] for a in assessed], ["CONFLICT", "LIKELY_INVALID"])


class EvaluateEligibilityTest(unittest.TestCase):
    def setUp(self):
        self.scope = {"destination": "US-OR", "base_minor": 10000}
        self.facts = {"brand": "Nike", "category": "Shoes", "on_sale": False, "is_first_order": True}

    def test_brand_excluded(self):
        conditions = {"excluded_brands": ["Nike"]}
        res = evaluate_eligibility("C1", self.scope, self.facts, conditions)
        self.assertEqual(res["eligibility"], "EXCLUDED")

    def test_min_spend_not_met(self):
        conditions = {"min_spend_minor": 20000}
        res = evaluate_eligibility("C1", self.scope, self.facts, conditions)
        self.assertEqual(res["eligibility"], "EXCLUDED")

    def test_full_match(self):
        conditions = {"eligible_brands": ["Nike"], "eligible_categories": ["Shoes"]}
        res = evaluate_eligibility("C1", self.scope, self.facts, conditions)
        self.assertEqual(res["eligibility"], "MATCH")


class RankCandidatesTest(unittest.TestCase):
    def setUp(self):
        self.scope = context(shop_code='sp', variant_id='v1', currency='USD', destination='US-OR',
                             account_scope='a1', quantity=1, base_minor=10000, basket_key='b1')

    def test_no_leak_effective_minor(self):
        assessed = [{"campaign": "C1", "campaign_confidence": "DISCOVERED", "conditions": [{}]}]
        evaluated = [{"campaign": "C1", "eligibility": "MATCH", "reasons": []}]
        ranked = rank_candidates(assessed, evaluated, [], scope=self.scope, now=NOW, max_age_seconds=600)
        self.assertNotIn("effective_minor", ranked[0])
        self.assertNotIn("sale_approved", ranked[0])

    def test_scope_isolation_in_ranking(self):
        assessed = [{"campaign": "C1", "campaign_confidence": "DISCOVERED", "conditions": [{}]}]
        evaluated = [{"campaign": "C1", "eligibility": "MATCH", "reasons": []}]
        other_scope = dict(self.scope, variant_id='v2')
        checks = [{"scope": other_scope, "campaign": "C1", "checked_at": NOW, "expires_at": EXPIRY, "status": "APPLICABLE"}]
        ranked = rank_candidates(assessed, evaluated, checks, scope=self.scope, now=NOW, max_age_seconds=600)
        self.assertEqual(ranked[0]["check_status"], "NOT_CHECKED")

    def test_expired_check_is_stale(self):
        assessed = [{"campaign": "C1", "campaign_confidence": "DISCOVERED", "conditions": [{}]}]
        evaluated = [{"campaign": "C1", "eligibility": "MATCH", "reasons": []}]
        checks = [{"scope": self.scope, "campaign": "C1", "checked_at": NOW, "expires_at": NOW, "status": "APPLICABLE"}]
        ranked = rank_candidates(assessed, evaluated, checks, scope=self.scope, now=LATER, max_age_seconds=600)
        self.assertEqual(ranked[0]["check_status"], "STALE")


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
        self.book.record_discovery(shop_code='sp', campaign='C1', source_url=URL, observed_at=NOW, conditions={"eligible_brands": ["Nike"]})
        self.book.record_check(scope=self.scope, campaign='C1', source_url=URL, checked_at=NOW, expires_at=EXPIRY,
                               status='APPLICABLE', post_minor=8000, conditions_confirmed=True, usage_available=True, evidence_ref='ev1')
        candidates = self.book.list_candidates(self.scope, now=LATER, max_age_seconds=600, product_facts=self.facts)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]['campaign'], 'C1')
        self.assertEqual(candidates[0]['eligibility'], 'MATCH')
        self.assertEqual(candidates[0]['check_status'], 'APPLICABLE')


if __name__ == '__main__':
    unittest.main()

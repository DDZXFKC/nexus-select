"""Executable synthetic regression suite for GLM corr and Nike v1 contract.

No source fixtures are fabricated as evidence of the real 27 matches.
Run: python3 -m unittest discover -s tests -p 'test_cross_shop_corr.py' -v
"""
import importlib.util
import unittest
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "tools" / "cross_shop_corr.py"
spec = importlib.util.spec_from_file_location("cross_shop_corr", FILE)
corr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(corr)


def sp(brand, style, color="", sid=None, sellable="1", **extra):
    return {"brand": brand, "style": style, "color": color,
            "source_id": sid or style + color, "sellable": sellable, **extra}


def fl(brand, code, fid=None, **extra):
    return {"brand": brand, "code": code, "source_id": fid or code, **extra}


def run(flrows, sprows, manual=()):
    return corr.correlate(flrows, sprows, manual)


class CorrContractTests(unittest.TestCase):
    def test_GLMTail3_and_full_corpus(self):
        r = run([fl("HOKA", "130BBLC")],
                [sp("HOKA", "1155130", "BBLC")])
        self.assertEqual(r[0]["status"], "AUTO")
        self.assertEqual(r[0]["sp_style"], "1155130")
        self.assertEqual(r[0]["tags"], "TAIL3")

    def test_GLMTail3_short_key_hold(self):
        r = run([fl("UGG", "130CHE")], [sp("UGG", "1155130", "CHE")])
        self.assertEqual(r[0]["status"], "HOLD_SHORT_KEY")

    def test_GLMTail_full_corpus_ambiguity_even_unsellable(self):
        r = run([fl("UGG", "130BBLC")],
                [sp("UGG", "1155130", "BBLC"),
                 sp("UGG", "88130", "BBLC", sellable="0")])
        self.assertEqual(r[0]["status"], "HOLD_AMBIG")
        self.assertEqual(r[0]["candidate_count"], 2)

    def test_GLMTail_leading_zero_preserved(self):
        r = run([fl("UGG", "0518BBLC")],
                [sp("UGG", "100518", "BBLC"),
                 sp("UGG", "518", "BBLC")])
        self.assertEqual(r[0]["status"], "AUTO")
        self.assertEqual(r[0]["sp_style"], "100518")

    def test_GLMTail_name_mismatch_advisory_not_gate(self):
        r = run([fl("HOKA", "D9RCCZ", name="White / White")],
                [sp("HOKA", "1200D9R", "CCZ", name="Flame")])
        self.assertEqual(r[0]["status"], "HOLD_NO_COLOR")
        # Valid numeric-core case with differing names:
        r = run([fl("HOKA", "130BBLC", name="White / White")],
                [sp("HOKA", "1155130", "BBLC", name="Flame")])
        self.assertEqual(r[0]["status"], "AUTO")
        self.assertIn("ADV_NAME_NOTE", r[0]["tags"])

    def test_GLMVans_prefix_one_time_longest_first(self):
        self.assertEqual(corr.vans_strip_one("VN000EFG"), "000EFG")
        self.assertEqual(corr.vans_strip_one("00ZB8CD"), "ZB8CD")
        self.assertEqual(corr.vans_strip_one("V00X"), "00X")
        self.assertEqual(corr.vans_strip_one("000X"), "0X")
        r = run([fl("Vans", "VN000EFG")], [sp("VANS", "000EFG")])
        self.assertEqual(r[0]["status"], "AUTO")

    def test_GLMVans_manual_seed_truncated(self):
        r = corr.correlate([fl("Vans", "00ZB8CD")], [sp("Vans", "ZB8CDA")])
        self.assertEqual(r[0]["status"], "AUTO")
        self.assertEqual(r[0]["rule"], "MANUAL_TRUNCATED")

    def test_GLMLegacy_and_no_color(self):
        r = run([fl("UGG", "2072001"), fl("HOKA", "AR422710"),
                 fl("VANS", "1234567")], [sp("UGG", "111", "CHE")])
        self.assertEqual([x["status"] for x in r],
                         ["HOLD_LEGACY_NUMERIC", "HOLD_NO_COLOR", "HOLD_LEGACY_NUMERIC"])

    def test_GLMNoMatch_is_not_hold(self):
        r = run([fl("VANS", "VN000EFG")], [sp("VANS", "UNRELATED")])
        self.assertEqual(r[0]["status"], "NO_MATCH")
        self.assertEqual(r[0]["hold_reason_codes"], "")

    def test_GLMCollision_all_fl_rows_held(self):
        r = run([fl("HOKA", "130BBLC", "a"), fl("HOKA", "130BBLC", "b")],
                [sp("HOKA", "1155130", "BBLC")])
        self.assertEqual([x["status"] for x in r], ["HOLD_COLLISION"] * 2)

    def test_Nike_current_generation_K1_K2_and_zero(self):
        self.assertEqual(corr.nike_k1("IB0018-004"), "B0018004")
        self.assertEqual(corr.nike_k2("B0018004"), "0018004")
        r = run([fl("NIKE", "B0018004")],
                [sp("Nike", "IB0018-004")])
        self.assertEqual(r[0]["status"], "AUTO")
        self.assertEqual(r[0]["rule"], "nike_fl_v1")
        self.assertEqual(r[0]["matched_key"], "B0018004")
        self.assertEqual(r[0]["candidate_count"], 1)

    def test_Nike_NFKC_and_hyphens(self):
        self.assertEqual(corr.nike_k1("ＩＢ００１８－００４"), "B0018004")
        self.assertEqual(corr.nike_k1("IB0018–004"), "B0018004")

    def test_Nike_old_formats_never_match(self):
        self.assertIsNone(corr.nike_k1("123456-001"))
        self.assertIsNone(corr.nike_k1("IB0018004"))
        self.assertIsNone(corr.nike_k1("IB0018-0004"))
        r = run([fl("NIKE", "12345678")],
                [sp("NIKE", "IB0018-004")])
        self.assertEqual(r[0]["status"], "HOLD_UNVERIFIED_FORMAT")

    def test_Nike_collision_not_tiebroken_by_name(self):
        r = run([fl("NIKE", "B0018004", name="same")],
                [sp("NIKE", "IB0018-004", sid="one", name="same"),
                 sp("NIKE", "XB0018-004", sid="two", name="different")])
        self.assertEqual(r[0]["status"], "HOLD_AMBIG")
        self.assertEqual(r[0]["candidate_count"], 2)

    def test_Nike_stop_on_first_party_counterexample(self):
        r = corr.correlate([fl("NIKE", "B0018004")],
                           [sp("NIKE", "IB0018-004")], (), suspended_nike=True)
        self.assertEqual(r[0]["status"], "HOLD_RULE_SUSPENDED")

    def test_Nike_evidence_tier_forwarded(self):
        r = run([fl("NIKE", "B0018004", evidence_tier="A")],
                [sp("NIKE", "IB0018-004")])
        self.assertEqual(r[0]["evidence_tier"], "A")

    def test_Stage3_verified_costs_and_no_zero_fill(self):
        flrows = [fl("NIKE", "B0018004", cost_calculated="1", cost_verified="1",
                     procurement_total_jpy="12000", procurement_unit="COLORWAY_ONE_UNIT")]
        sprows = [sp("NIKE", "IB0018-004", cost_calculated="1", cost_verified="1",
                     procurement_total_jpy="10000", procurement_unit="COLORWAY_ONE_UNIT")]
        matches = run(flrows, sprows)
        output = corr.join_adoption(matches, flrows, sprows)
        self.assertEqual(output[0]["winner_shop"], "SP")
        sprows[0]["cost_verified"] = "0"
        output = corr.join_adoption(matches, flrows, sprows)
        self.assertEqual(output[0]["winner_shop"], "FL")
        self.assertIn("SP:total_unverified", output[0]["adoption_reason"])
        flrows[0]["cost_calculated"] = "0"
        output = corr.join_adoption(matches, flrows, sprows)
        self.assertEqual(output[0]["adoption"], "HOLD")

    def test_full_corpus_required_and_duplicates_rejected(self):
        with self.assertRaises(ValueError):
            run([fl("UGG", "130BBLC")], [])
        with self.assertRaises(ValueError):
            run([fl("UGG", "130BBLC")],
                [sp("UGG", "1155130", "BBLC", sid="duplicate"),
                 sp("UGG", "888130", "BBLC", sid="duplicate")])


if __name__ == "__main__":
    unittest.main()

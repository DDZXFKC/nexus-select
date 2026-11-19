"""Expected-value tests for collector/color_fullrun.py (run: python3 -m unittest collector/test_color_fullrun.py)."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import color_fullrun as cf  # noqa: E402


def m(cid, token, hexv="", hex_status="UNKNOWN", scope="COMMON", key="*", fam="", fam_status="UNKNOWN"):
    return {"color_id": cid, "scope_type": scope, "scope_key": key, "token_normalized": token,
            "token_original": token.title(), "display_hex": hexv, "hex_status": hex_status,
            "family_internal": fam, "family_status": fam_status}


MASTER = [
    m("C-1", "black", "#171717", "APPROVED_APPROX", fam="black", fam_status="CONFIRMED"),
    m("C-2", "white", "#FFFFFF", "APPROVED_APPROX", fam="white", fam_status="CONFIRMED"),
    m("C-3", "red", "#C62828", "APPROVED_APPROX", fam="red", fam_status="CONFIRMED"),
    m("C-4", "brown", "#795548", "DRAFT", fam="brown", fam_status="CONFIRMED"),
    m("C-5", "multi", "#8A7896", "DRAFT"),
    m("C-6", "photon dust", "", "UNKNOWN"),
    m("C-7", "phantom", "#E7E2D9", "DRAFT", scope="BRAND", key="NIKE"),
    m("C-8", "volt", "#C8ED36", "CONFLICT", fam="yellow", fam_status="DRAFT"),
]


def prod(pid, tokens, ids, brand="NIKE", status="TAG_SUPPORTED", swatch=""):
    comps = [{"position": i + 1, "token_original": t, "color_id": c} for i, (t, c) in enumerate(zip(tokens, ids))]
    return {"shop_code": "SP", "market": "US", "supplier_product_id": pid, "supplier_color_key": "single",
            "brand_id": brand, "colorway_original": "/".join(tokens), "colorway_status": status,
            "components_json": json.dumps(comps), "swatch_status": swatch}


def status_of(row):
    out, _, _, _ = cf.recompute(MASTER, [row])
    return out[0]["swatch_status"], out[0]


class SwatchRules(unittest.TestCase):
    def test_confirmed_all_approved(self):
        st, row = status_of(prod("1", ["Black", "White", "Red"], ["C-1", "C-2", "C-3"]))
        self.assertEqual(st, "CONFIRMED")
        self.assertEqual([row["swatch_hex_1"], row["swatch_hex_2"], row["swatch_hex_3"]], ["#171717", "#FFFFFF", "#C62828"])

    def test_draft_when_one_not_approved(self):
        self.assertEqual(status_of(prod("2", ["Black", "Brown"], ["C-1", "C-4"]))[0], "DRAFT")

    def test_unknown_missing_hex(self):
        self.assertEqual(status_of(prod("3", ["Black", "Photon Dust"], ["C-1", "C-6"]))[0], "UNKNOWN")

    def test_unknown_zero_components(self):
        self.assertEqual(status_of(prod("4", [], []))[0], "UNKNOWN")

    def test_multi_in_display_is_unknown_even_with_hex(self):
        self.assertEqual(status_of(prod("5", ["Multi", "Black"], ["C-5", "C-1"]))[0], "UNKNOWN")

    def test_multi_only_as_fourth_color_ignored(self):
        st, row = status_of(prod("6", ["Black", "White", "Red", "Multi"], ["C-1", "C-2", "C-3", "C-5"]))
        self.assertEqual(st, "CONFIRMED")

    def test_missing_hex_not_skipped_to_fourth(self):
        st, row = status_of(prod("7", ["Black", "Photon Dust", "Red", "White"], ["C-1", "C-6", "C-3", "C-2"]))
        self.assertEqual(st, "UNKNOWN")
        self.assertEqual(row["swatch_hex_3"], "")

    def test_duplicate_colors_kept(self):
        st, row = status_of(prod("8", ["Black", "Black", "Red"], ["C-1", "C-1", "C-3"]))
        self.assertEqual(st, "CONFIRMED")
        self.assertEqual(row["swatch_hex_1"], row["swatch_hex_2"])

    def test_hold_contradiction_first(self):
        self.assertEqual(status_of(prod("9", ["Black"], ["C-1"], status="HOLD_CONTRADICTION"))[0], "HOLD")

    def test_hold_null_reference(self):
        self.assertEqual(status_of(prod("10", ["Black", "Sea Salt"], ["C-1", None]))[0], "HOLD")

    def test_hold_unknown_id(self):
        self.assertEqual(status_of(prod("11", ["Black"], ["C-999"]))[0], "HOLD")

    def test_hold_token_mismatch(self):
        self.assertEqual(status_of(prod("12", ["White"], ["C-1"]))[0], "HOLD")

    def test_hold_other_brand_scope(self):
        self.assertEqual(status_of(prod("13", ["Phantom"], ["C-7"], brand="JORDAN"))[0], "HOLD")

    def test_own_brand_scope_ok(self):
        self.assertEqual(status_of(prod("14", ["Phantom"], ["C-7"], brand="Nike"))[0], "DRAFT")

    def test_hold_hex_conflict(self):
        self.assertEqual(status_of(prod("15", ["Volt"], ["C-8"]))[0], "HOLD")

    def test_family_status_not_a_condition(self):
        # brown family CONFIRMED but hex DRAFT -> DRAFT; volt family DRAFT irrelevant (HOLD by hex)
        self.assertEqual(status_of(prod("16", ["Brown"], ["C-4"]))[0], "DRAFT")

    def test_bad_reference_beyond_display_is_reported_not_displayed(self):
        out, _, integrity, _ = cf.recompute(MASTER, [prod("17", ["Black", "White", "Red", "Sea Salt"], ["C-1", "C-2", "C-3", None])])
        self.assertEqual(out[0]["swatch_status"], "CONFIRMED")
        self.assertEqual(integrity, [{"supplier_product_id": "17", "position": 4, "problem": "NULL_ID"}])

    def test_protected_columns_unchanged(self):
        row = prod("18", ["Black"], ["C-1"], status="CONFIRMED_BY_TITLE_RULE", swatch="DRAFT")
        out, changes, _, _ = cf.recompute(MASTER, [row])
        for col in ("colorway_status", "components_json", "colorway_original", "supplier_product_id"):
            self.assertEqual(out[0][col], row[col])
        self.assertIn({"supplier_product_id": "18", "column": "swatch_status", "before": "DRAFT", "after": "CONFIRMED"}, changes)

    def test_search_families_split(self):
        _, row = status_of(prod("19", ["Black", "Volt"], ["C-1", "C-8"]))
        self.assertEqual(json.loads(row["search_families_json"]), ["black"])
        self.assertEqual(json.loads(row["search_families_candidates_json"]), ["yellow"])

    def test_duplicate_product_rows_rejected(self):
        with self.assertRaises(cf.DataError):
            cf.recompute(MASTER, [prod("20", ["Black"], ["C-1"]), prod("20", ["Black"], ["C-1"])])

    def test_broken_position_rejected(self):
        row = prod("21", ["Black"], ["C-1"])
        row["components_json"] = json.dumps([{"position": 2, "token_original": "Black", "color_id": "C-1"}])
        with self.assertRaises(cf.DataError):
            cf.recompute(MASTER, [row])


class MasterValidation(unittest.TestCase):
    def test_bad_id(self):
        with self.assertRaises(cf.DataError):
            cf.Master([m("X1", "black")])

    def test_duplicate_id(self):
        with self.assertRaises(cf.DataError):
            cf.Master([m("C-1", "black"), m("C-1", "white")])

    def test_duplicate_scope_key_normalized(self):
        with self.assertRaises(cf.DataError):
            cf.Master([m("C-1", "phantom", scope="BRAND", key="NIKE"), m("C-2", "Phantom", scope="BRAND", key="nike")])


class Generate(unittest.TestCase):
    def setUp(self):
        self.raw = {"100": {"id": 100, "handle": "air-max-sea-salt-black", "tags": ["Color_Black", "Color_White"]},
                    "101": {"id": 101, "handle": "dunk-low-phantom", "tags": []},
                    "102": {"id": 102, "handle": "cap-2-pack", "tags": []}}

    def p(self, pid, color, status="TAG_SUPPORTED", brand="NIKE", title="", stock="True"):
        return {"product_id": pid, "brand": brand, "color_name": color, "color_name_status": status,
                "title_original": title, "source_url": "", "in_stock": stock}

    def test_new_token_common_stable_id_and_existing_brand_row_not_reused(self):
        prods = [self.p("100", "Sea Salt/Black"), self.p("101", "Phantom", brand="JORDAN")]
        rows, new, _ = cf.generate(prods, self.raw, MASTER, set(), "2026-11-18T04:53:14")
        self.assertEqual([r["color_id"] for r in new], ["C-9", "C-10"])
        self.assertTrue(all(r["scope_type"] == "COMMON" for r in new))
        self.assertEqual(new[1]["token_normalized"], "phantom")  # JORDAN does not borrow NIKE's row
        rows2, new2, _ = cf.generate(prods, self.raw, MASTER, set(), "2026-11-18T04:53:14")
        self.assertEqual(rows, rows2)
        self.assertEqual(new, new2)

    def test_existing_ids_never_renumbered(self):
        _, new, _ = cf.generate([self.p("100", "Black/White")], self.raw, MASTER, set(), "x")
        self.assertEqual(new, [])

    def test_distinct_counts(self):
        _, _, stats = cf.generate([self.p("100", "Black/Black/White")], self.raw, MASTER, set(), "x")
        self.assertEqual({s["color_id"]: s["distinct_products"] for s in stats}, {"C-1": 1, "C-2": 1})

    def test_existing_sheet_rows_skipped(self):
        rows, _, _ = cf.generate([self.p("100", "Black")], self.raw, MASTER, {"SP|US|100|single"}, "x")
        self.assertEqual(rows, [])

    def test_raw_missing_rejected(self):
        with self.assertRaises(cf.DataError):
            cf.generate([self.p("999", "Black")], self.raw, MASTER, set(), "x")

    def test_raw_id_mismatch_rejected(self):
        raw = dict(self.raw)
        raw["100"] = {"id": 555}
        with self.assertRaises(cf.DataError):
            cf.generate([self.p("100", "Black")], raw, MASTER, set(), "x")

    def test_title_rule_conditions(self):
        ok = cf.title_rule_ok("Air Max Mens (Sea Salt/Black) Free Shipping", "Sea Salt/Black",
                              "air-max-sea-salt-black", {"black"}, ["", "black"])
        self.assertTrue(ok)
        self.assertFalse(cf.title_rule_ok("Air Max (Sea Salt/Black)", "Sea Salt/Black", "air-max", set(), []))
        self.assertFalse(cf.title_rule_ok("Cap (2 Pack)", "2 Pack", "cap-2-pack", set(), []))
        self.assertFalse(cf.title_rule_ok("Air Max (Black)", "Black", "air-max-black", {"red"}, ["black"]))
        self.assertFalse(cf.title_rule_ok("Air Max (Black) Unknown Suffix", "Black", "air-max-black", set(), ["black"]))

    def test_title_candidate_not_promoted_without_evidence(self):
        rows, _, _ = cf.generate([self.p("102", "2 Pack", status="TITLE_CANDIDATE", title="Cap (2 Pack)")],
                                 self.raw, MASTER, set(), "x")
        self.assertEqual(rows[0]["colorway_status"], "TITLE_CANDIDATE")

    def test_sole_family_requires_all_components_resolved(self):
        rows, _, _ = cf.generate([self.p("100", "Black/Sea Salt")], self.raw, MASTER, set(), "x")
        self.assertEqual(rows[0]["main_family_internal"], "")


if __name__ == "__main__":
    unittest.main()

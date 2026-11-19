"""Synthetic G-1 fixture tests: no production A2 or BUYMA data required.

Run: python3 -m unittest discover -s tests -p 'test_join_a2_brand_sizes.py' -v
"""
import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "join_a2_brand_sizes.py"
spec = importlib.util.spec_from_file_location("g1_join", SCRIPT)
g1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g1)

AC = ["brand", "department", "size_original", "cm", "source_url", "product_id", "category"]
VC = ["sku", "product_id", "variant_id", "brand", "department", "size_original", "category"]


def chart(size, cm, url="https://example.org/chart", scope="", dept="Men", category=""):
    return dict(brand="TEST", department=dept, size_original=size, cm=cm,
                source_url=url, product_id=scope, category=category)


def variant(vid, size, pid="p1", dept="Men", category=""):
    return dict(sku="sku-" + vid, product_id=pid, variant_id=vid, brand="TEST",
                department=dept, size_original=size, category=category)


def write_csv(path, cols, data):
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=cols)
        writer.writeheader()
        writer.writerows(data)


class G1FixtureTests(unittest.TestCase):
    def run_join(self, charts, variants, rules=None):
        with tempfile.TemporaryDirectory() as folder:
            a2 = Path(folder) / "a2.csv"
            vs = Path(folder) / "variants.csv"
            write_csv(a2, AC, charts)
            write_csv(vs, VC, variants)
            cfg = {
                "a2_columns": dict(brand="brand", department="department",
                                   size_original="size_original", cm="cm",
                                   source_url="source_url", scope="product_id"),
                "variant_columns": dict(sku="sku", product_id="product_id",
                                        variant_id="variant_id", brand="brand",
                                        department="department", size_original="size_original"),
                "department_rules": rules or {}
            }
            return g1.join(a2, vs, cfg)

    def test_conflicting_cm_holds(self):
        rows, _ = self.run_join([chart("9", "27"), chart("9", "27.5")],
                                [variant("a", "9")])
        self.assertEqual(rows[0]["status"], "HOLD_CONFLICT")
        self.assertEqual(rows[0]["cm"], "")

    def test_empty_cm_holds(self):
        rows, _ = self.run_join([chart("8", "")], [variant("a", "8")])
        self.assertEqual(rows[0]["status"], "HOLD_NO_JP_CM")

    def test_scope_exact_product_only(self):
        rows, _ = self.run_join([chart("7", "25", scope="p1")],
                                [variant("a", "7"), variant("b", "7", pid="p2")])
        self.assertEqual([r["status"] for r in rows], ["MATCHED", "HOLD_NO_CHART"])
        self.assertEqual(rows[0]["cm"], "25")

    def test_bad_provenance_is_row_level_and_audited(self):
        rows, excluded = self.run_join(
            [chart("6", "24", url=""), chart("7", "25")],
            [variant("a", "6"), variant("b", "7")])
        self.assertEqual([r["status"] for r in rows],
                         ["HOLD_NO_PROVENANCE", "MATCHED"])
        self.assertEqual(rows[0]["excluded_no_provenance"], "1")
        self.assertEqual(excluded["HOLD_NO_PROVENANCE"], 1)

    def test_invalid_url_not_usable_and_valid_candidate_survives(self):
        rows, excluded = self.run_join(
            [chart("9", "27", url="http://invalid.example"),
             chart("9", "27.5", url="https://example.org/valid")],
            [variant("a", "9")])
        self.assertEqual(rows[0]["status"], "MATCHED")
        self.assertEqual(rows[0]["cm"], "27.5")
        self.assertEqual(rows[0]["excluded_no_provenance"], "1")
        self.assertEqual(excluded["HOLD_NO_PROVENANCE"], 1)

    def test_department_dictionary_records_evidence(self):
        rules = {"variants": [{"id": "source_category_v1", "column": "category",
                               "map": {"mens shoes": "Men"}}]}
        rows, _ = self.run_join([chart("9", "27")],
                                [variant("a", "9", dept="", category="Mens Shoes")], rules)
        self.assertEqual(rows[0]["status"], "MATCHED")
        self.assertEqual(rows[0]["department"], "Men")
        self.assertEqual(rows[0]["department_dictionary_version"], "dept-spec-v1")
        self.assertIn("source_category_v1", rows[0]["department_rule"])
        evidence = json.loads(rows[0]["department_evidence"])
        self.assertEqual(evidence[0]["raw"], "Mens Shoes")

    def test_department_conflict_is_not_guessed(self):
        rules = {"variants": [{"id": "category_v1", "column": "category",
                               "map": {"womens shoes": "Women"}}]}
        rows, _ = self.run_join([chart("9", "27")],
                                [variant("a", "9", dept="Men", category="Womens Shoes")], rules)
        self.assertEqual(rows[0]["status"], "HOLD_DEPARTMENT_AMBIGUOUS")
        self.assertEqual(rows[0]["cm"], "")

    def test_unknown_department_is_manual_hold(self):
        rows, _ = self.run_join([chart("9", "27")],
                                [variant("a", "9", dept="Unisex")])
        self.assertEqual(rows[0]["status"], "HOLD_DEPARTMENT_UNRESOLVED")
        self.assertEqual(rows[0]["department"], "")

    def test_existing_ugg_ambiguity_kept(self):
        rows, _ = self.run_join([chart("4C", "11")],
                                [variant("41707750162638", "4C")])
        self.assertEqual(rows[0]["status"], "HOLD_UGG_INFANT_AMBIGUITY")

    def test_unmapped_a2_department_excluded(self):
        rows, excluded = self.run_join([chart("9", "27", dept="Unknown")],
                                        [variant("a", "9")])
        self.assertEqual(rows[0]["status"], "HOLD_NO_CHART")
        self.assertEqual(excluded["HOLD_DEPARTMENT_UNRESOLVED"], 1)


if __name__ == "__main__":
    unittest.main()

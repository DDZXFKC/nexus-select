"""Synthetic 163-row SP pool category preflight regression tests."""
import csv
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("batch3_preflight", ROOT / "tools" / "batch3_category_preflight.py")
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def csvwrite(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fields)
        w.writeheader()
        w.writerows(rows)


class CategoryPreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.pool = base / "pool.csv"
        self.selection = base / "selection.csv"
        self.master = base / "master.csv"
        self.rules = base / "rules.json"
        self.pool_rows = [
            {"SKU": "SP-" + str(i), "brand": "UGG", "department": "Men",
             "source_product_type": "Neumel Boots"} for i in range(163)]
        self.pool_rows[0]["source_product_type"] = "Tasman Slipper Mens Sandals"
        self.selected = [{"SKU": "SP-" + str(i)} for i in range(10)]
        self.categories = [
            {"category_id": "3320", "product_type": "sandals"},
            {"category_id": "3323", "product_type": "boots"}]
        self.config = {
            "version": "v1", "dictionary_version": "v1",
            "category_overrides_by_sku": {
                "SP-0": {"category_id": "3320", "evidence_ref": "glm:E-1", "verified_on": "2026-11-20"}},
            "category_dictionary": [],
            "brand_dept_defaults": [{
                "brand": "UGG", "department": "Men", "category_id": "3323",
                "evidence_ref": "category-master:UGG-Men", "verified_on": "2026-11-20",
                "verified_count": 163, "all_items_same_category_confirmed": True,
                "verified_pool_sha256": ""}]}
        self.persist()

    def persist(self):
        csvwrite(self.pool, ["SKU", "brand", "department", "source_product_type"], self.pool_rows)
        csvwrite(self.selection, ["SKU"], self.selected)
        csvwrite(self.master, ["category_id", "product_type"], self.categories)
        self.pool_hash = hashlib.sha256(self.pool.read_bytes()).hexdigest()
        if not self.config["brand_dept_defaults"][0]["verified_pool_sha256"]:
            self.config["brand_dept_defaults"][0]["verified_pool_sha256"] = self.pool_hash
        self.rules.write_text(json.dumps(self.config), encoding="utf-8")

    def result(self):
        self.persist()
        return p.run(self.pool, self.selection, self.master, self.rules, self.pool_hash)

    def test_exception_and_default_pass_with_route(self):
        rows, receipt = self.result()
        self.assertEqual(receipt["pass_count"], 10)
        self.assertEqual(rows[0]["selected_category_id"], "3320")
        self.assertEqual(rows[0]["category_source"], "exception_map")
        self.assertEqual(rows[1]["category_source"], "brand_dept_default")

    def test_unknown_sku_holds(self):
        self.selected[0] = {"SKU": "NOT-IN-POOL"}
        rows, receipt = self.result()
        self.assertEqual(receipt["hold_count"], 1)
        self.assertEqual(rows[0]["reason"], "unknown_sku")

    def test_type_contradiction_holds(self):
        del self.config["category_overrides_by_sku"]["SP-0"]
        rows, receipt = self.result()
        self.assertEqual(receipt["hold_count"], 1)
        self.assertIn("sandal_slipper_vs_boot_category", rows[0]["reason"])

    def test_stale_default_count_holds(self):
        self.config["brand_dept_defaults"][0]["verified_count"] = 162
        rows, receipt = self.result()
        self.assertEqual(receipt["hold_count"], 9)
        self.assertIn("default_expired_count", rows[1]["reason"])

    def test_wrong_pool_hash_is_fatal(self):
        self.persist()
        with self.assertRaisesRegex(ValueError, "pool sha256 mismatch"):
            p.run(self.pool, self.selection, self.master, self.rules, "0" * 64)

    def test_missing_evidence_holds(self):
        self.config["category_overrides_by_sku"]["SP-0"]["evidence_ref"] = ""
        rows, _ = self.result()
        self.assertIn("missing_category_evidence", rows[0]["reason"])


if __name__ == "__main__":
    unittest.main()

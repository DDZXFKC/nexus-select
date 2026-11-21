"""Independent cross-audit: 158 Shoe Palace Woo/source identities across two snapshots.

Does not compare cached stock or prices and never grants live purchase.
"""
import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NEW = ROOT / "data/xserver-export/sp158-variation-match-result-2026-11-22.csv"
OLD = ROOT / "data/xserver-export/sp158-live-sku-match-2026-11-22.csv"
WOO = ROOT / "data/xserver-export/sp-variation-skus-2026-11-21.csv"


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


class CrossSnapshot(unittest.TestCase):
    def test_independent_1713_source_skus_and_shopify_ids_agree(self):
        latest = read(NEW)
        former = read(OLD)
        woo = read(WOO)
        self.assertEqual(len(latest), 1713)
        self.assertEqual(len(former), 1713)
        self.assertEqual(len(woo), 1713)
        current = {(r["product_id"], r["variation_id"]): r for r in latest}
        prior = {(r["product_id"], r["variation_id"]): r for r in former}
        original = {(r["product_id"], r["variation_id"]): r for r in woo}
        self.assertEqual(len(current), 1713)
        self.assertEqual(len(prior), 1713)
        self.assertEqual(len(original), 1713)
        self.assertEqual(set(current), set(prior))
        self.assertEqual(set(current), set(original))
        for key in original:
            row = current[key]
            earlier = prior[key]
            wc = original[key]
            self.assertEqual(row["match_status"], "PASS", key)
            self.assertEqual(earlier["status"], "PASS", key)
            self.assertEqual(row["variation_sku"], wc["variation_sku"], key)
            self.assertEqual(earlier["woo_variation_sku"], wc["variation_sku"], key)
            self.assertEqual(row["parent_sku"], wc["parent_sku"], key)
            self.assertEqual(earlier["parent_sku"], wc["parent_sku"], key)
            self.assertEqual(row["supplier_product_id"], earlier["supplier_product_id"], key)
            self.assertEqual(row["source_url"], earlier["source_url"], key)
            self.assertEqual(row["supplier_variant_sku"], earlier["shopify_variant_sku_live"], key)
            self.assertEqual(row["supplier_variant_id"], earlier["shopify_variant_id_live"], key)


if __name__ == "__main__":
    unittest.main()

import unittest

from tools.sp158_merge_supplier_evidence import (
    LEGACY, URLS, WOO, read_csv, reconcile
)


class MergeEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.woo = read_csv(WOO)
        cls.urls = read_csv(URLS)
        cls.legacy = read_csv(LEGACY)
        cls.url_map = {r["supplier_product_id"]: r["source_url"] for r in cls.urls}

    def make_live(self, woo=None, supplier_variant_id="987654321"):
        row = woo or self.woo[0]
        supplier_id = row["parent_sku"][3:]
        return {
            "product_id":row["product_id"], "parent_sku":row["parent_sku"],
            "variation_id":row["variation_id"], "variation_sku":row["variation_sku"],
            "supplier_product_id":supplier_id,
            "source_url":self.url_map[supplier_id],
            "supplier_variant_id":supplier_variant_id,
            "supplier_variant_sku":row["variation_sku"],
            "status":"PASS", "reason":"EXACT_INDEPENDENT_SHOPIFY_VARIANT_SKU",
            "source_sha256":"a"*64,
            "observed_at_utc":"2026-11-21T17:50:58+00:00"
        }

    def test_legacy_snapshot_has_expected_full_coverage(self):
        rows, products = reconcile([], self.woo, self.urls, self.legacy)
        self.assertEqual(len(rows), 1713)
        self.assertEqual(len(products), 158)
        self.assertEqual(sum(r["match_status"]=="PASS" for r in rows), 77)

    def test_new_supplier_identity_adds_only_matched_variation(self):
        row = self.make_live()
        merged, _ = reconcile([row], self.woo, self.urls, self.legacy)
        self.assertEqual(sum(r["match_status"]=="PASS" for r in merged), 78)
        exact = next(r for r in merged if r["product_id"]==row["product_id"]
                     and r["variation_id"]==row["variation_id"])
        self.assertEqual(exact["variation_sku"], row["variation_sku"])
        self.assertEqual(exact["supplier_variant_id"], row["supplier_variant_id"])

    def test_existing_reviewed_identity_conflict_fails_closed(self):
        old = self.legacy[0]
        woo = next(r for r in self.woo if r["product_id"]==old["product_id"]
                   and r["variation_id"]==old["variation_id"])
        fresh = self.make_live(woo, "111111")
        merged, _ = reconcile([fresh], self.woo, self.urls, self.legacy)
        conflict = next(r for r in merged if r["product_id"]==old["product_id"]
                        and r["variation_id"]==old["variation_id"])
        self.assertEqual(conflict["match_status"], "HOLD")
        self.assertEqual(conflict["reason_codes"], "CONFLICT_LIVE_VS_LEGACY_SUPPLIER_VARIANT_ID")

    def test_live_url_mismatch_never_promoted(self):
        live = self.make_live()
        live["source_url"] = "https://www.shoepalace.com/products/other-product"
        merged, _ = reconcile([live], self.woo, self.urls, self.legacy)
        self.assertEqual(sum(r["match_status"]=="PASS" for r in merged), 77)

    def test_unknown_woo_variation_rejected(self):
        row = self.make_live()
        row["variation_id"] = "9999999999999"
        with self.assertRaises(ValueError):
            reconcile([row], self.woo, self.urls, self.legacy)

    def test_duplicate_live_record_rejected(self):
        row = self.make_live()
        with self.assertRaises(ValueError):
            reconcile([row, row], self.woo, self.urls, self.legacy)


if __name__ == "__main__":
    unittest.main()

import json
import unittest

from tools.sp158_supplier_variant_probe import probe, robots_allows, valid_url


URL = "https://www.shoepalace.com/products/example-sneaker"
ROWS = [
    {"parent_sku": "SP-123", "variation_id": "11", "variation_sku": "SKU9"},
    {"parent_sku": "SP-123", "variation_id": "12", "variation_sku": "SKU10"},
]
ROBOTS = b"User-agent: *\nAllow: /\n"
BLOCK = b"User-agent: *\nDisallow: /products/\n"


class SPVariantProbeTests(unittest.TestCase):
    def test_exact_sku_and_product_id(self):
        body = json.dumps({"id": 123, "variants": [
            {"id": 900, "sku": "SKU9", "available": True, "price": 100},
            {"id": 901, "sku": "SKU10", "available": False, "price": 1}
        ]}).encode()
        rows = probe("10", URL, ROWS, getter=lambda _: body, robots_body=ROBOTS)
        self.assertEqual([r["status"] for r in rows], ["PASS", "PASS"])
        self.assertEqual([r["supplier_variant_id"] for r in rows], ["900", "901"])
        self.assertNotIn("stock", rows[0])
        self.assertNotIn("price", rows[0])

    def test_mismatch_product_id_fails_closed(self):
        body = json.dumps({"id": 124, "variants": [{"id": 900, "sku": "SKU9"}]}).encode()
        rows = probe("10", URL, ROWS, getter=lambda _: body, robots_body=ROBOTS)
        self.assertTrue(all(r["reason"] == "SUPPLIER_PRODUCT_ID_MISMATCH" for r in rows))

    def test_ambiguous_supplier_sku_not_accepted(self):
        body = json.dumps({"id": 123, "variants": [
            {"id": 900, "sku": "SKU9"}, {"id": 901, "sku": "SKU9"}
        ]}).encode()
        rows = probe("10", URL, ROWS, getter=lambda _: body, robots_body=ROBOTS)
        self.assertEqual(rows[0]["reason"], "SUPPLIER_SKU_AMBIGUOUS")
        self.assertEqual(rows[1]["reason"], "SUPPLIER_SKU_MISSING")

    def test_robots_disallow_zero_merchant_requests(self):
        calls = []
        rows = probe("10", URL, ROWS,
                     getter=lambda url: calls.append(url) or b"{}", robots_body=BLOCK)
        self.assertEqual(calls, [])
        self.assertEqual(rows[0]["reason"], "ROBOTS_NOT_VERIFIED")

    def test_missing_robots_prohibits_live_request(self):
        rows = probe("10", URL, ROWS, getter=lambda _: self.fail("must not fetch"))
        self.assertEqual(rows[0]["reason"], "ROBOTS_NOT_VERIFIED")

    def test_invalid_supplier_url_rejected(self):
        self.assertFalse(valid_url("https://www.shoepalace.com.evil.invalid/products/a"))
        self.assertFalse(valid_url(URL + "?variant=999"))
        self.assertFalse(valid_url("http://www.shoepalace.com/products/a"))

    def test_http_429_quarantine(self):
        from urllib.error import HTTPError
        def blocked(_):
            raise HTTPError(URL, 429, "rate limited", {}, None)
        rows = probe("10", URL, ROWS, getter=blocked, robots_body=ROBOTS)
        self.assertEqual(rows[0]["reason"], "HTTP_429")
        self.assertEqual(rows[0]["status"], "HOLD")


if __name__ == "__main__":
    unittest.main()

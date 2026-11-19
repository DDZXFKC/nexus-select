"""Executable fixture IDs for GLM 6-condition cross-shop review.

python3 -m unittest discover -s tests -p 'test_cross_shop_offer_contract.py' -v
"""
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "cross_shop_offer_contract",
    Path(__file__).resolve().parents[1] / "tools" / "cross_shop_offer_contract.py")
offer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(offer)

ALIASES = {"nike": "NIKE", "nike®": "NIKE", "ナイキ": "NIKE",
           "converse": "CONVERSE"}
BASE = {"source_product_id": "xyz", "source_variant_id": "v01",
        "brand_raw": "ＮＩＫＥ", "model_code_full_raw": "ＡＢ－００７/ｂ",
        "color_code_raw": "007/B", "currency": "USD", "item_price_local": "100.00",
        "source_url": "https://example.org/p", "stock_observed": "0"}


class CrossShopOfferContractTests(unittest.TestCase):
    def test_C5_SP_RAW_OFFER_ROUNDTRIP(self):
        original = dict(BASE)
        result = offer.encode_offer("SP", original, ALIASES)
        self.assertEqual(offer.decode_offer(result), original)
        self.assertEqual(result["model_code_full_norm"], "AB-007/B")
        self.assertEqual(result["color_code_raw"], "007/B")

    def test_C5_FL_RAW_OFFER_ROUNDTRIP(self):
        original = dict(BASE, source_product_id="fl-198", brand_raw="Nike®",
                        currency="EUR", item_price_local="109.99",
                        stock_observed="UNKNOWN")
        result = offer.encode_offer("FL", original, ALIASES)
        self.assertEqual(offer.decode_offer(result), original)
        self.assertEqual(result["brand_norm"], "NIKE")

    def test_C5_BRAND_ALIAS_AND_FULLWIDTH(self):
        self.assertEqual(offer.brand_normalize("ＮＩＫＥ", ALIASES), "NIKE")
        self.assertEqual(offer.brand_normalize(" Nike® ", ALIASES), "NIKE")
        self.assertEqual(offer.model_normalize("ＡＢ－００７/ｂ"), "AB-007/B")

    def test_C5_MODEL_LEADING_ZERO_AND_SEPARATOR_NOT_COLLAPSED(self):
        self.assertNotEqual(offer.model_normalize("AB-007/B"),
                            offer.model_normalize("AB-7/B"))
        self.assertNotEqual(offer.model_normalize("AB-007/B"),
                            offer.model_normalize("AB/007/B"))
        self.assertEqual(offer.model_normalize("ab-007/b"), "AB-007/B")

    def test_C5_UNKNOWN_ALIAS_HOLD(self):
        with self.assertRaisesRegex(ValueError, "unknown brand alias"):
            offer.brand_normalize("unmapped", ALIASES)

    def test_C5_RAW_TAMPERING_DETECTED(self):
        encoded = offer.encode_offer("SP", BASE, ALIASES)
        encoded["raw_row_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            offer.decode_offer(encoded)

    def test_C5_DUPLICATE_SHOP_KEY_REJECTED(self):
        first = offer.encode_offer("SP", BASE, ALIASES)
        second = offer.encode_offer("SP", dict(BASE, source_product_id="xyz2"), ALIASES)
        with self.assertRaisesRegex(ValueError, "duplicate shop colorway"):
            offer.uniqueness_audit([first, second])

    def test_C6_STABLE_ID_UNAMBIGUOUS(self):
        self.assertNotEqual(offer.stable_id("SP", "a|b", "c"),
                            offer.stable_id("SP", "a", "b|c"))
        self.assertEqual(offer.stable_id("SP", "xyz", "v01"),
                         offer.stable_id("SP", "xyz", "v01"))

    def test_C5_SP_FL_SAME_COLORWAY_ALLOWED(self):
        sp = offer.encode_offer("SP", BASE, ALIASES)
        fl = offer.encode_offer("FL", dict(BASE, source_product_id="fl2"), ALIASES)
        self.assertTrue(offer.uniqueness_audit([sp, fl]))


if __name__ == "__main__":
    unittest.main()

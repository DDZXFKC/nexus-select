"""P0-finalization §6.1 strict manifest normalization gate tests."""
import importlib.util
import unittest
from pathlib import Path

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("corr_adapter_parity", root / "tools/cross_shop_corr_adapter.py")
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


def row(shop="SP", product="p-001", style="1155130", color="BBLC"):
    return {
        "source_row_id": shop + "-" + product + "-US9",
        "shop_code": shop, "source_product_id": product,
        "source_variant_id": "US9", "brand_raw": "HOKA",
        "model_code_full_raw": style + "-" + color, "color_code_raw": color,
        "source_url": "https://example.org/sku",
        "currency": "USD", "item_price_local": "100.00",
        "stock_observed": "IN_STOCK",
        "corr_code": "130BBLC" if shop == "FL" else "",
        "corr_style": style if shop == "SP" else "",
        "corr_color": color if shop == "SP" else "",
        "sellable": "1", "name": "Bondi 7",
        "cost_calculated": "1", "cost_verified": "1",
        "procurement_total_jpy": "20000",
        "procurement_unit": "COLORWAY_ONE_UNIT",
        "official_price_current": "", "official_price_usd": "",
    }


def adapt_for(shop="SP", product="p-001"):
    item = row(shop, product)
    sp, fl, manifest = adapter.adapt(list(item), [item])
    out, fields = (sp, adapter.SP_HEADER) if shop == "SP" else (fl, adapter.FL_HEADER)
    return out, fields, manifest


class ParityManifestTests(unittest.TestCase):
    def test_semantic_parity_with_raw_reference_product_id_SP_FL(self):
        for shop in ("SP", "FL"):
            with self.subTest(shop=shop):
                out, fields, manifest = adapt_for(shop, "id|:7")
                reference = [dict(out[0], source_id="id|:7")]
                got = adapter.compare_reference(out, reference, fields, manifest, shop)
                self.assertTrue(got["pass"], got)
                self.assertEqual(got["normalization"], "MANIFEST_SHOP_PRODUCT_V1")
                self.assertEqual([got[k] for k in ("missing", "extra", "differing", "invalid_ids")],
                                 [[], [], [], []])
                self.assertEqual(out[0]["source_id"], manifest[0]["source_id"])

    def test_no_manifest_or_missing_mapping_explicit_fail(self):
        out, fields, manifest = adapt_for()
        reference = [dict(out[0], source_id="p-001")]
        with self.assertRaisesRegex(ValueError, "manifest"):
            adapter.compare_reference(out, reference, fields, None, "SP")
        got = adapter.compare_reference(out, reference, fields, [], "SP")
        self.assertFalse(got["pass"])
        self.assertEqual(len(got["invalid_ids"]), 1)
        self.assertIn(out[0]["source_id"], str(got["invalid_ids"]))

    def test_corrupted_manifest_source_id_fails_with_ID(self):
        out, fields, manifest = adapt_for()
        broken = [dict(manifest[0], source_id="7:INVALID")]
        ref = [dict(out[0], source_id="p-001")]
        got = adapter.compare_reference(out, ref, fields, broken, "SP")
        self.assertFalse(got["pass"])
        self.assertIn("7:INVALID", str(got["invalid_ids"]))

    def test_manifest_raw_row_tampering_fail(self):
        out, fields, manifest = adapt_for()
        broken = [dict(manifest[0], rows_sha256=["0" * 64])]
        got = adapter.compare_reference(out, [dict(out[0], source_id="p-001")],
                                        fields, broken, "SP")
        self.assertFalse(got["pass"])
        self.assertIn(out[0]["source_id"], str(got["invalid_ids"]))

    def test_multi_colorway_collapse_into_same_product_fails(self):
        a, fields, m1 = adapt_for("SP", "same")
        b = row("SP", "same", "1155131", "CCZ")
        sp2, _, m2 = adapter.adapt(list(b), [b])
        got = adapter.compare_reference(a + sp2,
              [dict(a[0], source_id="same"), dict(sp2[0], source_id="same")],
              fields, m1 + m2, "SP")
        self.assertFalse(got["pass"])
        self.assertTrue(any("many-to-one" in v["reason"] for v in got["invalid_ids"]))

    def test_other_fields_are_never_exempt_from_parity(self):
        out, fields, manifest = adapt_for()
        reference = [dict(out[0], source_id="p-001", sellable="0")]
        got = adapter.compare_reference(out, reference, fields, manifest, "SP")
        self.assertFalse(got["pass"])
        self.assertEqual(len(got["differing"]), 1)
        self.assertEqual(got["missing"], [])
        self.assertEqual(got["extra"], [])

    def test_deterministic_normalized_collision_in_reference_fails(self):
        out, fields, manifest = adapt_for()
        reference = [dict(out[0], source_id="p-001"),
                     dict(out[0], source_id="p-001")]
        got = adapter.compare_reference(out, reference, fields, manifest, "SP")
        self.assertFalse(got["pass"])
        self.assertTrue(any("collision" in v["reason"] for v in got["invalid_ids"]))

    def test_adapter_manifest_complete_roundtrip(self):
        a = row("SP", "model-x")
        b = dict(a, source_row_id="SP-model-x-US10",
                 source_variant_id="US10", stock_observed="OUT_OF_STOCK",
                 item_price_local="130.00")
        sp, fl, manifest = adapter.adapt(list(a), [a, b])
        self.assertEqual(len(sp), 1)
        self.assertEqual(adapter.restore(manifest), [a, b])
        ref = [dict(sp[0], source_id="model-x")]
        self.assertTrue(adapter.compare_reference(sp, ref, adapter.SP_HEADER,
                                                  manifest, "SP")["pass"])


if __name__ == "__main__":
    unittest.main()

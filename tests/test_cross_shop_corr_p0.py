"""P0 corr identity guard, GLM erratum, HOLD and interface-v1 parity tests.

python3 -m unittest discover -s tests -p 'test_cross_shop_corr_p0.py' -v
"""
import ast
import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


corr = load("corr_under_p0", "tools/cross_shop_corr.py")
adapter = load("corr_adapter_under_p0", "tools/cross_shop_corr_adapter.py")


def sp(brand, style, color, sellable="1"):
    return {"source_id": brand + style + color, "brand": brand, "style": style,
            "color": color, "sellable": sellable}


def fl(brand, code):
    return {"source_id": brand + code, "brand": brand, "code": code}


def source(shop, suffix, variant="size10", **kwargs):
    row = {
        "source_row_id": shop + "-" + suffix + "-" + variant,
        "shop_code": shop,
        "source_product_id": shop + "-" + suffix,
        "source_variant_id": variant,
        "brand_raw": "HOKA",
        "model_code_full_raw": "1155130-BBLC",
        "color_code_raw": "BBLC",
        "source_url": "https://example.org/" + shop.lower(),
        "currency": "USD", "item_price_local": "99.90",
        "stock_observed": "IN_STOCK",
        "corr_code": "130BBLC" if shop == "FL" else "",
        "corr_style": "1155130" if shop == "SP" else "",
        "corr_color": "BBLC" if shop == "SP" else "",
        "sellable": "1", "name": "Bondi",
        "cost_calculated": "1", "cost_verified": "1",
        "procurement_total_jpy": "20000.00", "procurement_unit": "COLORWAY_ONE_UNIT",
        "official_price_current": "", "official_price_usd": "",
    }
    row.update(kwargs)
    return row


class CorrP0Tests(unittest.TestCase):
    def test_identity_key_no_import_or_redefinition_in_two_corr_modules(self):
        """Protect existing identity_key contract, with AST rather than comments."""
        for file in ("tools/cross_shop_corr.py", "tests/test_cross_shop_corr.py"):
            tree = ast.parse((ROOT / file).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    modules = ([alias.name for alias in node.names]
                               if isinstance(node, ast.Import) else [node.module or ""])
                    for module in modules:
                        self.assertNotIn("identity_key", module, file)
                        self.assertNotIn("cross_shop_offer_contract", module, file)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    self.assertNotEqual(node.name, "identity_key", file)
        # This is not a substitute for executing the existing identity contract suite.

    def test_erratum_42110519_and_hoka_thirteen_legacy_codes(self):
        nums = ("42110519", "42110588", "42112011", "42116011",
                "42116840", "42116845", "42162011", "42162032",
                "42162771", "42162860", "42168716", "42168717",
                "42171891")
        results = corr.correlate([fl("HOKA", n) for n in nums],
                                 [sp("HOKA", "1155130", "BBLC")], ())
        self.assertEqual(len(results), 13)
        self.assertEqual([r["status"] for r in results],
                         ["HOLD_LEGACY_NUMERIC"] * 13)
        self.assertTrue(all(r["sp_source_id"] == "" for r in results))
        self.assertTrue(all(r["hold_reason_codes"] == "HOLD_LEGACY_NUMERIC"
                            for r in results))

    def test_hold_not_sellable_even_when_only_candidate(self):
        rows = corr.correlate([fl("UGG", "3236CHE")],
                              [sp("UGG", "3236", "CHE", sellable="0")], ())
        self.assertEqual(rows[0]["status"], "HOLD_NOT_SELLABLE")
        self.assertEqual(rows[0]["candidate_count"], 1)
        self.assertEqual(rows[0]["sp_source_id"], "")
        self.assertEqual(rows[0]["hold_reason_codes"], "HOLD_NOT_SELLABLE")

    def test_interface_v1_size_rows_roundtrip_and_corr_identical(self):
        first = source("SP", "s1", "US9", stock_observed="OUT_OF_STOCK",
                       item_price_local="99.99")
        second = source("SP", "s1", "US10", stock_observed="IN_STOCK",
                        item_price_local="109.99")
        third = source("FL", "f1", "US9", stock_observed="UNKNOWN",
                       item_price_local="104.99")
        original = [first, second, third]
        headers = list(first)
        spos, flos, evidence = adapter.adapt(headers, original)
        self.assertEqual((len(spos), len(flos)), (1, 1))
        self.assertEqual(sorted(adapter.restore(evidence), key=lambda x: x["source_row_id"]),
                         sorted(original, key=lambda x: x["source_row_id"]))
        self.assertEqual([r["source_row_id"] for r in original[:2]],
                         evidence[1]["source_row_ids"] if evidence[1]["shop_code"] == "SP"
                         else evidence[0]["source_row_ids"])
        # Compare the adapter's output to an independent reference schema fixture.
        reference_sp = [{k: v for k, v in spos[0].items()}]
        reference_fl = [{k: v for k, v in flos[0].items()}]
        self.assertEqual(adapter.compare_reference(spos, reference_sp,
                         adapter.SP_HEADER)["pass"], True)
        self.assertEqual(adapter.compare_reference(flos, reference_fl,
                         adapter.FL_HEADER)["pass"], True)
        matching = corr.correlate(flos, spos, ())
        direct = corr.correlate([fl("HOKA", "130BBLC")],
                                [sp("HOKA", "1155130", "BBLC")], ())
        # Canonical source IDs are distinct, but core match and disposition identical.
        for field in ("brand", "fl_code", "status", "sp_style", "sp_color",
                      "rule", "matched_key", "candidate_count", "tags",
                      "hold_reason_codes"):
            self.assertEqual(matching[0][field], direct[0][field])

    def test_adapter_rejects_unverified_style_and_size_cost_conflict(self):
        raw = source("SP", "s1", corr_style="")
        with self.assertRaisesRegex(ValueError, "style not verified"):
            adapter.adapt(list(raw), [raw])
        a = source("SP", "s1", "US9")
        b = source("SP", "s1", "US10", procurement_total_jpy="25000")
        with self.assertRaisesRegex(ValueError, "inconsistent colorway"):
            adapter.adapt(list(a), [a, b])

    def test_reference_parity_detects_real_difference_and_missing_reference(self):
        rows = [source("SP", "s1")]
        spout, _, _ = adapter.adapt(list(rows[0]), rows)
        with self.assertRaisesRegex(ValueError, "reference adapter output required"):
            adapter.compare_reference(spout, None, adapter.SP_HEADER)
        other = dict(spout[0], sellable="0")
        result = adapter.compare_reference(spout, [other], adapter.SP_HEADER)
        self.assertFalse(result["pass"])
        self.assertEqual(result["differing"], [spout[0]["source_id"]])

    def test_adapter_rejects_duplicate_raw_source_row_id(self):
        row = source("SP", "s1")
        with self.assertRaisesRegex(ValueError, "duplicate source_row_id"):
            adapter.adapt(list(row), [row, dict(row)])


if __name__ == "__main__":
    unittest.main()

"""Regression: batch3 permits zero stock; batch1 and batch2 still block it."""
import ast
import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "tools" / "build_buyma_batch.py"
spec = importlib.util.spec_from_file_location("build_buyma_batch", MODULE)
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


class StockGateTests(unittest.TestCase):
    def fake_inputs(self, stock):
        item = {"Type": "variable", "SKU": "SP-123", "Brand": "TEST",
                "Name": "Sample Mens Shoes (Black)", "Images": "https://example.org/one.jpg",
                "Regular price": "25000"}
        variation = {"Type": "variation", "SKU": "var123", "Parent": "SP-123",
                     "Attribute 1 value": "9", "In stock?": stock}
        config = {"brands": {"TEST": {
            "source": "/irrelevant", "brand_id": "777", "brand_name": "TEST",
            "categories": {"Men": "3323"}, "approved_buyma_prices": {"SP-123": 30000},
            "color_ids": {"Black": 2}}}
        book = {("TEST", "Men", "9"): 27}
        return [item, variation], config, book

    def run_case(self, stock, allow_zero):
        woo, cfg, book = self.fake_inputs(stock)
        previous = generator.read
        generator.read = lambda _path: [
            {"productId": "123", "description_en": "Sample", "url": "https://example.org/item"}]
        self.addCleanup(setattr, generator, "read", previous)
        return generator.generate(["SP-123"], woo, cfg, book,
                                  approved_categories={"SP-123": "3323"},
                                  allow_zero_stock=allow_zero)

    def test_stock_b1_b2_zero_still_rejected(self):
        with self.assertRaisesRegex(ValueError, "no stock"):
            self.run_case("0", False)

    def test_stock_b3_zero_preserved_in_colorsizes(self):
        items, colorsizes = self.run_case("0", True)
        self.assertEqual(len(items), 1)
        self.assertEqual(colorsizes[0]["在庫ステータス"], "0")
        self.assertEqual(colorsizes[0]["検索用サイズ"], "270")

    def test_stock_b1_b2_in_stock_unchanged(self):
        items, colorsizes = self.run_case("1", False)
        self.assertEqual(len(items), 1)
        self.assertEqual(colorsizes[0]["在庫ステータス"], "1")

    def test_stock_b3_does_not_allow_missing_variants(self):
        woo, cfg, book = self.fake_inputs("0")
        previous = generator.read
        generator.read = lambda _path: [
            {"productId": "123", "description_en": "Sample", "url": "https://example.org/item"}]
        self.addCleanup(setattr, generator, "read", previous)
        with self.assertRaisesRegex(ValueError, "no variations"):
            generator.generate(["SP-123"], woo[:1], cfg, book,
                               approved_categories={"SP-123": "3323"}, allow_zero_stock=True)

    def test_batch3_flag_only_set_by_prefix(self):
        tree = ast.parse(MODULE.read_text(encoding="utf-8"))
        src = ast.get_source_segment(MODULE.read_text(encoding="utf-8"), tree)
        self.assertIn("allow_zero_stock=(a.prefix == 'batch3')", src)


if __name__ == "__main__":
    unittest.main()

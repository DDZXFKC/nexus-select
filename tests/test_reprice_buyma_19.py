"""Synthetic regression tests for provisional 19% BUYMA repricer.

python3 -m unittest discover -s tests -p 'test_reprice_buyma_19.py' -v
"""
import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "tools" / "reprice_buyma_19.py"
spec = importlib.util.spec_from_file_location("reprice_buyma_19", SOURCE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def write(path, head, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=head)
        writer.writeheader()
        writer.writerows(rows)


class RepricingTests(unittest.TestCase):
    def test_old_and_new_prices_from_unrounded_cost(self):
        self.assertEqual(mod.price("165.0", mod.OLD_DIVISOR)[0], 40800)
        self.assertEqual(mod.price("165.0", mod.NEW_DIVISOR)[0], 40300)
        self.assertEqual(mod.price("12.5", mod.OLD_DIVISOR)[0], 7800)
        self.assertEqual(mod.price("12.5", mod.NEW_DIVISOR)[0], 7700)

    def test_half_even_old_cost_remains_unchanged(self):
        _, cost = mod.price("12.5")
        self.assertEqual(round(float(cost)), 5774)

    def test_negative_zero_invalid(self):
        for usd in ("0", "-1", "NaN", "Infinity", ""):
            with self.subTest(usd=usd):
                with self.assertRaises(Exception):
                    mod.price(usd)

    def test_margin_and_linked_repricing_do_not_mutate_source(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            margin = folder / "old_margin.csv"
            item = folder / "old_items.csv"
            output = folder / "new_margin.csv"
            output_items = folder / "new_items.csv"
            head = ["sku", "usd", "cost_jpy", "price_jpy", "formula_price_jpy",
                    "price_match", "gross_profit_jpy", "margin_pct"]
            write(margin, head, [{
                "sku": "SP-1", "usd": "165.0", "cost_jpy": "30351",
                "price_jpy": "40800", "formula_price_jpy": "40800",
                "price_match": "yes", "gross_profit_jpy": "10449", "margin_pct": "25.6"}])
            write(item, ["商品管理番号", "単価", "カテゴリ"], [
                {"商品管理番号": "SP-1", "単価": "40800", "カテゴリ": "3321"}])
            original_margin, original_items = margin.read_bytes(), item.read_bytes()
            evidence = mod.reprice_margin(margin, output)
            self.assertEqual(len(evidence), 1)
            mapping, _ = mod.mapping_from_margin(margin)
            result = mod.reprice_linked(item, output_items, mapping, "商品管理番号", "単価")
            self.assertEqual(result["repriced"], 1)
            _, rows = mod.read(output_items)
            self.assertEqual(rows[0]["単価"], "40300")
            self.assertEqual(rows[0]["カテゴリ"], "3321")
            self.assertEqual(margin.read_bytes(), original_margin)
            self.assertEqual(item.read_bytes(), original_items)

    def test_missing_cost_guard_and_exclusion_option(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            src = folder / "list.csv"
            write(src, ["sku", "price_jpy"], [
                {"sku": "FL-1", "price_jpy": "40800"},
                {"sku": "FL-HOLD", "price_jpy": "0"}])
            mapping = {"FL-1": (40800, 40300)}
            with self.assertRaisesRegex(ValueError, "no approved cost"):
                mod.reprice_linked(src, folder / "should_not_exist.csv", mapping,
                                   "sku", "price_jpy")
            report = mod.reprice_linked(src, folder / "new.csv", mapping,
                                        "sku", "price_jpy", True)
            self.assertEqual(report["repriced"], 1)
            self.assertEqual(report["unmapped_skus"], ["FL-HOLD"])
            _, rows = mod.read(folder / "new.csv")
            self.assertEqual(rows[1]["price_jpy"], "0")


if __name__ == "__main__":
    unittest.main()

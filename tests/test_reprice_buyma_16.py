"""Tests for owner 16% repricing from verified 19% snapshots."""
import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "tools" / "reprice_buyma_16.py"
spec = importlib.util.spec_from_file_location("reprice_buyma_16", SOURCE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def write(path, columns, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        w = csv.DictWriter(file, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)

class Reprice16Tests(unittest.TestCase):
    def test_16_formula_from_unrounded_cost(self):
        self.assertEqual(mod.price("165", mod.OLD_DIVISOR)[0], 40300)
        self.assertEqual(mod.price("165", mod.NEW_DIVISOR)[0], 38700)
        self.assertEqual(mod.price("12.5", mod.OLD_DIVISOR)[0], 7700)
        self.assertEqual(mod.price("12.5", mod.NEW_DIVISOR)[0], 7400)

    def test_cost_round_half_even_unchanged(self):
        _, exact = mod.price("12.5")
        self.assertEqual(round(float(exact)), 5774)

    def test_invalid_cost_cannot_reprice(self):
        for value in ("", "0", "-1", "NaN", "Infinity"):
            with self.subTest(value=value):
                with self.assertRaises(Exception):
                    mod.price(value)

    def test_margin_linked_and_source_immutable(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            old = folder / "old.csv"
            linked = folder / "linked.csv"
            head = ["sku","usd","cost_jpy","price_jpy","formula_price_jpy",
                    "price_match","gross_profit_jpy","margin_pct"]
            write(old,head,[{"sku":"SP-1","usd":"165","cost_jpy":"30351",
                             "price_jpy":"40300","formula_price_jpy":"40300",
                             "price_match":"yes","gross_profit_jpy":"9949","margin_pct":"24.7"}])
            write(linked,["商品管理番号","単価","カテゴリ"],
                  [{"商品管理番号":"SP-1","単価":"40300","カテゴリ":"3321"}])
            before_old = old.read_bytes()
            before_linked = linked.read_bytes()
            audit = mod.reprice_margin(old, folder / "new-margin.csv")
            self.assertEqual(audit[0]["price_19_jpy"] if "price_19_jpy" in audit[0]
                             else audit[0]["price_old_jpy"],40300)
            mapping,_ = mod.mapping_from_margin(old)
            result = mod.reprice_linked(linked,folder / "new-linked.csv",
                                        mapping,"商品管理番号","単価")
            self.assertEqual(result["repriced"],1)
            _, rows = mod.read(folder / "new-linked.csv")
            self.assertEqual(rows[0]["単価"],"38700")
            self.assertEqual(rows[0]["カテゴリ"],"3321")
            self.assertEqual(old.read_bytes(),before_old)
            self.assertEqual(linked.read_bytes(),before_linked)

    def test_unmapped_is_hold_not_zero_cost(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            file = folder / "listing.csv"
            write(file,["sku","price_jpy"],[{"sku":"SP-UNVERIFIED","price_jpy":"0"}])
            with self.assertRaisesRegex(ValueError,"no approved cost"):
                mod.reprice_linked(file,folder / "out.csv",{},"sku","price_jpy")

if __name__ == "__main__":
    unittest.main()

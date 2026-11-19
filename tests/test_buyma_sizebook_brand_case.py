"""Regression for case-normalized brand lookup into A2-sizebook.

Run: python3 -m unittest discover -s tests -p 'test_buyma_sizebook_brand_case.py' -v
"""
import importlib.util
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "tools" / "build_buyma_batch.py"
spec = importlib.util.spec_from_file_location("build_buyma_size_test", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SizeBookBrandCaseTest(unittest.TestCase):
    def test_vans_mixed_case_joins_uppercase_chart(self):
        with tempfile.TemporaryDirectory() as directory:
            table = Path(directory) / "sizes.csv"
            table.write_text(
                "brand,department,size_original,cm\n"
                "VANS,Men,3.5,21.5\n"
                "VANS,Men,13.5,31.5\n", encoding="utf-8")
            book = module.sizebook(table)
            self.assertEqual(book[("VANS", "Men", "3.5")], module.Decimal("21.5"))
            self.assertEqual(book[("VANS", "Men", "13.5")], module.Decimal("31.5"))
            sku = "SP-456"
            parent = {"Type": "variable", "SKU": sku, "Brand": "Vans",
                      "Name": "Example Mens Shoes (Black)",
                      "Images": "https://example.test/1.jpg", "Regular price": "30000"}
            variants = [{"Type": "variation", "Parent": sku,
                         "Attribute 1 value": size, "In stock?": "0"}
                        for size in ("3.5", "13.5")]
            cfg = {"brands": {"Vans": {
                "source": "/synthetic/source.csv", "brand_id": "123", "brand_name": "Vans",
                "categories": {"Men": "999"}, "approved_buyma_prices": {sku: "40000"},
                "color_ids": {"Black": "2"}}}}
            original_read = module.read
            module.read = lambda path: [{"productId": "456", "description_en": "Example",
                                         "url": "https://example.test/item"}]
            try:
                items, colors = module.generate(
                    [sku], [parent] + variants, cfg, book,
                    approved_categories={sku: "999"}, allow_zero_stock=True)
            finally:
                module.read = original_read
            self.assertEqual(len(items), 1)
            self.assertEqual(len(colors), 2)
            self.assertEqual([row["検索用サイズ"] for row in colors], ["215", "315"])
            self.assertEqual([row["在庫ステータス"] for row in colors], ["0", "0"])
            self.assertEqual(items[0]["ブランド名"], "Vans")

    def test_hoka_ugg_existing_uppercase_remains_compatible(self):
        with tempfile.TemporaryDirectory() as directory:
            table = Path(directory) / "sizes.csv"
            table.write_text(
                "brand,department,size_original,cm\n"
                "HOKA,Men,9,27\nUGG,Women,7,24\n", encoding="utf-8")
            book = module.sizebook(table)
            for brand, department, size, expected in (
                    ("HOKA", "Men", "9", "27"), ("UGG", "Women", "7", "24")):
                self.assertEqual(book.get((brand.upper(), department, size)),
                                 module.Decimal(expected))

    def test_missing_chart_still_holds(self):
        self.assertIsNone({("VANS", "Men", "3.5"): 21.5}.get(("VANS", "Men", "14.5")))


if __name__ == "__main__":
    unittest.main()

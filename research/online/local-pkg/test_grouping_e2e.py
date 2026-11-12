import csv, json, tempfile, unittest
from pathlib import Path
import merchant_to_channels

PKG = Path(__file__).parent
URLS = {
 'https://www.bstn.com/eu_en/p/adidas-adilette-280647-0009238',
 'https://www.notre-shop.com/products/j-balvin-air-jordan-4-retro-sneaker-in-lemonade-lemonade',
 'https://www.notre-shop.com/products/novalis-gel-teremoa-ii-sneaker-in-dark-gull-grey-black',
 'https://patta.nl/products/patta-leather-hooded-bomber-jacket-moonless-night',
 'https://patta.nl/products/patta-square-quilted-puffer-jacket-black',
}

class GroupingEndToEnd(unittest.TestCase):
    def test_five_pages_group_to_five_products(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            res = merchant_to_channels.run(PKG / 'input_pages_multi' / 'manifest.csv', td / 't.sqlite', td / 'out')
            self.assertEqual(res['parsed_size_rows'], 51)
            self.assertEqual(res['products'], 5)
            self.assertEqual(res['published'], 0)
            self.assertEqual(res['buyma_rows'], 5)
            rep = json.loads((td / 'out' / 'channel_report_v4.json').read_text(encoding='utf-8'))
            per_url = {}
            for item in rep['review']:
                per_url[item['source_url']] = per_url.get(item['source_url'], 0) + 1
            self.assertEqual(set(per_url), URLS)
            self.assertTrue(all(v == 1 for v in per_url.values()))
            with (td / 'out' / 'extracted_evidence.csv').open(encoding='utf-8-sig', newline='') as f:
                rows = list(csv.DictReader(f))
            self.assertIn('product_id', rows[0])
            by_url = {}
            for r in rows:
                by_url.setdefault(r['product_url'], set()).add(r['product_id'])
                if 'notre-shop' in r['product_url']:
                    self.assertTrue(r['name'].strip())
            for url, ids in by_url.items():
                if 'notre-shop' in url or 'patta' in url:
                    self.assertEqual(len(ids), 1)
                    self.assertTrue(next(iter(ids)))

if __name__ == '__main__':
    unittest.main()

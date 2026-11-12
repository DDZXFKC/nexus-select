import csv
import tempfile
import unittest
from pathlib import Path
from verify_six_pages import prepare

class ManifestTests(unittest.TestCase):
    def test_merge_and_reject_reuse(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = []
            for host in ['www.bstn.com', 'www.notre-shop.com', 'patta.nl']:
                for index in range(2):
                    name = '%s-%s.html' % (host, index)
                    (root / name).write_text('<html></html>')
                    rows.append({'html_file': name, 'product_url': 'https://%s/products/%s' % (host, index)})
            def write(name, values):
                with (root / name).open('w', newline='') as f:
                    w = csv.DictWriter(f, fieldnames=['html_file', 'product_url'])
                    w.writeheader(); w.writerows(values)
            write('five.csv', rows[:-1])
            write('extra.csv', [rows[0], rows[-1]])
            with self.assertRaises(ValueError):
                prepare([root / 'five.csv'], root / 'invalid.csv')
            merged = root / 'six.csv'
            self.assertEqual(len(prepare([root / 'five.csv', root / 'extra.csv'], merged)), 6)
            with self.assertRaises(ValueError):
                prepare([root / 'five.csv', root / 'extra.csv'], merged)
            write('conflict.csv', [dict(rows[0], html_file=rows[1]['html_file'])])
            with self.assertRaises(ValueError):
                prepare([root / 'five.csv', root / 'extra.csv', root / 'conflict.csv'], root / 'conflict-out.csv')

if __name__ == '__main__':
    unittest.main()

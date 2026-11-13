import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path
from bstn_integration import import_csv

class EvidenceTest(unittest.TestCase):
    def test_missing_color_retained_and_refresh_resets(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'rows.csv'
            with p.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=['product_url','sku','size','brand','name','color','price','currency','availability_claim','observed_utc'])
                w.writeheader()
                w.writerow(dict(product_url='https://www.bstn.com/eu_en/p/test',sku='0009238',size='37 EU',brand='Adidas',name='Slides',color='',price='27.99',currency='EUR',availability_claim='InStock',observed_utc='2026-11-12T00:00:00Z'))
            c=sqlite3.connect(':memory:')
            self.assertEqual(import_csv(c,p)['staged'],1)
            self.assertEqual(c.execute('SELECT color_claim,manufacturer_sku,verification_state,decision FROM merchant_evidence').fetchone(),('','','UNVERIFIED','HOLD'))
            c.execute("UPDATE merchant_evidence SET manufacturer_sku='MANUAL',verification_state='MANUALLY_VERIFIED'")
            import_csv(c,p)
            self.assertEqual(c.execute('SELECT manufacturer_sku,verification_state FROM merchant_evidence').fetchone(),('','UNVERIFIED'))
    def test_other_host_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'rows.csv'
            p.write_text('product_url,sku,size,brand,price,currency,observed_utc\nhttps://evil.example/p,1,42,A,1,EUR,now\n')
            c=sqlite3.connect(':memory:')
            self.assertEqual(import_csv(c,p)['rejected'],1)

import csv,sqlite3,tempfile,unittest
from pathlib import Path
from bstn_integration import CREATE
from production_pipeline import EXT
from channel_ready_v4 import export
class TestV4(unittest.TestCase):
 def test_realistic_sizes_and_separate_merchants(self):
  with tempfile.TemporaryDirectory() as d:
   db=Path(d)/'x.db';c=sqlite3.connect(db);c.execute(CREATE);c.execute(EXT)
   for shop in ['one.example','two.example']:
    for size in ['38','39']:
     c.execute('INSERT INTO merchant_evidence VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(f'https://{shop}/shoe','shop-sku',size,'Nike','Runner','Black','99','EUR','InStock','2026-11-12','ABC','','UNVERIFIED','HOLD'))
   c.commit();c.close();r=export(db,Path(d)/'out')
   self.assertEqual((r['input_size_rows'],r['products'],r['woocommerce_rows'],r['buyma_rows'],r['published']),(4,2,6,2,0))
   with (Path(d)/'out'/'woocommerce_review_v4.csv').open(encoding='utf-8-sig') as f:
    rows=list(csv.DictReader(f));self.assertEqual(sum(x['Type']=='variable' for x in rows),2);self.assertTrue(all(x['Published']=='0' for x in rows))
 def test_image_rights_and_formula_injection(self):
  with tempfile.TemporaryDirectory() as d:
   db=Path(d)/'x.db';c=sqlite3.connect(db);c.execute(CREATE);c.execute(EXT)
   url='https://example.com/a';c.execute('INSERT INTO merchant_evidence VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(url,'s','M','','=SUM(1,2)','','1','EUR','InStock','now','','','UNVERIFIED','HOLD'))
   c.execute('INSERT INTO product_enrichment (source_url,merchant_sku,size,image_urls,image_rights) VALUES(?,?,?,?,?)',(url,'s','M','https://example.com/img.jpg','UNKNOWN'));c.commit();c.close()
   export(db,Path(d)/'out')
   with (Path(d)/'out'/'woocommerce_review_v4.csv').open(encoding='utf-8-sig') as f:
    rows=list(csv.DictReader(f));self.assertEqual(rows[0]['Images'],'');self.assertTrue(rows[0]['Name'].startswith("'"))
if __name__=='__main__':unittest.main()

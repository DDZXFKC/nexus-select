import csv, sqlite3, tempfile, unittest
from pathlib import Path
from bstn_integration import CREATE
from channel_exports_v2 import export

class GroupedExportTest(unittest.TestCase):
 def test_thirteen_sizes_one_product(self):
  with tempfile.TemporaryDirectory() as d:
   db=Path(d)/'test.db';c=sqlite3.connect(db);c.execute(CREATE)
   for i in range(13):
    c.execute('INSERT INTO merchant_evidence (source_url,merchant_sku,size,brand,name,color_claim,price_claim,currency,stock_claim,observed_utc) VALUES (?,?,?,?,?,?,?,?,?,?)',('https://www.bstn.com/p/test','0009238',str(i),'adidas','Adilette','','27.99','EUR','InStock','2026-11-12'))
   c.commit();c.close();out=Path(d)/'out';r=export(db,out)
   self.assertEqual((r['source_size_rows'],r['grouped_products'],r['woo_rows'],r['buyma_products'],r['published']),(13,1,14,1,0))
   with (out/'woocommerce_variation_review.csv').open(encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
   self.assertEqual(rows[0]['Type'],'variable')
   self.assertTrue(all(x['Parent']==rows[0]['SKU'] for x in rows[1:]))
   self.assertTrue(all(x['Published']=='0' and x['In stock?']=='0' for x in rows))
   with (out/'buyma_product_review.csv').open(encoding='utf-8-sig') as f: buyma=list(csv.DictReader(f))
   self.assertEqual(len(buyma),1)
   self.assertEqual(buyma[0]['manufacturer_style_code'],'')
 def test_no_cross_shop_merge_without_identity(self):
  from channel_exports_v2 import key_for
  a={'url':'https://shop1.com/a','merchant_sku':'123','brand':'Nike','manufacturer_sku':'','color':''}
  b={**a,'url':'https://shop2.com/b'}
  self.assertNotEqual(key_for(a),key_for(b))
if __name__=='__main__':unittest.main()

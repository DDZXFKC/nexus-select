import csv,sqlite3,tempfile,unittest
from pathlib import Path
from channel_exports import make_exports

class Exports(unittest.TestCase):
 def test_separate_review_exports(self):
  with tempfile.TemporaryDirectory() as t:
   db=Path(t)/'x.db';c=sqlite3.connect(db)
   c.execute('CREATE TABLE merchant_evidence(source_url TEXT,merchant_sku TEXT,size TEXT,brand TEXT,name TEXT,color_claim TEXT,price_claim TEXT,currency TEXT,stock_claim TEXT,manufacturer_sku TEXT,verification_state TEXT)')
   c.execute('INSERT INTO merchant_evidence VALUES(?,?,?,?,?,?,?,?,?,?,?)',('https://www.bstn.com/p/example','store123','42','adidas','Shoes','','27.99','EUR','InStock','','UNVERIFIED'))
   c.commit();c.close()
   result=make_exports(db,Path(t)/'out');self.assertEqual(result['rows'],1)
   for filename in ('woocommerce_drafts.csv','buyma_review.csv'):
    with (Path(t)/'out'/filename).open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
    self.assertEqual(len(rows),1)
    if filename.startswith('woocommerce'):
     self.assertEqual(rows[0]['Published'],'0');self.assertEqual(rows[0]['In stock?'],'0');self.assertNotEqual(rows[0]['SKU'],'store123')
    else:self.assertEqual(rows[0]['listing_status'],'HOLD')
if __name__=='__main__':unittest.main()

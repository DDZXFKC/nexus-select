import csv,tempfile,unittest
from pathlib import Path
from production_pipeline import run
class TestEndToEnd(unittest.TestCase):
 def test_multi_shop_grouping_and_conservative_profit(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);inp=p/'input.csv'
   data=[{'product_url':'https://shop-a.example/product','brand':'Nike','name':'Shoe','sku':'SHOP-1','size':str(i),'price':'50','currency':'EUR','observed_utc':'2026-11-12'} for i in (8,9)]
   data.append(dict(data[0],product_url='https://shop-b.example/product',sku='SHOP-2',size='10'))
   data.append(dict(data[0],product_url='http://invalid.example/p',sku='BAD'))
   with inp.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=data[0].keys());w.writeheader();w.writerows(data)
   report=run(inp,p/'db.sqlite',p/'out')
   self.assertEqual((report['stage']['accepted'],report['stage']['rejected'],report['grouped_products'],report['woo_rows'],report['buyma_products'],report['published']),(3,1,2,5,2,0))
   with (p/'out'/'profit_review.csv').open(encoding='utf-8-sig') as f: profits=list(csv.DictReader(f))
   self.assertEqual(len(profits),3)
   self.assertTrue(all(not r['estimated_profit_jpy'] and r['status']=='HOLD' for r in profits))
   self.assertEqual(run(inp,p/'db.sqlite',p/'out')['profit_rows'],3)
 def test_profit_when_all_costs_known(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);inp=p/'input.csv'
   data={'product_url':'https://shop-a.example/product','brand':'Nike','name':'Shoe','sku':'S1','size':'8','price':'50','currency':'EUR','observed_utc':'2026-11-12','shipping_cost':'10','import_tax':'500','partner_fee':'300','international_shipping':'1000','platform_fee_rate':'0.1','fx_jpy':'160','selling_price_jpy':'20000'}
   with inp.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=data);w.writeheader();w.writerow(data)
   run(inp,p/'db.sqlite',p/'out')
   with (p/'out'/'profit_review.csv').open(encoding='utf-8-sig') as f:r=next(csv.DictReader(f))
   self.assertEqual(r['estimated_profit_jpy'],'6600.00')
if __name__=='__main__':unittest.main()

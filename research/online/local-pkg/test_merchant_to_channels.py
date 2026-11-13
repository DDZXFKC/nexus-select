import csv,json,tempfile,unittest
from pathlib import Path
from merchant_to_channels import run

class EndToEnd(unittest.TestCase):
 def test_two_products_and_sizes(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   def page(sku,offers):
    return '<script type="application/ld+json">'+json.dumps({'@type':'Product','name':'Shoe '+sku,'brand':{'name':'adidas'},'sku':sku,'color':'Black','offers':[{'price':'50','priceCurrency':'EUR','size':size,'availability':'https://schema.org/InStock'} for size in offers]})+'</script>'
   (root/'a.html').write_text(page('A',['40','41']))
   (root/'b.html').write_text(page('B',['42']))
   with (root/'manifest.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['html_file','product_url']);w.writeheader();w.writerows([{'html_file':'a.html','product_url':'https://www.bstn.com/p/a'},{'html_file':'b.html','product_url':'https://www.bstn.com/p/b'}])
   result=run(root/'manifest.csv',root/'db.sqlite',root/'out')
   self.assertEqual((result['parsed_size_rows'],result['products'],result['woo_rows'],result['buyma_rows'],result['published']),(3,2,5,2,0))
   with (root/'out'/'woocommerce_review_v4.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
   self.assertEqual(sum(x['Type']=='variable' for x in rows),2)
   self.assertTrue(all(x['Published']=='0' and x['In stock?']=='0' for x in rows))
 def test_reject_path_traversal(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   (root/'manifest.csv').write_text('html_file,product_url\n../secret.html,https://www.bstn.com/p/a\n')
   with self.assertRaises(ValueError):run(root/'manifest.csv',root/'db.sqlite',root/'out')
if __name__=='__main__':unittest.main()

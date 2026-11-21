import unittest
from tools.stockcheck_sp_reconcile import reconcile

class Reconcile(unittest.TestCase):
 def test_three_statuses_fail_closed(self):
  parents=[{"woo_product_id":1,"parent_sku":"SP-100"},
           {"woo_product_id":2,"parent_sku":"SP-200"},
           {"woo_product_id":3,"parent_sku":"SP-300"}]
  urls=[{"supplier_product_id":"100","source_url":"https://www.shoepalace.com/products/a"},
        {"supplier_product_id":"200","source_url":"https://www.shoepalace.com/products/b"}]
  evidence=[{"supplier_product_id":"100","status":"verified"}]
  rows=reconcile(parents,urls,evidence)
  self.assertEqual([r["status"] for r in rows],["IDENTITY_SAMPLE_VERIFIED","SOURCE_URL_DOCUMENTED_ID_UNVERIFIED","NO_SOURCE_URL_EVIDENCE"])
  self.assertTrue(all(r["live_stock_verified"]=="NO" for r in rows))
 def test_parent_meta_disagreement(self):
  r=reconcile([{"parent_sku":"SP-10","supplier_product_id":"20"}],[],[])
  self.assertEqual(r[0]["status"],"HOLD_PARENT_ID_MISMATCH")
 def test_duplicate_ids_rejected(self):
  with self.assertRaises(ValueError):reconcile([{"parent_sku":"SP-10"},{"parent_sku":"SP-10"}],[],[])
 def test_conflicting_urls_rejected(self):
  u=[{"supplier_product_id":"10","source_url":"https://www.shoepalace.com/products/a"},
     {"supplier_product_id":"10","source_url":"https://www.shoepalace.com/products/b"}]
  with self.assertRaises(ValueError):reconcile([{"parent_sku":"SP-10"}],u,[])
 def test_no_url_guessing(self):
  r=reconcile([{"parent_sku":"SP-10"}],[],[])
  self.assertEqual(r[0]["source_url"],"")
if __name__=="__main__":unittest.main()

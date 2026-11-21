import unittest
from tools.stockcheck_sp_evidence_adapter import verified_sp_rows, match_snapshot
from tools.stockcheck_sp_join_contract import link_sp_variation

class EvidenceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.rows=verified_sp_rows()
 def test_77_identity_evidence_rows_remain_intact(self):
  self.assertEqual(len(self.rows),77)
  self.assertEqual(len({(r["woo_product_id"],r["variation_id"]) for r in self.rows}),77)
  self.assertEqual(len({r["woo_product_id"] for r in self.rows}),7)
  self.assertTrue(all(r["merchant_variant_id"].isdigit() and r["source_url"].startswith("https://www.shoepalace.com/products/") for r in self.rows))
 def test_no_supplier_sku_data_never_grants_match(self):
  for r in self.rows:
   self.assertFalse(r["merchant_variant_sku"])
   p={"product_id":r["woo_product_id"],"product_type":"variable",
      "shop_code":"SP","supplier_product_id":r["supplier_product_id"],
      "sku":"SP-"+r["supplier_product_id"]}
   v={"product_id":r["woo_product_id"],"variation_id":r["variation_id"],
      "variation_sku":"some-woo-sku","attributes":{"サイズ":r["requested_size"]}}
   self.assertEqual(match_snapshot(p,v,self.rows)["reason"],"NO_VERIFIED_VARIATION_SKU_MATCH")
 def test_documented_one_real_variant_sku_sample(self):
  row=next(r for r in self.rows if r["woo_product_id"]==21376 and r["requested_size"]=="US 5")
  p={"product_id":21376,"product_type":"variable","sku":"SP-8798793826510",
     "shop_code":"SP","supplier_product_id":"8798793826510"}
  v={"product_id":21376,"variation_id":row["variation_id"],"variation_sku":"21141139",
     "attributes":{"サイズ":"US 5"}}
  checked=dict(row,merchant_variant_sku="21141139")
  self.assertEqual(link_sp_variation(p,v,[checked])["status"],"CANDIDATE_ONLY")
  self.assertEqual(link_sp_variation(p,dict(v,variation_sku="21141138"),[checked])["status"],"HOLD")
if __name__=="__main__":unittest.main()

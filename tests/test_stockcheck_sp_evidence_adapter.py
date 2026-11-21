import unittest
from tools.stockcheck_sp_evidence_adapter import verified_sp_rows, match_snapshot
from tools.stockcheck_sp_join_contract import link_sp_variation

class EvidenceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.rows=verified_sp_rows()
 def test_evidence_integrity(self):
  self.assertTrue(self.rows)
  self.assertEqual(len({(r["woo_product_id"],r["variation_id"]) for r in self.rows}),len(self.rows))
  self.assertEqual(len({(r["supplier_product_id"],r["merchant_variant_sku"]) for r in self.rows}),len(self.rows))
  self.assertTrue({21376,19905,19812,19801,20043}.issubset({r["woo_product_id"] for r in self.rows}))
  for r in self.rows:
   self.assertEqual(r["merchant_variant_sku"],r["woo_variation_sku"])
   self.assertTrue(r["sku_evidence"])
   self.assertTrue(r["sku_verified_at_utc"])
 def test_each_row_matches_exact_woo_sku_and_wrong_sku_is_held(self):
  for r in self.rows:
   p={"product_id":r["woo_product_id"],"product_type":"variable","sku":"SP-"+r["supplier_product_id"],
      "shop_code":"SP","supplier_product_id":r["supplier_product_id"]}
   v={"product_id":r["woo_product_id"],"variation_id":r["variation_id"],
      "variation_sku":r["woo_variation_sku"],"attributes":{"サイズ":r["requested_size"]}}
   got=match_snapshot(p,v,self.rows)
   self.assertEqual(got["status"],"CANDIDATE_ONLY",{"row":r,"got":got})
   self.assertEqual(got["merchant_variant_id"],r["merchant_variant_id"])
   self.assertEqual(got["woo_variation_sku"],r["woo_variation_sku"])
   self.assertEqual(match_snapshot(p,dict(v,variation_sku="DELIBERATELY-MISMATCHED"),self.rows)["status"],"HOLD")
   self.assertEqual(match_snapshot(p,dict(v,variation_sku=""),self.rows)["status"],"HOLD")
   self.assertEqual(match_snapshot(p,dict(v,variation_id=99999999),self.rows)["status"],"HOLD")
 def test_size_text_irrelevant_to_identity(self):
  r=self.rows[0]
  p={"product_id":r["woo_product_id"],"product_type":"variable","sku":"SP-"+r["supplier_product_id"],
      "shop_code":"SP","supplier_product_id":r["supplier_product_id"]}
  v={"product_id":r["woo_product_id"],"variation_id":r["variation_id"],
     "variation_sku":r["woo_variation_sku"],"attributes":{"サイズ":"display text is irrelevant"}}
  self.assertEqual(match_snapshot(p,v,self.rows)["status"],"CANDIDATE_ONLY")
 def test_bad_supplier_sku_fails_closed(self):
  r=self.rows[0]
  p={"product_id":r["woo_product_id"],"product_type":"variable","sku":"SP-"+r["supplier_product_id"],
      "shop_code":"SP","supplier_product_id":r["supplier_product_id"]}
  v={"product_id":r["woo_product_id"],"variation_id":r["variation_id"],
     "variation_sku":r["woo_variation_sku"]}
  self.assertEqual(link_sp_variation(p,v,[dict(r,merchant_variant_sku="DIFFERENT")])["status"],"HOLD")
if __name__=="__main__":unittest.main()

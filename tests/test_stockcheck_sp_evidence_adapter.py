import unittest
from tools.stockcheck_sp_evidence_adapter import verified_sp_rows, match_snapshot
from tools.stockcheck_sp_join_contract import link_sp_variation

class EvidenceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rows=verified_sp_rows()
 def test_evidence_integrity_not_fixed_row_count(self):
  self.assertTrue(self.rows, "empty evidence")
  self.assertEqual(len(set((x["woo_product_id"],x["variation_id"]) for x in self.rows)),len(self.rows))
  self.assertTrue({21376,19905,19812,19801,20043}.issubset(set(x["woo_product_id"] for x in self.rows)))
  self.assertTrue(all(x["shop_code"]=="SP" for x in self.rows))
  self.assertTrue(all(x["merchant_size"] and x["merchant_variant_id"] for x in self.rows))
  self.assertTrue(all(x["requested_color"] for x in self.rows)) # supplier label, not Woo attribute
 def test_all_rows_match_exact_woo_variation(self):
  for row in self.rows:
   pid=row["woo_product_id"]
   p={"product_id":pid,"product_type":"variable","sku":"SP-"+row["supplier_product_id"],
      "shop_code":"SP","supplier_product_id":row["supplier_product_id"]}
   v={"product_id":pid,"variation_id":row["variation_id"],
      "attributes":{"サイズ":row["requested_size"]}}
   got=match_snapshot(p,v,self.rows)
   self.assertEqual(got["status"],"CANDIDATE_ONLY",{"row":row,"decision":got})
   self.assertEqual(got["merchant_variant_id"],row["merchant_variant_id"])
 def test_grade_school_sizes_are_strict_and_identity_bound(self):
  gs=[x for x in self.rows if "Y (" in x["requested_size"]]
  self.assertTrue(gs)
  for row in gs:
   p={"product_id":row["woo_product_id"],"product_type":"variable",
      "sku":"SP-"+row["supplier_product_id"],"shop_code":"SP",
      "supplier_product_id":row["supplier_product_id"]}
   v={"product_id":row["woo_product_id"],"variation_id":row["variation_id"],
      "attributes":{"サイズ":row["requested_size"]}}
   self.assertEqual(match_snapshot(p,v,self.rows)["status"],"CANDIDATE_ONLY")
   bad=dict(row,merchant_size="4Y" if row["merchant_size"]!="4Y" else "3Y")
   self.assertEqual(link_sp_variation(p,v,[bad])["status"],"HOLD")
   self.assertEqual(link_sp_variation(p,dict(v,variation_id=999999),[row])["status"],"HOLD")
   self.assertEqual(link_sp_variation(p,dict(v,attributes={"サイズ":"EU 36","カラー":row["requested_color"]}),[row])["status"],"HOLD")
 def test_owner_removes_us_prefix_without_losing_variant_identity(self):
  for row in self.rows:
   pid=row["woo_product_id"]
   p={"product_id":pid,"product_type":"variable","sku":"SP-"+row["supplier_product_id"],
      "shop_code":"SP","supplier_product_id":row["supplier_product_id"]}
   cleaned=row["requested_size"].removeprefix("US ")
   v={"product_id":pid,"variation_id":row["variation_id"],"attributes":{"サイズ":cleaned}}
   got=match_snapshot(p,v,self.rows)
   self.assertEqual(got["status"],"CANDIDATE_ONLY",{"row":row,"decision":got})
   self.assertEqual(got["merchant_variant_id"],row["merchant_variant_id"])
   if "cm)" in row["requested_size"]:
    self.assertIn("cm)",cleaned)
 def test_prefix_removal_cannot_cross_variation_boundary(self):
  row=self.rows[0]
  p={"product_id":row["woo_product_id"],"product_type":"variable",
     "sku":"SP-"+row["supplier_product_id"],"shop_code":"SP",
     "supplier_product_id":row["supplier_product_id"]}
  v={"product_id":row["woo_product_id"],"variation_id":999999,
     "attributes":{"サイズ":row["requested_size"].removeprefix("US ")}}
  self.assertEqual(match_snapshot(p,v,self.rows)["status"],"HOLD")
 def test_not_alternative_variation(self):
  row=self.rows[0];p={"product_id":21376,"product_type":"variable","sku":"SP-8798793826510","shop_code":"SP","supplier_product_id":"8798793826510"}
  v={"product_id":21376,"variation_id":999999,"attributes":{"サイズ":row["requested_size"]}}
  self.assertEqual(match_snapshot(p,v,self.rows)["status"],"HOLD")
 def test_no_gender_or_size_conversion(self):
  row=self.rows[0];p={"product_id":21376,"product_type":"variable","sku":"SP-8798793826510","shop_code":"SP","supplier_product_id":"8798793826510"}
  v={"product_id":21376,"variation_id":row["variation_id"],"attributes":{"サイズ":"UK 5"}}
  self.assertEqual(match_snapshot(p,v,self.rows)["status"],"HOLD")
 def test_us_numeric_option_requires_variation_evidence(self):
  row=self.rows[0]
  p={"product_id":21376,"product_type":"variable","sku":"SP-8798793826510","shop_code":"SP","supplier_product_id":"8798793826510"}
  v={"product_id":21376,"variation_id":row["variation_id"],"attributes":{"サイズ":row["requested_size"]}}
  option=row["requested_size"].removeprefix("US ")
  candidate=dict(row,merchant_size=option)
  self.assertEqual(link_sp_variation(p,v,[candidate])["status"],"CANDIDATE_ONLY")
  candidate["variation_id"]=123456
  self.assertEqual(link_sp_variation(p,v,[candidate])["status"],"HOLD")
if __name__=="__main__":unittest.main()

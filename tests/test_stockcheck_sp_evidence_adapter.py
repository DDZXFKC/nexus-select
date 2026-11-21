import unittest
from tools.stockcheck_sp_evidence_adapter import verified_sp_rows, match_snapshot
from tools.stockcheck_sp_join_contract import link_sp_variation

class EvidenceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rows=verified_sp_rows()
 def test_33_evidence_rows(self):
  self.assertEqual(len(self.rows),33)
  self.assertEqual(len(set(x["variation_id"] for x in self.rows)),33)
  self.assertEqual(set(x["woo_product_id"] for x in self.rows),{21376,19905})
 def test_all_rows_match_exact_woo_variation(self):
  ids={21376:"8798793826510",19905:"8813225803982"}
  for row in self.rows:
   pid=row["woo_product_id"]
   p={"product_id":pid,"product_type":"variable","sku":"SP-"+ids[pid],
      "shop_code":"SP","supplier_product_id":ids[pid]}
   v={"product_id":pid,"variation_id":row["variation_id"],
      "attributes":{"サイズ":row["requested_size"],"カラー":row["requested_color"]}}
   got=match_snapshot(p,v,self.rows)
   self.assertEqual(got["status"],"CANDIDATE_ONLY",got)
   self.assertEqual(got["merchant_variant_id"],row["merchant_variant_id"])
 def test_not_alternative_variation(self):
  row=self.rows[0];p={"product_id":21376,"product_type":"variable","sku":"SP-8798793826510","shop_code":"SP","supplier_product_id":"8798793826510"}
  v={"product_id":21376,"variation_id":999999,"attributes":{"サイズ":row["requested_size"],"カラー":row["requested_color"]}}
  self.assertEqual(match_snapshot(p,v,self.rows)["status"],"HOLD")
 def test_no_gender_or_size_conversion(self):
  row=self.rows[0];p={"product_id":21376,"product_type":"variable","sku":"SP-8798793826510","shop_code":"SP","supplier_product_id":"8798793826510"}
  v={"product_id":21376,"variation_id":row["variation_id"],"attributes":{"サイズ":"UK 5","カラー":row["requested_color"]}}
  self.assertEqual(match_snapshot(p,v,self.rows)["status"],"HOLD")
 def test_us_numeric_option_requires_variation_evidence(self):
  row=self.rows[0]
  p={"product_id":21376,"product_type":"variable","sku":"SP-8798793826510","shop_code":"SP","supplier_product_id":"8798793826510"}
  v={"product_id":21376,"variation_id":row["variation_id"],"attributes":{"サイズ":row["requested_size"],"カラー":row["requested_color"]}}
  option=row["requested_size"].removeprefix("US ")
  candidate=dict(row,merchant_size=option)
  self.assertEqual(link_sp_variation(p,v,[candidate])["status"],"CANDIDATE_ONLY")
  candidate["variation_id"]=123456
  self.assertEqual(link_sp_variation(p,v,[candidate])["status"],"HOLD")
if __name__=="__main__":unittest.main()

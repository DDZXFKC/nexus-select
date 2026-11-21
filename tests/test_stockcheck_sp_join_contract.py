import unittest
from tools.stockcheck_sp_join_contract import link_sp_variation

P={"product_id":100,"product_type":"variable","sku":"SP-8813225869518","shop_code":"SP","supplier_product_id":"8813225869518"}
V={"product_id":100,"variation_id":200,"attributes":{"サイズ":"US 9","カラー":"Black"},"variation_sku":"OTHER-2"}
O=[{"shop_code":"SP","supplier_product_id":"8813225869518","merchant_variant_id":"920","source_url":"https://example.test/p/real","size":"US 9","color":"Black","verified":True}]
class TestSPJoin(unittest.TestCase):
 def test_exact_parent_and_variation(self):
  r=link_sp_variation(P,V,O)
  self.assertEqual(r["status"],"CANDIDATE_ONLY")
  self.assertEqual(r["woo_variation_id"],200)
 def test_variation_sku_must_not_be_parent(self):
  self.assertEqual(link_sp_variation(P,V,O)["status"],"CANDIDATE_ONLY")
 def test_wrong_parent_meta(self):
  self.assertEqual(link_sp_variation(dict(P,supplier_product_id="123"),V,O)["reason"],"SP_PARENT_ID_MISMATCH")
 def test_unreviewed_not_usable(self):
  self.assertEqual(link_sp_variation(P,V,[dict(O[0],verified=False)])["reason"],"NO_VERIFIED_SIZE_COLOR_MATCH")
 def test_size_not_guessed(self):
  self.assertEqual(link_sp_variation(P,dict(V,attributes={"サイズ":"9","カラー":"Black"}),O)["status"],"HOLD")
 def test_color_not_guessed(self):
  self.assertEqual(link_sp_variation(P,dict(V,attributes={"サイズ":"US 9","カラー":"Blue"}),O)["status"],"HOLD")
 def test_ambiguous(self):
  self.assertEqual(link_sp_variation(P,V,O+O)["reason"],"AMBIGUOUS_SUPPLIER_VARIANT")
 def test_missing_size(self):
  self.assertEqual(link_sp_variation(P,dict(V,attributes={"カラー":"Black"}),O)["reason"],"MISSING_SIZE_OR_COLOR")
 def test_missing_variation(self):
  self.assertEqual(link_sp_variation(P,dict(V,variation_id=0),O)["reason"],"MISSING_VARIATION")
 def test_simple_allowed_if_exact_proven(self):
  p=dict(P,product_type="simple")
  v={"product_id":100,"variation_id":0,"attributes":{}}
  x=[dict(O[0],size="",color="")]
  self.assertEqual(link_sp_variation(p,v,x)["status"],"CANDIDATE_ONLY")
 def test_simple_wrong_variation(self):
  self.assertEqual(link_sp_variation(dict(P,product_type="simple"),V,O)["reason"],"SIMPLE_VARIATION_MISMATCH")
if __name__=="__main__":unittest.main()

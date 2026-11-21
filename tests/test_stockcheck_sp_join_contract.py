import unittest
from tools.stockcheck_sp_join_contract import link_sp_variation

P={"product_id":21376,"product_type":"variable","sku":"SP-8798793826510","shop_code":"SP","supplier_product_id":"8798793826510"}
V={"product_id":21376,"variation_id":21380,"variation_sku":"21141139","attributes":{"サイズ":"US 5"}}
O={"shop_code":"SP","supplier_product_id":"8798793826510",
   "woo_product_id":21376,"variation_id":21380,
   "merchant_variant_sku":"21141139","merchant_variant_id":"48297066070222",
   "source_url":"https://www.shoepalace.com/products/vans-d9rbla-premium-old-skool-36-bandana-black-mens-skate-shoes-black","verified":True}
class TestSPJoin(unittest.TestCase):
 def match(self,p=P,v=V,offers=None):
  return link_sp_variation(p,v,[O] if offers is None else offers)
 def test_exact_sku(self):
  x=self.match()
  self.assertEqual(x["status"],"CANDIDATE_ONLY")
  self.assertEqual(x["woo_variation_sku"],"21141139")
 def test_size_labels_do_not_affect_sku_join(self):
  for size in ("US 5","5","US 5Y (23cm)","unrelated display label"):
   self.assertEqual(self.match(v=dict(V,attributes={"サイズ":size}))["status"],"CANDIDATE_ONLY")
 def test_supplier_sku_mismatch(self):
  self.assertEqual(self.match(offers=[dict(O,merchant_variant_sku="OTHER")])["status"],"HOLD")
 def test_no_supplier_sku_must_hold(self):
  x=dict(O); x.pop("merchant_variant_sku")
  self.assertEqual(self.match(offers=[x])["reason"],"NO_VERIFIED_VARIATION_SKU_MATCH")
 def test_wrong_woo_variant(self):
  self.assertEqual(self.match(v=dict(V,variation_id=999999))["status"],"HOLD")
 def test_wrong_parent(self):
  self.assertEqual(self.match(p=dict(P,supplier_product_id="123"))["reason"],"SP_PARENT_ID_MISMATCH")
 def test_ambiguous(self):
  self.assertEqual(self.match(offers=[O,O])["reason"],"AMBIGUOUS_SUPPLIER_VARIANT")
 def test_missing_woo_sku(self):
  self.assertEqual(self.match(v=dict(V,variation_sku=""))["reason"],"MISSING_WOO_VARIATION_SKU")
 def test_bogus_url(self):
  self.assertEqual(self.match(offers=[dict(O,source_url="https://attacker.test/products/fake")])["status"],"HOLD")
 def test_unverified_supplier_offer(self):
  self.assertEqual(self.match(offers=[dict(O,verified=False)])["status"],"HOLD")
 def test_no_variation_or_simple(self):
  self.assertEqual(self.match(v=dict(V,variation_id=0))["reason"],"INVALID_WOO_IDS")
  self.assertEqual(self.match(p=dict(P,product_type="simple"))["reason"],"UNSUPPORTED_TYPE")
if __name__=="__main__":unittest.main()

"""Coverage audit for known SP supplier URLs; never equate URL with verified stock."""
import csv
import unittest
from pathlib import Path
from urllib.parse import urlparse

SOURCE=Path(__file__).resolve().parents[1]/"data/xserver-export/sp-30-source-url-coverage-2026-11-21.csv"
class URLCoverage(unittest.TestCase):
 def test_every_known_sp_parent_has_a_single_source_and_status(self):
  with SOURCE.open(encoding="utf-8",newline="") as f:
   rows=list(csv.DictReader(f))
  self.assertTrue(rows)
  ids=set()
  for row in rows:
   pid=row["supplier_product_id"]
   self.assertTrue(pid.isdecimal())
   self.assertNotIn(pid,ids,"duplicate supplier product ID")
   ids.add(pid)
   self.assertEqual(row["parent_sku"],"SP-"+pid)
   parsed=urlparse(row["source_url"])
   self.assertEqual(parsed.scheme,"https")
   self.assertEqual(parsed.hostname,"www.shoepalace.com")
   self.assertTrue(parsed.path.startswith("/products/"))
   self.assertTrue(row["source_files"])
   self.assertIn(row["verification_status"],{"IDENTITY_VERIFIED_2026_11_21","URL_DOCUMENTED_ID_UNVERIFIED"})
   if row["verification_status"]=="IDENTITY_VERIFIED_2026_11_21":
    self.assertTrue(row["woo_product_id"].isdecimal())
    self.assertGreater(int(row["verified_variations"]),0)
   else:
    self.assertEqual(row["woo_product_id"],"")
    self.assertEqual(row["verified_variations"],"0")
if __name__=="__main__":unittest.main()

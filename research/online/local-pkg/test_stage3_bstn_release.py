import json,unittest
from stage3_catalog import listing_hits,discover_listings
from test_stage3_bstn_listing import CFG,fixture

def changed(page, replacements):
 raw=fixture(page)
 data=json.loads(raw.decode().split('>',1)[1].rsplit('<',1)[0])
 hits=data['props']['pageProps']['serverState']['initialResults']['magento2_eu_products']['results'][0]['hits']
 for i,u in replacements.items():hits[i]['url']=u
 return ('<script id="__NEXT_DATA__">'+json.dumps(data)+'</script>').encode()

class ReleaseHits(unittest.TestCase):
 def test_release_count(self):
  urls,n,p=listing_hits(changed(1,{0:'r/release'}),1)
  self.assertEqual((len(urls),n,p),(96,97,2))
 def test_excluded_queue(self):
  class F:
   def listing(self,u):return fixture(2) if 'page=2' in u else changed(1,{0:'r/release'})
  urls,n,e=discover_listings(CFG,F())
  self.assertEqual((len(urls),n,e),(96,2,1))
  self.assertTrue(all('/eu_en/p/' in u for u in urls))
 def test_unknown_prefix(self):
  with self.assertRaises(ValueError):listing_hits(changed(1,{0:'x/unknown'}),1)
 def test_duplicate_release(self):
  with self.assertRaises(ValueError):listing_hits(changed(1,{0:'r/release',1:'r/release'}),1)
 def test_cross_page_duplicate(self):
  class F:
   def listing(self,u):return changed(2,{0:'r/release'}) if 'page=2' in u else changed(1,{0:'r/release'})
  with self.assertRaises(ValueError):discover_listings(CFG,F())
if __name__=='__main__':unittest.main()

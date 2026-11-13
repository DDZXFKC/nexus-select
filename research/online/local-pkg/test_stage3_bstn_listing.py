import unittest,json
from stage3_catalog import listing_scope,listing_hits,discover_listings,listing_page,Fetch
HOST='www.bstn.com'
SEED='https://www.bstn.com/eu_en/men/all-products?categories=Men~All+Products~Footwear'
CFG=dict(host=HOST,listing_seeds=[SEED],product_path_regex='/eu_en/p/[^/]+')
def fixture(page,total=97,start=None):
 start=(page-1)*96 if start is None else start
 hits=[dict(url='p/item-'+str(i)) for i in range(start,start+min(96,total-(page-1)*96))]
 r=dict(nbHits=total,nbPages=(total+95)//96,hitsPerPage=96,page=page-1,hits=hits)
 data=dict(props=dict(pageProps=dict(serverState=dict(initialResults=dict(magento2_eu_products=dict(results=[r]))))))
 return ('<script id="__NEXT_DATA__" type="application/json">'+json.dumps(data)+'</script>').encode()
class Listing(unittest.TestCase):
 def test_pages(self):
  class F:
   def listing(self,u):return fixture(2 if 'page=2' in u else 1)
  urls,n,_=discover_listings(CFG,F());self.assertEqual((len(urls),n),(97,2))
 def test_page_index(self):
  with self.assertRaises(ValueError):listing_hits(fixture(1),2)
 def test_scope(self):
  for u in (SEED+'&redirect=x',SEED.replace(HOST,'media.bstn.com'),SEED+'&page=0',SEED+'&categories=Men'):
   with self.assertRaises(ValueError):listing_scope(u,HOST)
 def test_duplicate(self):
  class F:
   def listing(self,u):return fixture(2,start=0) if 'page=2' in u else fixture(1)
  with self.assertRaises(ValueError):discover_listings(CFG,F())
 def test_missing(self):
  with self.assertRaises(ValueError):listing_hits(b'<html></html>',1)
 def test_url(self):
  self.assertIn('page=2',listing_page(SEED,2))
if __name__=='__main__':unittest.main()

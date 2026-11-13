import json
import unittest
from urllib.parse import urlsplit, parse_qs
from stage3_catalog import listing_hits, discover_listings
from test_stage3_bstn_listing import CFG

def fixture(page=1,total=3443,aux_page=0,primary_page=None,count=2):
    def result(n,p,prefix):
        return dict(nbHits=n,nbPages=(n+95)//96,hitsPerPage=96,page=p,
                    hits=[dict(url=f'p/{prefix}-{i}') for i in range(p*96,min((p+1)*96,n))])
    primary=result(total,page-1,'primary')
    if primary_page is not None:
        primary['page']=primary_page
    auxiliary=result(13724,aux_page,'aux')
    results=([primary]+[auxiliary]*3)[:count]
    data=dict(props=dict(pageProps=dict(serverState=dict(initialResults=dict(magento2_eu_products=dict(results=results))))))
    return ('<script id="__NEXT_DATA__" type="application/json">'+json.dumps(data)+'</script>').encode()

class TwoResults(unittest.TestCase):
    def test_first_page(self):
        urls,total,pages=listing_hits(fixture(),1)
        self.assertEqual((len(urls),total,pages),(96,3443,36))
        self.assertTrue(all('/p/primary-' in u for u in urls))
    def test_second_page(self):
        urls,_,_=listing_hits(fixture(page=2),2)
        self.assertEqual(len(urls),96)
        self.assertTrue(urls[0].endswith('primary-96'))
    def test_auxiliary_pagination_rejected(self):
        with self.assertRaises(ValueError):
            listing_hits(fixture(page=2,aux_page=1),2)
    def test_primary_pagination_rejected(self):
        with self.assertRaises(ValueError):
            listing_hits(fixture(page=2,primary_page=0),2)
    def test_unrecognized_shapes_rejected(self):
        for count in (0,4):
            with self.subTest(count=count):
                with self.assertRaises(ValueError):
                    listing_hits(fixture(count=count),1)
    def test_full_coverage(self):
        class FetchFixture:
            def listing(self,url):
                page=int(parse_qs(urlsplit(url).query).get('page',['1'])[0])
                return fixture(page=page)
        urls,pages,excluded=discover_listings(CFG,FetchFixture())
        self.assertEqual((len(urls),pages,excluded),(3443,36,0))
        self.assertTrue(all('/p/primary-' in u for u in urls))

if __name__=='__main__':
    unittest.main()

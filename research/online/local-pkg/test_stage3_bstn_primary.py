import unittest,json
from stage3_catalog import listing_hits

def result(page,total,prefix):
 return dict(nbHits=total,nbPages=(total+95)//96,hitsPerPage=96,page=page,hits=[dict(url=f'p/{prefix}-{i}') for i in range(page*96,min(total,(page+1)*96))])
def raw(results):
 return ('<script id="__NEXT_DATA__">'+json.dumps(dict(props=dict(pageProps=dict(serverState=dict(initialResults=dict(magento2_eu_products=dict(results=results)))))))+'</script>').encode()
class Test(unittest.TestCase):
 def test_first(self):
  u,n,p=listing_hits(raw([result(0,381,'main'),result(0,384,'aux'),result(0,3447,'all')]),1);self.assertEqual((len(u),n,p),(96,381,4));self.assertTrue(all('/main-' in x for x in u))
 def test_second(self):
  u,n,p=listing_hits(raw([result(1,381,'main'),result(0,384,'aux'),result(0,3447,'all')]),2);self.assertTrue(u[0].endswith('main-96'))
 def test_last(self):
  self.assertEqual(len(listing_hits(raw([result(3,381,'main'),result(0,384,'aux'),result(0,3447,'all')]),4)[0]),93)
 def test_single(self):
  self.assertEqual(listing_hits(raw([result(0,97,'main')]),1)[1],97)
 def test_wrong_primary(self):
  with self.assertRaises(ValueError):listing_hits(raw([result(0,384,'aux'),result(1,381,'main'),result(0,3447,'all')]),2)
 def test_shape(self):
  with self.assertRaises(ValueError):listing_hits(raw([result(0,381,'main'),result(0,384,'aux')]),1)
 def test_aux_moves(self):
  with self.assertRaises(ValueError):listing_hits(raw([result(1,381,'main'),result(1,384,'aux'),result(0,3447,'all')]),2)
if __name__=='__main__':unittest.main()

import unittest,sqlite3,json
from datetime import datetime,timezone
from stage3_persistent_discovery import setup,capture,summary,PersistentFetch
from unittest.mock import patch
from stage3_catalog import Fetch
def cfg():
 return dict(host='www.bstn.com',enabled=True,permission_reference='fixture only',reviewer='fixture',reviewed_at=datetime.now(timezone.utc).isoformat(),interval_seconds=5,request_budget=10,listing_seeds=['https://www.bstn.com/eu_en/men/all-products?categories=Men~All+Products~Footwear'],product_path_regex=r'/eu_en/p/[a-z0-9-]+')
def raw(page=1,total=96,start=0,release=False):
 hits=[dict(url=('r/' if release and i==0 else 'p/')+'item-'+str(start+i)) for i in range(min(96,total-(page-1)*96))]
 r=dict(nbHits=total,nbPages=(total+95)//96,hitsPerPage=96,page=page-1,hits=hits)
 x=dict(props=dict(pageProps=dict(serverState=dict(initialResults=dict(magento2_eu_products=dict(results=[r]))))))
 return ('<script id="__NEXT_DATA__">'+json.dumps(x)+'</script>').encode()
class PersistentTests(unittest.TestCase):
 def setUp(self):
  self.c=sqlite3.connect(':memory:');self.cfg=cfg();setup(self.c,self.cfg,10)
 def tearDown(self):self.c.close()
 def test_replay(self):
  for _ in range(2):capture(self.c,self.cfg,1,raw(release=True),'2026-11-13T00:00:00Z')
  self.assertEqual(summary(self.c)['captures'],1);self.assertEqual(summary(self.c)['unique_candidates'],95)
  self.assertEqual(self.c.execute('SELECT raw FROM pages').fetchone()[0],raw(release=True))
 def test_drift(self):
  capture(self.c,self.cfg,1,raw(total=192),'2026-11-13T00:00:00Z')
  capture(self.c,self.cfg,2,raw(2,191,95),'2026-11-13T00:01:00Z')
  self.assertTrue(summary(self.c)['drift']);self.assertEqual(summary(self.c)['unique_candidates'],190)
 def test_missing_not_removed(self):
  capture(self.c,self.cfg,1,raw(),'2026-11-13T00:00:00Z')
  capture(self.c,self.cfg,1,raw(start=96),'2026-11-13T00:01:00Z')
  self.assertEqual(summary(self.c)['unique_candidates'],192);self.assertFalse(summary(self.c)['catalog_complete'])
 def test_invalid(self):
  with self.assertRaises(Exception):capture(self.c,self.cfg,2,raw(),'x')
  self.assertEqual(summary(self.c)['captures'],0)
 def test_scope(self):
  self.cfg['product_path_regex']=r'/eu_en/p/no-match'
  with self.assertRaises(Exception):capture(self.c,self.cfg,1,raw(),'x')
 def test_stale(self):
  self.cfg['reviewed_at']='2000-01-01T00:00:00Z'
  with self.assertRaises(Exception):setup(self.c,self.cfg,10)
 def test_cap(self):
  with self.assertRaises(Exception):setup(self.c,self.cfg,11)
 def test_budget_and_raw(self):
  f=PersistentFetch(self.cfg,self.c,1)
  with patch.object(Fetch,'read',return_value=raw()) as read:
   f.listing('https://www.bstn.com/example')
   with self.assertRaises(Exception):f.listing('https://www.bstn.com/example')
   self.assertEqual(read.call_count,1)
  self.assertEqual(self.c.execute('SELECT raw FROM ledger').fetchone()[0],raw())
 def test_failed_stop(self):
  f=PersistentFetch(self.cfg,self.c,10)
  with patch.object(Fetch,'read',side_effect=ValueError('HTTP 403')) as read:
   for _ in range(2):
    with self.assertRaises(Exception):f.listing('https://www.bstn.com/example')
   self.assertEqual(read.call_count,1)
 def test_pending_stop(self):
  self.c.execute("INSERT INTO ledger(url,kind,at,status) VALUES('x','listing',0,'PENDING')");self.c.commit()
  with patch.object(Fetch,'read') as read:
   with self.assertRaises(Exception):PersistentFetch(self.cfg,self.c,10).listing('x')
   read.assert_not_called()
if __name__=='__main__':unittest.main()

import unittest
from stage3_listing_probe import probe
from test_stage3_bstn_listing import CFG,fixture

class F:
    def __init__(self,raws):self.raws=iter(raws);self.calls=0
    def listing(self,url):self.calls+=1;return next(self.raws)

class Probe(unittest.TestCase):
    def test_drift(self):
        f=F([fixture(1,200),fixture(2,199,start=95)])
        urls,e=probe(CFG,f,2)
        self.assertEqual(len(urls),191)
        self.assertTrue(e['drift'])
        self.assertFalse(e['catalog_complete'])
        self.assertEqual(len(e['pages'][1]['overlap']),1)
    def test_release(self):
        f=F([fixture(1).replace(b'p/item-0"',b'r/item-0"')])
        urls,e=probe(CFG,f,1)
        self.assertEqual((len(urls),e['excluded_release']),(95,1))
    def test_stable_still_partial(self):
        urls,e=probe(CFG,F([fixture(1),fixture(2)]),2)
        self.assertEqual(len(urls),97)
        self.assertFalse(e['drift'])
        self.assertEqual(e['coverage'],'PARTIAL')
    def test_invalid_page(self):
        with self.assertRaises(ValueError):probe(CFG,F([fixture(1),fixture(1)]),2)
    def test_bound(self):
        f=F([])
        with self.assertRaises(ValueError):probe(CFG,f,6)
        self.assertEqual(f.calls,0)
    def test_fetch_failure(self):
        class Bad:
            def listing(self,url):raise ValueError('HTTP 403')
        with self.assertRaisesRegex(ValueError,'HTTP 403'):probe(CFG,Bad(),2)

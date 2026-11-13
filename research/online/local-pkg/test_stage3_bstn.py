import unittest
from unittest.mock import patch
from stage3_catalog import *
HOST='www.bstn.com'
MEDIA='https://media.bstn.com/sitemap.xml'
CHILD='https://media.bstn.com/sitemap-1-1.xml'
PRODUCT='https://www.bstn.com/eu_en/p/a'
class BSTN(unittest.TestCase):
 def test_scope(self):
  self.assertEqual(sitemap_scope(MEDIA,HOST),MEDIA)
  for u in ['https://media.bstn.com/a.jpg','https://evil.example/a.xml','https://media.bstn.com/a.xml?x=1']:
   with self.assertRaises(ValueError):sitemap_scope(u,HOST)
  with self.assertRaises(ValueError):scope(MEDIA,HOST)
 def test_large(self):
  raw=b'<urlset><!--'+b'x'*10487622+b'--><url><loc>'+PRODUCT.encode()+b'</loc></url></urlset>'
  self.assertEqual(sitemap(raw),('urlset',[PRODUCT]))
 def test_cap(self):
  with patch('stage3_catalog.SITEMAP_CAP',32):
   with self.assertRaises(ValueError):sitemap(b'<urlset>'+b' '*32+b'</urlset>')
 def test_discover(self):
  cfg=dict(host=HOST,sitemap_seeds=[MEDIA],product_path_regex='/eu_en/p/[^/]+')
  data={MEDIA:('<sitemapindex><sitemap><loc>'+CHILD+'</loc></sitemap></sitemapindex>').encode(),CHILD:('<urlset><url><loc>'+PRODUCT+'</loc></url><url><loc>'+MEDIA+'</loc></url></urlset>').encode()}
  self.assertEqual(discover(cfg,data.__getitem__),([PRODUCT],2,1))
 def test_media_product_rejected(self):
  f=Fetch.__new__(Fetch);f.cfg={'host':HOST}
  with self.assertRaises(ValueError):f(MEDIA)
 def test_unlisted(self):
  f=Fetch.__new__(Fetch);f.cfg={'host':HOST};f.listed=set()
  with self.assertRaises(ValueError):f.sitemap(MEDIA)
 def test_bad_xml(self):
  for raw in [b'<urlset><bad/></urlset>',b'<!DOCTYPE x><urlset/>',b'<urlset><url><loc/></url></urlset>']:
   with self.assertRaises(ValueError):sitemap(raw)
 def test_robots_denial(self):
  f=Fetch.__new__(Fetch);f.cfg={'host':HOST};f.listed={MEDIA}
  rp=urllib.robotparser.RobotFileParser();rp.parse(['User-agent: *','Disallow: /'])
  f.robots={'media.bstn.com':rp}
  with self.assertRaises(ValueError):f.sitemap(MEDIA)
if __name__=='__main__':unittest.main()

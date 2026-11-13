import unittest,sqlite3,tempfile
from pathlib import Path
from stage3_catalog import *
from test_stage2_detail import html,parent
HOST='www.notre-shop.com'
URL='https://'+HOST+'/products/a'
CFG=dict(host=HOST,product_path_regex='/products/[^/]+',sitemap_seeds=['https://'+HOST+'/sitemap.xml'])
class Catalog(unittest.TestCase):
 def test_discover(self):
  raw=('<urlset><url><loc>'+URL+'</loc></url><url><loc>'+URL+'</loc></url></urlset>').encode()
  self.assertEqual(discover(CFG,lambda u:raw)[0],[URL])
 def test_scope(self):
  with self.assertRaises(ValueError):scope('https://other.com/a',HOST)
 def test_xml(self):
  with self.assertRaises(ValueError):sitemap(b'<!DOCTYPE a><urlset/>')
 def test_permission(self):
  with self.assertRaises(ValueError):policy(CFG)
 def test_resume(self):
  raw=html(parent()).encode()
  with sqlite3.connect(':memory:') as c:
   init(c);prepare(c,'a',CFG,[URL]);process(c,'a',lambda u:raw,extract,1)
   process(c,'a',lambda u:self.fail('refetch'),extract,1)
   self.assertEqual(c.execute('SELECT count(*) FROM observations').fetchone()[0],1)
   prepare(c,'b',CFG,[URL]);process(c,'b',lambda u:raw,extract,1)
   self.assertEqual(c.execute('SELECT count(*) FROM observations').fetchone()[0],1)
   with tempfile.TemporaryDirectory() as d:
    r=report(c,'b',Path(d));self.assertEqual(r['delta']['new'],0)
 def test_stop(self):
  with sqlite3.connect(':memory:') as c:
   init(c);prepare(c,'a',CFG,[URL])
   with self.assertRaises(ValueError):process(c,'a',lambda u:b'bad',extract,1)
   self.assertEqual(c.execute('SELECT state FROM queue').fetchone()[0],'ERROR')
   self.assertEqual(c.execute('SELECT count(*) FROM observations').fetchone()[0],0)
 def test_product_error_continues(self):
  raw=html(parent()).encode()
  def parser(body,url):
   rows=extract(body,url)
   if url==URL:
    for row in rows:row['fields']['brand']['value']=''
   return rows
  with sqlite3.connect(':memory:') as c:
   init(c);prepare(c,'a',CFG,[URL,URL+'2'])
   process(c,'a',lambda u:raw,parser,2)
   self.assertEqual(dict(c.execute('SELECT url,state FROM queue')),{URL:'ERROR',URL+'2':'DONE'})
   self.assertEqual(c.execute('SELECT complete FROM runs').fetchone()[0],0)
 def test_fetch_error_stops(self):
  def fetch(url):raise ValueError('truncated response')
  with sqlite3.connect(':memory:') as c:
   init(c);prepare(c,'a',CFG,[URL,URL+'2'])
   with self.assertRaises(ValueError):process(c,'a',fetch,extract,2)
   self.assertEqual(dict(c.execute('SELECT url,state FROM queue')),{URL:'ERROR',URL+'2':'PENDING'})
 def test_scope_change(self):
  with sqlite3.connect(':memory:') as c:
   init(c);prepare(c,'a',CFG,[URL])
   with self.assertRaises(ValueError):prepare(c,'a',CFG,[URL,URL+'2'])
if __name__=='__main__':unittest.main()

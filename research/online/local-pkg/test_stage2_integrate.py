import unittest,sqlite3,copy
from stage2_integrate import join,exports,history
from stage2_detail import extract
from test_stage2_detail import html,parent
URL='https://notre-shop.com/p'
def fixture():
 import hashlib
 raw=html(parent()).encode();h=hashlib.sha256(raw).hexdigest()
 b=dict(product_url=URL,sku='s1',size='8 M / Black/White',price='180',currency='USD',brand='Brand',name='Brand Sneaker',product_id='old',color='',availability_claim='')
 return [b],[{'url':URL,'rows':extract(raw,URL)}],{URL:h}
class Integration(unittest.TestCase):
 def test_join_export(self):
  r=join(*fixture());w,b,p,m=exports(r)
  self.assertEqual((len(w),len(b),len(p),len(m)),(2,1,1,1))
  self.assertEqual(r[0]['size'],'8 M')
  self.assertEqual(r[0]['title'],'Brand Sneaker')
  self.assertEqual(w[0]['Images'],'')
  self.assertEqual(w[0]['Regular price'],'')
  self.assertEqual(p[0]['cost_jpy'],'')
  self.assertEqual(b[0]['listing_status'],'HOLD')
 def test_hash(self):
  b,p,h=fixture();h[URL]='wrong'
  with self.assertRaises(ValueError):join(b,p,h)
 def test_price(self):
  b,p,h=fixture();b[0]['price']='181'
  with self.assertRaises(ValueError):join(b,p,h)
 def test_missing(self):
  b,p,h=fixture();p[0]['rows']=[]
  with self.assertRaises(ValueError):join(b,p,h)
 def test_duplicate(self):
  b,p,h=fixture();p[0]['rows']*=2
  with self.assertRaises(ValueError):join(b,p,h)
 def test_history(self):
  r=join(*fixture())
  with sqlite3.connect(':memory:') as c:
   self.assertEqual(history(c,r),1)
   self.assertEqual(history(c,r),1)
   changed=copy.deepcopy(r);changed[0]['price']='181';changed[0]['capture_hash']='new'
   self.assertEqual(history(c,changed),2)
 def test_simple(self):
  r=join(*fixture())[0];r.update(source_url='https://www.bstn.com/p',merchant_product_id='0012650',brand='Jason Markk',size='ONE SIZE')
  w,b,p,m=exports([r])
  self.assertEqual(len(w),1);self.assertEqual(w[0]['Type'],'simple')
  self.assertEqual(w[0]['Attribute 1 name'],'')
  r['merchant_product_id']='other'
  self.assertEqual(exports([r])[0][0]['Type'],'variable')
 def test_group_conflict(self):
  r=join(*fixture())[0];s=dict(r,source_variant_id='other',size='9',brand='Other')
  with self.assertRaises(ValueError):exports([r,s])
 def test_color_groups(self):
  r=join(*fixture())[0];s=dict(r,source_variant_id='other',color='Red')
  self.assertEqual(len(exports([r,s])[1]),2)
if __name__=='__main__':unittest.main()

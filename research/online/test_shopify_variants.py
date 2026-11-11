import unittest
from shopify_variants import parse
class ShopifyVariantTests(unittest.TestCase):
 def test_notre_json(self):
  html='<script>window.x={"variants":[{"sku":"A","title":"US 9","price":{"amount":"89.00","currencyCode":"USD"}}]}</script>'
  rows=parse(html,'https://www.notre-shop.com/products/example')
  self.assertEqual(len(rows),1)
  self.assertEqual(rows[0]['size'],'US 9')
  self.assertEqual(rows[0]['price'],'89.00')
  self.assertEqual(rows[0]['gate'],'HOLD')
 def test_patta_aggregate_offer(self):
  html='<script type="application/ld+json">{"@type":"Product","name":"Sample","brand":{"name":"Patta"},"offers":{"@type":"AggregateOffer","priceCurrency":"EUR"}}</script><script>{"variants":[{"sku":"P1","title":"M","price":6500},{"sku":"P2","title":"L","price":6500}]}</script>'
  rows=parse(html,'https://patta.nl/products/sample')
  self.assertEqual(len(rows),2)
  self.assertEqual(rows[0]['brand'],'Patta')
 def test_reject_unknown_host(self):
  with self.assertRaises(ValueError):parse('','https://example.org/')
 def test_unrecognized_structure_fails_closed(self):
  with self.assertRaises(ValueError):parse('<script>abc</script>','https://patta.nl/p')
if __name__=='__main__':unittest.main()

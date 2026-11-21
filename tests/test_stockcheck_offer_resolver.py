import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from stockcheck_offer_resolver import MerchantObservation,choose_offer
NOW='2026-11-21T15:00:00+09:00'
def obs(id='shop1',stock='IN_STOCK',price=30399,**kw):
    d=dict(offer_id=id,variation_id=100,stock=stock,checked_at=NOW,
           sale_price_jpy=price,complete_cost=True,evidence_ref='fixture:source')
    d.update(kw)
    return MerchantObservation(**d)
def ev(items,ids=('shop1',),**kw):
    a=dict(listed_jpy=30000,variation_id=100,candidate_offer_ids=ids,observations=items,now=NOW)
    a.update(kw)
    return choose_offer(**a)
class OfferTests(unittest.TestCase):
    def test_399(self): self.assertEqual((ev({'shop1':obs()}).status,ev({'shop1':obs()}).checkout_jpy),('LISTED',30000))
    def test_400(self): self.assertEqual((ev({'shop1':obs(price=30400)}).status,ev({'shop1':obs(price=30400)}).checkout_jpy),('QUOTE_CONFIRM_REQUIRED',30400))
    def test_cheaper(self): self.assertEqual(ev({'shop1':obs(price=20000)}).checkout_jpy,30000)
    def test_cheapest(self): self.assertEqual(ev({'shop1':obs(price=33000),'shop2':obs(id='shop2',price=30200)},ids=('shop1','shop2')).offer_id,'shop2')
    def test_unknown_not_oos(self): self.assertEqual(ev({'shop1':obs(stock='OUT_OF_STOCK')},ids=('shop1','shop2')).status,'UNCONFIRMED')
    def test_all_oos(self): self.assertEqual(ev({'shop1':obs(stock='OUT_OF_STOCK'),'shop2':obs(id='shop2',stock='OUT_OF_STOCK')},ids=('shop1','shop2')).status,'OUT_OF_STOCK')
    def test_no_price(self): self.assertEqual(ev({'shop1':obs(price=None)}).status,'UNCONFIRMED')
    def test_no_cost(self): self.assertEqual(ev({'shop1':obs(complete_cost=False)}).status,'UNCONFIRMED')
    def test_cached(self): self.assertEqual(ev({'shop1':obs(cached=True)}).status,'UNCONFIRMED')
    def test_wrong_variant(self): self.assertEqual(ev({'shop1':obs(variation_id=101)}).status,'UNCONFIRMED')
    def test_expired(self): self.assertEqual(ev({'shop1':obs(checked_at='2026-11-21T14:57:00+09:00')}).status,'UNCONFIRMED')
    def test_future(self): self.assertEqual(ev({'shop1':obs(checked_at='2026-11-21T15:01:00+09:00')}).status,'UNCONFIRMED')
    def test_no_evidence(self): self.assertEqual(ev({'shop1':obs(evidence_ref='')}).status,'UNCONFIRMED')
    def test_bad_price(self): self.assertEqual(ev({'shop1':obs(price=True)}).status,'UNCONFIRMED')
    def test_unknown_status(self): self.assertEqual(ev({'shop1':obs(stock='UNCONFIRMED')}).status,'UNCONFIRMED')
    def test_no_candidates(self): self.assertEqual(ev({},ids=()).status,'UNCONFIRMED')
    def test_stale_oos(self): self.assertEqual(ev({'shop1':obs(stock='OUT_OF_STOCK',checked_at='2026-11-21T14:50:00+09:00')}).status,'UNCONFIRMED')
if __name__=='__main__': unittest.main()

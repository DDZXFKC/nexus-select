import importlib.util
import json
import unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from urllib.error import URLError

spec=importlib.util.spec_from_file_location("stockcheck_core",Path(__file__).resolve().parents[1]/"tools/stockcheck_core.py")
mod=importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name]=mod
spec.loader.exec_module(mod)

URL="https://shop.example.test/p/xyz"
def mock_body(available=True,price=True):
    item={"available":available}
    if price:item["price"]={"amount":"120.00","currency":"USD"}
    return ('<script type="application/json" id="ahc-test-fixture">'+
            json.dumps({"variants":{"US 9":item}})+'</script>').encode()

class StockCheckCoreTest(unittest.TestCase):
    def make(self,outcomes):
        now=datetime(2026,11,21,tzinfo=timezone.utc)
        state={"now":now,"calls":0,"sleeps":[]}
        it=iter(outcomes)
        def fetch(_):
            state["calls"]+=1
            next_item=next(it)
            if isinstance(next_item,Exception):raise next_item
            return next_item
        def sleep(seconds):
            state["sleeps"].append(seconds)
        checker=mod.StockChecker({"shop":mod.fixture_variant_parser},fetch=fetch,
                clock=lambda:state["now"],sleep=sleep)
        return checker,state

    def test_in_stock_and_cache_same_variant(self):
        c,s=self.make([(200,mock_body())])
        x=c.check(URL,"shop",{"size":"US 9"})
        self.assertEqual((x.stock,x.current_price["currency"]),("IN_STOCK","USD"))
        self.assertTrue(c.check(URL,"shop",{"size":"US 9"}).cache_hit)
        self.assertEqual(s["calls"],1)

    def test_out_of_stock(self):
        c,_=self.make([(200,mock_body(False))])
        self.assertEqual(c.check(URL,"shop",{"size":"US 9"}).stock,"OUT_OF_STOCK")

    def test_missing_size_fails_closed(self):
        c,_=self.make([(200,mock_body())])
        x=c.check(URL,"shop",{"size":"US 10"})
        self.assertEqual((x.stock,x.reason),("UNCONFIRMED","UNREADABLE"))

    def test_price_unknown_fails_closed_and_not_cached(self):
        c,s=self.make([(200,mock_body(True,False)),(200,mock_body(True,False))])
        self.assertEqual(c.check(URL,"shop",{"size":"US 9"}).reason,"PRICE_UNKNOWN")
        self.assertFalse(c.check(URL,"shop",{"size":"US 9"}).cache_hit)
        self.assertEqual(s["calls"],2)

    def test_five_second_retry_only(self):
        c,s=self.make([(503,b""),(200,mock_body())])
        self.assertEqual(c.check(URL,"shop",{"size":"US 9"}).stock,"IN_STOCK")
        self.assertEqual(s["sleeps"],[5])

    def test_blocked_does_not_retry_or_bypass(self):
        c,s=self.make([(403,b"")])
        self.assertEqual(c.check(URL,"shop",{"size":"US 9"}).reason,"BLOCKED")
        self.assertEqual(c.check(URL,"shop",{"size":"US 9"}).reason,"BLOCKED")
        self.assertEqual(s["calls"],1)
        self.assertEqual(s["sleeps"],[])

    def test_404_out_of_stock(self):
        c,_=self.make([(404,b"")])
        self.assertEqual(c.check(URL,"shop",{"size":"US 9"}).reason,"NOT_FOUND_404")

    def test_connection_error_retries_then_final(self):
        c,s=self.make([URLError("offline"),URLError("offline")])
        self.assertEqual(c.check(URL,"shop",{"size":"US 9"}).reason,"UNREACHABLE")
        self.assertEqual(s["sleeps"],[5])

    def test_missing_parser_unreadable(self):
        c,s=self.make([(200,mock_body())])
        self.assertEqual(c.check(URL,"missing-shop",{"size":"US 9"}).reason,"UNREADABLE")

    def test_no_url_does_not_fetch(self):
        c,s=self.make([])
        self.assertEqual(c.check("","shop").reason,"NO_URL")
        self.assertEqual(s["calls"],0)

    def test_no_long_term_retry_scheduling(self):
        self.assertFalse(hasattr(mod.StockChecker,"schedule_retry"))

if __name__=="__main__":
    unittest.main()

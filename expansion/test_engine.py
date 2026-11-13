import unittest, tempfile
from pathlib import Path
from engine import Engine, canonical
class TestEngine(unittest.TestCase):
    def test_resume_and_hold(self):
        with tempfile.TemporaryDirectory() as d:
            db=Path(d)/"queue.db"
            sites={"a":{"host":"example.com","adapter":"shopify_fixture","enabled":True,"policy_review":"fixture only","currency":"USD"}}
            u="https://example.com/products/a"
            bad="https://example.com/products/b"
            snap={"currency":"USD","product":{"id":1,"vendor":"Brand","title":"Shoe","variants":[{"id":2,"size":"9","price":"100","available":True}]}}
            e=Engine(db,sites)
            e.discover("a",{"urls":[u,u,bad]})
            e.run("a",{u:snap,bad:{}})
            e.db.close()
            e=Engine(db,sites)
            e.discover("a",{"urls":[u]})
            e.run("a",{u:{}})
            self.assertEqual(len(e.export()),1)
            self.assertEqual(e.export()[0]["status"],"HOLD")
            self.assertEqual(dict(e.db.execute("SELECT url,state FROM queue")),{u:"done",bad:"hold"})
            e.db.close()
    def test_origin(self):
        with self.assertRaises(ValueError):
            canonical("https://evil.example/a","example.com")
    def test_disabled(self):
        e=Engine(":memory:",{"a":{"enabled":False}})
        with self.assertRaises(ValueError):
            e.discover("a",{"urls":[]})
        e.db.close()
if __name__=="__main__":
    unittest.main()

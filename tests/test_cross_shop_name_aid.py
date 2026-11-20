"""P1 name-aid is diagnostic only; both HOLD queues, never AUTO."""
import importlib.util
import unittest
from pathlib import Path

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("name_aid", root / "tools/cross_shop_name_aid.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class NameAidTests(unittest.TestCase):
    def test_no_color_and_legacy_both_included(self):
        corr = [{"brand":"HOKA","fl_code":"AR422710","status":"HOLD_NO_COLOR"},
                {"brand":"HOKA","fl_code":"42110519","status":"HOLD_LEGACY_NUMERIC"},
                {"brand":"HOKA","fl_code":"130BBLC","status":"AUTO"}]
        fl = [{"brand":"HOKA","code":"AR422710","name":"Hoka Bondi 7"},
              {"brand":"HOKA","code":"42110519","name":"Hoka Clifton 9"},
              {"brand":"HOKA","code":"130BBLC","name":"Hoka Bondi 7"}]
        sp = [{"brand":"HOKA","style":"422710","color":"BLK",
               "name":"Bondi 7","source_id":"sp1"},
              {"brand":"HOKA","style":"110519","color":"CHE",
               "name":"Clifton 9","source_id":"sp2"}]
        rows = mod.report(corr, fl, sp)
        self.assertEqual(set(r["fl_code"] for r in rows), {"AR422710", "42110519"})
        self.assertTrue(all(r["human_review_required"]=="1" for r in rows))
        self.assertTrue(all(r["match_status"] != "AUTO" for r in rows))
        self.assertTrue(all("HOLD_" in r["queue"] for r in rows))

    def test_no_evidence_hint_keeps_hold(self):
        rows = mod.report([{"brand":"UGG","fl_code":"2072001",
                            "status":"HOLD_LEGACY_NUMERIC"}],
                          [{"brand":"UGG","code":"2072001","name":"Unknown"}],
                          [{"brand":"UGG","style":"99999","name":"Other",
                            "source_id":"s"}])
        self.assertEqual(rows[0]["match_status"],"NO_EVIDENCED_HINT")
        self.assertEqual(rows[0]["sp_source_id"],"")

    def test_row_order_guard(self):
        with self.assertRaisesRegex(ValueError,"row order mismatch"):
            mod.report([{"brand":"UGG","fl_code":"2072001",
                         "status":"HOLD_LEGACY_NUMERIC"}],
                       [{"brand":"UGG","code":"bad"}], [])

if __name__ == "__main__":
    unittest.main()

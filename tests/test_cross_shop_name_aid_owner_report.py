"""Audit owner shortlist: coverage, counts, no auto, strict failures."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
spec=importlib.util.spec_from_file_location("owner_report",ROOT/"tools/cross_shop_name_aid_owner_report.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def sample():
    corr=[
        {"brand":"HOKA","fl_code":"AR422710","status":"HOLD_NO_COLOR"},
        {"brand":"HOKA","fl_code":"42110519","status":"HOLD_LEGACY_NUMERIC"},
        {"brand":"HOKA","fl_code":"130BBLC","status":"AUTO"}
    ]
    fl=[
        {"brand":"HOKA","code":"AR422710","name":"Bondi 7"},
        {"brand":"HOKA","code":"42110519","name":"Clifton 9"},
        {"brand":"HOKA","code":"130BBLC","name":"Bondi 7"}
    ]
    sp=[
        {"brand":"HOKA","style":"422710","name":"Bondi 7","source_id":"s1"},
        {"brand":"HOKA","style":"111111","name":"Clifton 9","source_id":"s2"}
    ]
    suggestions=[
        {"brand":"HOKA","fl_code":"AR422710","queue":"HOLD_NO_COLOR",
         "sp_source_id":"s1","sp_style":"422710","sp_color":"BLK",
         "style_suffix_hint":"1","name_overlap_tokens":"BONDI",
         "human_review_required":"1","suggestion_only":"1",
         "match_status":"UNVERIFIED_CANDIDATE"},
        {"brand":"HOKA","fl_code":"42110519","queue":"HOLD_LEGACY_NUMERIC",
         "sp_source_id":"s2","sp_style":"111111","sp_color":"CHE",
         "style_suffix_hint":"0","name_overlap_tokens":"CLIFTON",
         "human_review_required":"1","suggestion_only":"1",
         "match_status":"UNVERIFIED_CANDIDATE"}
    ]
    return corr,fl,sp,suggestions

class OwnerReportTests(unittest.TestCase):
    def test_complete_owner_report_has_no_auto(self):
        result,coverage,summary=m.prepare(*sample(),expected_holds=2)
        self.assertEqual(summary["hold_count"],2)
        self.assertEqual(summary["hold_statuses"],
                         {"HOLD_LEGACY_NUMERIC":1,"HOLD_NO_COLOR":1})
        self.assertEqual(summary["owner_review_holds"],2)
        self.assertEqual(summary["auto_adopted"],0)
        self.assertTrue(all(r["decision"]=="UNREVIEWED" for r in coverage))
        self.assertTrue(all(r["suggestion_only"]=="1" for r in result))

    def test_missing_hold_candidate_row_fails(self):
        a,b,c,d=sample()
        with self.assertRaisesRegex(ValueError,"coverage mismatch"):
            m.prepare(a,b,c,d[:1],expected_holds=2)

    def test_unauthorized_auto_flag_fails(self):
        a,b,c,d=sample()
        d[0]["suggestion_only"]="0"
        with self.assertRaisesRegex(ValueError,"authority"):
            m.prepare(a,b,c,d,expected_holds=2)

    def test_wrong_total_count_fails(self):
        with self.assertRaisesRegex(ValueError,"count changed"):
            m.prepare(*sample(),expected_holds=60)

    def test_collapsing_duplicate_hold_identity_fails(self):
        a,b,c,d=sample()
        a.append(dict(a[0]))
        b.append(dict(b[0]))
        with self.assertRaisesRegex(ValueError,"duplicate HOLD"):
            m.prepare(a,b,c,d,expected_holds=2)

if __name__=="__main__":
    unittest.main()

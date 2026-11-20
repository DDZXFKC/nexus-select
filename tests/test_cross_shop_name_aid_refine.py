"""Read-only P1 narrowing tests: all HOLDs retained, generic noise removed."""
import importlib.util
import unittest
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def load(n,p):
    spec=importlib.util.spec_from_file_location(n,root/p)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
original=load("old_aid","tools/cross_shop_name_aid.py")
refine=load("refined_aid","tools/cross_shop_name_aid_refine.py")

class RefinementTests(unittest.TestCase):
    def test_bondi_7_vs_bondi_9_and_generic_color(self):
        corr=[{"brand":"HOKA","fl_code":"AR422710","status":"HOLD_NO_COLOR"}]
        fl=[{"brand":"HOKA","code":"AR422710","name":"Hoka Bondi 7 Black"}]
        sp=[{"brand":"HOKA","style":"422710","name":"Bondi 7 White","source_id":"yes"},
            {"brand":"HOKA","style":"422711","name":"Bondi 9 Black","source_id":"wrong"},
            {"brand":"HOKA","style":"999999","name":"Black White","source_id":"noise"}]
        initial=original.report(corr,fl,sp)
        out=refine.refine(corr,fl,sp,initial)
        self.assertEqual([r["sp_source_id"] for r in out],["yes"])
        self.assertEqual(out[0]["evidence_strength"],"STYLE_SUFFIX")
        self.assertEqual(out[0]["match_status"],"HUMAN_REVIEW_CANDIDATE")
        self.assertEqual(out[0]["suggestion_only"],"1")

    def test_legacy_no_strong_candidate_must_stay_visible(self):
        corr=[{"brand":"HOKA","fl_code":"42110519","status":"HOLD_LEGACY_NUMERIC"}]
        fl=[{"brand":"HOKA","code":"42110519","name":"Hoka Black White"}]
        sp=[{"brand":"HOKA","style":"111111","name":"Hoka White Black","source_id":"weak"}]
        out=refine.refine(corr,fl,sp,original.report(corr,fl,sp))
        self.assertEqual(len(out),1)
        self.assertEqual(out[0]["match_status"],"NO_STRONG_CANDIDATE")
        self.assertEqual(out[0]["sp_source_id"],"")

    def test_max_per_row_and_no_auto(self):
        corr=[{"brand":"UGG","fl_code":"UG461450","status":"HOLD_NO_COLOR"}]
        fl=[{"brand":"UGG","code":"UG461450","name":"Ultra Mini Classic"}]
        sp=[{"brand":"UGG","style":str(100000+i),"name":"Ultra Mini","source_id":str(i)}
            for i in range(12)]
        out=refine.refine(corr,fl,sp,original.report(corr,fl,sp),max_per_fl=3)
        self.assertEqual(len(out),3)
        self.assertTrue(all(r["human_review_required"]=="1" and
                            r["match_status"] != "AUTO" for r in out))
        with self.assertRaisesRegex(ValueError,"positive"):
            refine.refine(corr,fl,sp,[],max_per_fl=0)

    def test_all_hold_rows_covered_without_hints(self):
        corr=[{"brand":"HOKA","fl_code":"AR422710","status":"HOLD_NO_COLOR"},
              {"brand":"HOKA","fl_code":"42110519","status":"HOLD_LEGACY_NUMERIC"}]
        fl=[{"brand":"HOKA","code":"AR422710","name":"A"},
            {"brand":"HOKA","code":"42110519","name":"B"}]
        out=refine.refine(corr,fl,[],[])
        self.assertEqual(len(out),2)
        self.assertTrue(all(x["match_status"]=="NO_STRONG_CANDIDATE" for x in out))

if __name__=="__main__":
    unittest.main()

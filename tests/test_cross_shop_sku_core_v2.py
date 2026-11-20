"""GLM matching v2 contract: no colors, no fuzzy match, no wrong AUTO."""
import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location(
    "match_v2",Path(__file__).resolve().parents[1]/"tools/cross_shop_sku_core_v2.py")
v2=importlib.util.module_from_spec(spec)
spec.loader.exec_module(v2)


def row(sid, sku, name="Bondi 7", brand="HOKA", code=None):
    return {"source_id":sid,"brand":brand,"sku":sku,"name":name,
            "code":code or sid}


class MatchingV2Tests(unittest.TestCase):
    def test_nfkc_case_and_separator_normalization(self):
        self.assertEqual(v2.normalize_sku("Ａｂ－１２３ / ４"),"AB1234")
        self.assertEqual(v2.normalize_sku("a.b/12 3"),"AB123")
        self.assertEqual(v2.sku_core("ＡＢ１２３－０１２"),"AB123")
        self.assertEqual(v2.sku_core("AB123/12"),"AB123")
        self.assertEqual(v2.sku_core("AB123.1"),"AB123")

    def test_non_color_suffix_remains_full_code(self):
        self.assertEqual(v2.sku_core("AB123-BLACK"),"AB123BLACK")
        self.assertEqual(v2.sku_core("AB123-1234"),"AB1231234")
        self.assertEqual(v2.sku_core("AB123"),"AB123")

    def test_color_never_blocks_AUTO(self):
        fl=[row("fl1","AB123-100","Bondi 7",code="FL123")]
        sp=[row("sp1","AB123-400","Bondi 7")]
        got=v2.evaluate(fl,sp)
        self.assertEqual(got[0]["status"],"AUTO")
        self.assertEqual(got[0]["candidate_count"],1)

    def test_name_divergence_VERIFY(self):
        got=v2.evaluate([row("f","AB123-100","Bondi 7")],
                        [row("s","AB123-400","Clifton 9")])
        self.assertEqual(got[0]["status"],"VERIFY")
        self.assertEqual(got[0]["reason"],"NAME_MODEL_CONFLICT")

    def test_generation_conflict_VERIFY(self):
        got=v2.evaluate([row("f","AB123-100","Bondi 7")],
                        [row("s","AB123-400","Bondi 9")])
        self.assertEqual(got[0]["status"],"VERIFY")
        self.assertEqual(got[0]["reason"],"NAME_MODEL_GENERATION_CONFLICT")

    def test_brand_conflict_VERIFY(self):
        got=v2.evaluate([row("f","AB123-100","Bondi 7","HOKA")],
                        [row("s","AB123-400","Bondi 7","UGG")])
        self.assertEqual(got[0]["status"],"VERIFY")
        self.assertEqual(got[0]["reason"],"BRAND_CONFLICT")

    def test_same_core_multiple_sp_is_VERIFY(self):
        got=v2.evaluate([row("f","AB123-100")],
                        [row("s1","AB123-200"),row("s2","AB123-300")])
        self.assertEqual(got[0]["status"],"VERIFY")
        self.assertEqual(got[0]["reason"],"CORE_COLLISION")
        self.assertEqual(got[0]["candidate_count"],2)

    def test_one_sp_multiple_fl_is_VERIFY(self):
        got=v2.evaluate([row("f1","AB123-100"),row("f2","AB123-300")],
                        [row("s","AB123-200")])
        self.assertEqual([x["status"] for x in got],["VERIFY","VERIFY"])

    def test_no_guess_no_edit_distance(self):
        got=v2.evaluate([row("f","AB124-100")],[row("s","AB123-100")])
        self.assertEqual(got[0]["status"],"NG")
        self.assertEqual(got[0]["reason"],"NO_EXACT_CORE")

    def test_old60_report_and_new_auto_sku_names(self):
        fl=[row("f1","AB123-100","Bondi 7",code="130BBLC"),
            row("f2","CD234-001","Clifton 9",code="42110519")]
        sp=[row("s1","AB123-200","Bondi 7"),row("s2","CD234-900","Clifton 8")]
        results=v2.evaluate(fl,sp)
        old=[{"brand":"HOKA","fl_code":"130BBLC","status":"HOLD_NO_COLOR"},
             {"brand":"HOKA","fl_code":"42110519","status":"HOLD_LEGACY_NUMERIC"}]
        changed,new_auto=v2.old_sixty_and_auto(old,results,fl)
        self.assertEqual(len(changed),2)
        self.assertEqual([x["new_status"] for x in changed],["AUTO","VERIFY"])
        self.assertEqual(len(new_auto),1)
        self.assertEqual(new_auto[0]["fl_sku"],"AB123-100")
        self.assertEqual(new_auto[0]["sp_sku"],"AB123-200")
        self.assertEqual(new_auto[0]["sp_name"],"Bondi 7")

    def test_missing_old60_explicit_fail(self):
        fl=[row("f1","AB123-100",code="130BBLC")]
        results=v2.evaluate(fl,[row("s","AB123-200")])
        old=[{"brand":"HOKA","fl_code":"130BBLC","status":"HOLD_NO_COLOR"},
             {"brand":"HOKA","fl_code":"42110519","status":"HOLD_LEGACY_NUMERIC"}]
        with self.assertRaisesRegex(ValueError,"unresolved"):
            v2.old_sixty_and_auto(old,results,fl)

    def test_unknown_sku_does_not_bypass_gate(self):
        with self.assertRaisesRegex(ValueError,"missing manufacturer SKU"):
            v2.evaluate([row("f","","Bondi 7")],[row("s","AB123")])

    def test_source_id_duplicates_rejected(self):
        with self.assertRaisesRegex(ValueError,"duplicate"):
            v2.evaluate([row("f","AB123"),row("f","AB456")],[row("s","AB123")])

if __name__=="__main__":
    unittest.main()

"""P2 diagnostics are advisory and never alter AUTO or Stage3."""
import importlib.util
import unittest
from pathlib import Path
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("p2_diag",root/"tools/cross_shop_name_note_diagnostic.py")
p2=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p2)

class NameNoteTests(unittest.TestCase):
    def test_nfkc_hyphen_case_do_not_create_false_advisory(self):
        corr=[{"brand":"NIKE","fl_code":"B0018004","status":"AUTO",
               "sp_source_id":"sp1","tags":"ADV_NAME_NOTE"}]
        fl=[{"code":"B0018004","name":"Ｎｉｋｅ Air‐Force １"}]
        sp=[{"source_id":"sp1","name":"NIKE AIR FORCE 1"}]
        rows=p2.diagnostic(corr,fl,sp)
        self.assertEqual(rows[0]["recommended_adv_name_note"],"false")
        self.assertEqual(rows[0]["normalized_name_different"],"false")
        self.assertEqual(rows[0]["existing_adv_name_note"],"true")
        self.assertEqual(corr[0]["tags"],"ADV_NAME_NOTE")

    def test_content_disagreement_is_diagnostic_not_hold(self):
        corr=[{"brand":"HOKA","fl_code":"130BBLC","status":"AUTO",
               "sp_source_id":"sp1","tags":""}]
        fl=[{"code":"130BBLC","name":"Bondi Flame"}]
        sp=[{"source_id":"sp1","name":"Clifton Heather"}]
        before=dict(corr[0])
        row=p2.diagnostic(corr,fl,sp)[0]
        self.assertEqual(row["recommended_adv_name_note"],"true")
        self.assertEqual(row["diagnostic_only"],"1")
        self.assertEqual(corr[0],before)

    def test_no_name_is_not_evidence(self):
        corr=[{"brand":"UGG","fl_code":"3236CHE","status":"AUTO",
               "sp_source_id":"sp1","tags":""}]
        fl=[{"code":"3236CHE","name":""}]
        sp=[{"source_id":"sp1","name":"Classic Mini"}]
        self.assertEqual(p2.diagnostic(corr,fl,sp)[0]["recommended_adv_name_note"],"false")

    def test_non_auto_is_skipped(self):
        corr=[{"brand":"HOKA","fl_code":"AR422710","status":"HOLD_NO_COLOR",
               "sp_source_id":"","tags":""}]
        self.assertEqual(p2.diagnostic(corr,[{"code":"AR422710"}],[]),[])

if __name__=="__main__":
    unittest.main()

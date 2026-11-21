import importlib.util
import sys
import unittest
from pathlib import Path

path=Path(__file__).resolve().parents[1]/"tools/stockcheck_inquiry_contract.py"
spec=importlib.util.spec_from_file_location("stockcheck_inquiry_contract",path)
mod=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=mod
spec.loader.exec_module(mod)

def payload(**updates):
    d={"receipt_id":"SC-20261121-001","name":"Customer","email":"customer@example.com",
       "product_id":21376,"variation_id":21377,
       "selected_variation":{"size":"US 9","color":"Black"}}
    d.update(updates)
    return d

class InquiryInputTests(unittest.TestCase):
    def test_required_name_email_and_optional_message(self):
        p=mod.parse_inquiry(payload())
        self.assertEqual((p.name,p.email,p.message),("Customer","customer@example.com",""))
        self.assertEqual(mod.parse_inquiry(payload(message="Please check")).message,"Please check")
        for x in [payload(name=""),payload(email=""),payload(email="invalid")]:
            with self.assertRaises(ValueError):mod.parse_inquiry(x)

    def test_size_comes_from_selected_variation_not_message(self):
        p=mod.parse_inquiry(payload(message="I think US 12",selected_variation={"size":"US 9","color":"Black"}))
        self.assertEqual(p.size,"US 9")
        self.assertEqual(p.color,"Black")
        with self.assertRaises(ValueError):
            mod.parse_inquiry(payload(selected_variation={"color":"Black"},message="US 12"))
        with self.assertRaises(ValueError):
            mod.parse_inquiry(payload(size="US 12"))

    def test_requires_server_resolved_variation(self):
        for p in [payload(variation_id=0),payload(selected_variation=None),
                  payload(product_id=0),payload(color="White")]:
            with self.assertRaises(ValueError):mod.parse_inquiry(p)

    def test_popup_message_is_optional_but_bounded(self):
        with self.assertRaises(ValueError):
            mod.parse_inquiry(payload(message="a"*1001))

if __name__=="__main__":
    unittest.main()

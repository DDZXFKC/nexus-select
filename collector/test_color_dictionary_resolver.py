import unittest
from color_dictionary_resolver import resolve, norm
class ColorTests(unittest.TestCase):
    def test_exact_and_preserve(self):
        d = {"phantom": {"#6E797B"}}
        self.assertEqual(resolve("Phantom","#E7E2D9",{},d),("#E7E2D9","EXISTING"))
        self.assertEqual(resolve("PHANTOM","",{},d),("#6E797B","DICTIONARY_EXACT"))
    def test_normalize(self):
        self.assertEqual(norm(" Ｍｏｓｓ   Green "), "moss green")
    def test_basic_and_ambiguous(self):
        self.assertEqual(resolve("Core Black","",{},{}),("#171717","BASIC_WORD"))
        self.assertEqual(resolve("Red Blue","",{},{}),("","AMBIGUOUS_BASIC"))
    def test_special(self):
        self.assertEqual(resolve("Multi","",{},{"multi":{"#123456"}}),("","SPECIAL"))
        self.assertEqual(resolve("NOCOLOR","",{},{}),("","SPECIAL"))
    def test_unknown_conflict(self):
        self.assertEqual(resolve("Mystery","",{},{}),("","UNKNOWN"))
        self.assertEqual(resolve("Mystery","",{},{"mystery":{"#123456","#654321"}}),("","DICTIONARY_CONFLICT"))
    def test_palette(self):
        self.assertEqual(resolve("Off Noir","",{"off noir":"#28262C"},{"off noir":{"#000000"}}),("#28262C","PALETTE_EXACT"))
if __name__ == "__main__":
    unittest.main()

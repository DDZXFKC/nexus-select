"""Tests for color_woo_export.py (run: python3 -m unittest collector/test_color_woo_export.py)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import color_woo_export as we  # noqa: E402
from test_color_fullrun import MASTER, prod  # noqa: E402


def run(row, status):
    row["swatch_status"] = status
    rows, stats, mism = we.export(MASTER, [row])
    return rows, mism


class Export(unittest.TestCase):
    def test_confirmed_gets_hex(self):
        rows, mism = run(prod("p1", ["Black", "White"], ["C-1", "C-2"]), "CONFIRMED")
        self.assertEqual([r["display_hex"] for r in rows], ["#171717", "#FFFFFF"])
        self.assertEqual(mism, [])

    def test_draft_component_blank(self):
        rows, _ = run(prod("p2", ["Black", "Brown"], ["C-1", "C-4"]), "DRAFT")
        self.assertEqual([r["display_hex"] for r in rows], ["", ""])

    def test_hold_blanks_approved_too(self):
        rows, _ = run(prod("p3", ["Black", "Volt"], ["C-1", "C-8"]), "HOLD")
        self.assertEqual([r["display_hex"] for r in rows], ["", ""])

    def test_no_components_marker(self):
        rows, _ = run(prod("p5", [], []), "UNKNOWN")
        self.assertEqual([(r["position"], r["hex_status"]) for r in rows], [(0, "NO_COMPONENTS")])

    def test_context_columns(self):
        rows, _ = run(prod("p6", ["Black"], ["C-1"]), "CONFIRMED")
        self.assertEqual((rows[0]["market"], rows[0]["colorway_original"], rows[0]["swatch_status"]),
                         ("US", "Black", "CONFIRMED"))

    def test_bad_status_raises(self):
        with self.assertRaises(we.cf.DataError):
            run(prod("p7", ["Black"], ["C-1"]), "OK")

    def test_mismatch_reported(self):
        _, mism = run(prod("p4", ["Black"], ["C-1"]), "DRAFT")
        self.assertEqual(len(mism), 1)


if __name__ == "__main__":
    unittest.main()

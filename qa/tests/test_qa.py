"""Detection tests: every intentional defect must be found, and a clean site must produce nothing.

Run:  cd qa && python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ahc_qa.__main__ import guard_report_dir, load_config  # noqa: E402
from ahc_qa.crawl import Crawler, normalize  # noqa: E402
from ahc_qa.data_checks import check_category_structure, run_data_checks  # noqa: E402
from ahc_qa.findings import Finding, FindingSet, compare_with_baseline, write_reports  # noqa: E402
from ahc_qa.purchase import host_is_safe, pick_test_products, run_purchase_checks  # noqa: E402
from mock_site import MockSite, mock_export  # noqa: E402


def cfg_for(base: str, tmp: str) -> dict:
    cfg = load_config("")
    cfg.update({"base_url": base, "allowed_hosts": ["127.0.0.1"], "purchase_allowed_hosts": ["127.0.0.1"], "report_dir": tmp})
    cfg["crawl"].update({"delay_seconds": 0, "timeout_seconds": 5})
    cfg["purchase"].update({"browsers": ["chromium"], "tracking_page_path": "/order-tracking/", "screenshot": False})
    return cfg


def types(fs) -> set:
    return {f.type for f in fs}


class DataChecks(unittest.TestCase):
    base = "http://127.0.0.1:1/"

    def run_with(self, *defects):
        cfg = cfg_for(self.base, tempfile.mkdtemp())
        return run_data_checks(mock_export(self.base, defects), cfg)

    def test_clean_has_no_findings(self):
        self.assertEqual([f.to_dict() for f in self.run_with()], [])

    def test_each_defect_is_detected(self):
        cases = {
            "noprice": ("PRICE_MISSING", "CRITICAL"),
            "varprice": ("VARIATION_PRICE_MISSING", "CRITICAL"),
            "noname": ("NAME_MISSING", "HIGH"),
            "nobrand": ("BRAND_MISSING", "HIGH"),
            "noimage": ("IMAGE_NOT_SET", "HIGH"),
            "filemissing": ("IMAGE_FILE_MISSING", "HIGH"),
            "dupsku": ("SKU_DUPLICATE", "MEDIUM"),
            "nocat": ("CATEGORY_NONE", "HIGH"),
            "gendermix": ("CATEGORY_GENDER_MIX", "REVIEW"),
            "countmismatch": ("CATEGORY_COUNT_MISMATCH", "MEDIUM"),
            "blogname": ("BRAND_RESIDUE", "HIGH"),
            "video": ("INV_PC_HERO_STATIC", "HIGH"),
        }
        for defect, (t, sev) in cases.items():
            with self.subTest(defect=defect):
                fs = self.run_with(defect)
                hit = [f for f in fs if f.type == t]
                self.assertTrue(hit, f"{defect} not detected: {types(fs)}")
                self.assertEqual(hit[0].severity, sev)

    def test_invalid_price(self):
        cfg = cfg_for(self.base, tempfile.mkdtemp())
        ex = mock_export(self.base)
        ex["products"][1]["price"] = "0"
        self.assertIn("PRICE_INVALID", types(run_data_checks(ex, cfg)))

    def test_category_structure_snapshot(self):
        tmp = tempfile.mkdtemp()
        snap = os.path.join(tmp, "cat.json")
        ex = mock_export(self.base)
        f, created = check_category_structure(ex, snap)
        self.assertTrue(created)
        self.assertEqual(f, [])
        f, _ = check_category_structure(ex, snap)
        self.assertEqual(f, [])
        ex["categories"][3]["parent"] = 11
        f, _ = check_category_structure(ex, snap)
        self.assertEqual(types(f), {"INV_CATEGORY_STRUCTURE"})


class CrawlChecks(unittest.TestCase):
    def crawl(self, defects):
        tmp = tempfile.mkdtemp()
        with MockSite(defects) as site:
            cfg = cfg_for(site.base, tmp)
            ex = mock_export(site.base)
            cr = Crawler(cfg, os.path.join(tmp, "state"), ex)
            fs = cr.run(resume=False, log=lambda *_: None)
        return fs, cr

    def test_clean_site_has_no_findings(self):
        fs, cr = self.crawl(set())
        self.assertEqual([f.to_dict() for f in fs], [])
        self.assertGreater(len(cr.pages), 8)

    def test_defects_detected(self):
        fs, _ = self.crawl({"broken", "residue", "dropdown", "video", "emptycat", "nogallery", "notitle",
                            "nohighlight", "dupitem", "alllink", "oldurl"})
        got = types(fs)
        for t in ["BROKEN_LINK", "IMAGE_BROKEN", "REDIRECT_CHAIN", "REDIRECT_LOOP", "BRAND_RESIDUE",
                  "INV_NO_HEADER_DROPDOWN", "INV_PC_HERO_STATIC", "INV_EMPTY_CATEGORY_HIDDEN",
                  "INV_PRODUCT_VERTICAL_GALLERY", "TITLE_MISSING", "CAT_CURRENT_HIGHLIGHT",
                  "CAT_LIST_DUPLICATE", "INV_NO_ALL_GROUP_LINK", "CAT_OLD_URL"]:
            self.assertIn(t, got, f"{t} missing; got {got}")
        bl = [f for f in fs if f.type == "BROKEN_LINK"][0]
        self.assertIn("リンク元", bl.location)

    def test_highlight_ok_on_paged_and_empty_pages(self):
        tmp = tempfile.mkdtemp()
        with MockSite(set()) as site:
            cfg = cfg_for(site.base, tmp)
            ex = mock_export(site.base)
            ex["categories"].append({"id": 40, "name": "SHOES", "slug": "kids-shoes", "parent": 12, "count": 0,
                                     "link": site.base + "product-category/kids/kids-shoes/"})
            cr = Crawler(cfg, os.path.join(tmp, "state"), ex)
            fs = cr.run(resume=False, log=lambda *_: None)
        self.assertIn(normalize(site.base + "product-category/mens/mens-shoes/mens-sneakers/page/2/"), cr.pages)
        self.assertNotIn("CAT_CURRENT_HIGHLIGHT", types(fs), [f.to_dict() for f in fs])

    def test_template_findings_are_aggregated_and_scheme_normalised(self):
        fs, cr = self.crawl({"residue", "scheme"})
        res = [f for f in fs if f.type == "BRAND_RESIDUE"]
        self.assertEqual(len(res), 1, [f.to_dict() for f in res])
        self.assertGreater(res[0].extra["page_count"], 5)
        self.assertIn("SCHEME_MISMATCH", types(fs))
        self.assertNotIn("FETCH_ERROR", types(fs))
        self.assertFalse(any(u.startswith("https://") for u in cr.pages))

    def test_resume(self):
        tmp = tempfile.mkdtemp()
        with MockSite(set()) as site:
            cfg = cfg_for(site.base, tmp)
            cfg["crawl"]["max_pages"] = 3
            cr = Crawler(cfg, os.path.join(tmp, "state"), mock_export(site.base))
            cr.run(resume=False, log=lambda *_: None)
            self.assertEqual(len(cr.pages), 3)
            cfg["crawl"]["max_pages"] = 1000
            cr2 = Crawler(cfg, os.path.join(tmp, "state"), mock_export(site.base))
            fs = cr2.run(resume=True, log=lambda *_: None)
            self.assertGreater(len(cr2.pages), 3)
            self.assertEqual(fs, [])

    def test_other_hosts_are_never_fetched(self):
        tmp = tempfile.mkdtemp()
        cfg = cfg_for("http://127.0.0.1:1/", tmp)
        cr = Crawler(cfg, os.path.join(tmp, "s"), {})
        with self.assertRaises(ValueError):
            cr.f.get("https://example.com/")


def spec_export(base="http://127.0.0.1:1/"):
    from ahc_qa.category_spec import expected_terms, expected_path
    terms = expected_terms()
    ids = {slug: i + 1 for i, slug in enumerate(terms)}
    cats = [{"id": ids[s], "name": s, "slug": s, "parent": ids.get(par, 0), "count": 0,
             "link": base.rstrip("/") + expected_path(s, terms)} for s, par in terms.items()]
    def prod(pid, name, slugs):
        return {"id": pid, "name": name, "category_ids": [ids[x] for x in slugs], "permalink": f"{base}product/{pid}/"}
    prods = [prod(1, "Nike Air Force 1 '07", ["mens", "mens-shoes", "mens-sneakers"]),
             prod(2, "ASICS Novablast 5", ["mens", "mens-shoes", "mens-running", "womens", "womens-shoes", "womens-running"])]
    return {"categories": cats, "products": prods}


class CategorySpec(unittest.TestCase):
    def cfg(self):
        c = cfg_for("http://127.0.0.1:1/", tempfile.mkdtemp())
        c["category_spec"] = {"enabled": True, "expected_counts": {"total": 2, "mens": 2, "womens": 1}}
        return c

    def test_spec_has_90_terms(self):
        from ahc_qa.category_spec import expected_terms
        self.assertEqual(len(expected_terms()), 90)

    def test_clean(self):
        from ahc_qa.category_spec import run_category_spec_checks
        self.assertEqual([f.to_dict() for f in run_category_spec_checks(spec_export(), self.cfg())], [])

    def test_defects(self):
        from ahc_qa.category_spec import run_category_spec_checks
        ex = spec_export()
        ex["categories"] = [c for c in ex["categories"] if c["slug"] != "kids-eyewear"]           # missing term
        bs = {c["slug"]: c for c in ex["categories"]}
        bs["womens-jeans"]["parent"] = bs["womens-shoes"]["id"]                                       # wrong parent
        bs["mens-boots"]["link"] = "http://127.0.0.1:1/product-category/mens/mens-boots/"             # old 2-level URL
        ex["categories"].append({"id": 999, "name": "Sale", "slug": "sale", "parent": 0, "count": 0, "link": ""})
        ex["products"][0]["category_ids"] = [bs["mens-sneakers"]["id"]]                               # ancestors missing
        ex["products"].append({"id": 3, "name": "Nike Dunk Low", "permalink": "",
                               "category_ids": [bs[x]["id"] for x in ("mens", "mens-shoes", "mens-basketball")]})  # facet rule
        ex["products"].append({"id": 4, "name": "Tee", "permalink": "", "category_ids": [bs["womens"]["id"]]})  # leaf missing
        got = types(run_category_spec_checks(ex, self.cfg()))
        for t in ["CAT_SPEC_MISSING", "CAT_SPEC_PARENT", "CAT_SPEC_URL", "CAT_SPEC_EXTRA", "CAT_ANCESTOR_MISSING",
                  "CAT_FACET_RULE", "CAT_LEAF_MISSING", "CAT_COUNT_EXPECTED"]:
            self.assertIn(t, got)

    def test_unisex_is_not_reported(self):
        cfg = cfg_for("http://x/", tempfile.mkdtemp())
        ex = mock_export("http://x/")
        ex["products"][1]["category_ids"] = [21, 20]  # womens-clothing + mens-shoes
        ex["categories"][3]["count"] = 2
        self.assertNotIn("CATEGORY_GENDER_MIX", types(run_data_checks(ex, cfg)))


class Baseline(unittest.TestCase):
    def test_new_existing_resolved(self):
        tmp = tempfile.mkdtemp()
        a = FindingSet()
        a.add(Finding("PRICE_MISSING", "CRITICAL", "x", product_id=1))
        a.add(Finding("BRAND_MISSING", "HIGH", "x", product_id=2))
        diff = compare_with_baseline(a, os.path.join(tmp, "baseline.json"))
        paths = write_reports(a, tmp, {"base_url": "x", "checks": []}, diff)
        os.replace(paths["json"], os.path.join(tmp, "baseline.json"))
        b = FindingSet()
        b.add(Finding("PRICE_MISSING", "CRITICAL", "wording changed", product_id=1))
        b.add(Finding("NAME_MISSING", "HIGH", "x", product_id=3))
        diff = compare_with_baseline(b, os.path.join(tmp, "baseline.json"))
        self.assertEqual((diff["new"], diff["existing"], len(diff["resolved"])), (1, 1, 1))
        out = write_reports(b, os.path.join(tmp, "r2"), {"base_url": "x", "checks": []}, diff)
        with open(out["html"], encoding="utf-8") as fh:
            self.assertIn("新規", fh.read())


class Safety(unittest.TestCase):
    def test_purchase_host_gate(self):
        self.assertTrue(host_is_safe("http://kaitsuke-shop.local/", ["kaitsuke-shop.local"]))
        self.assertFalse(host_is_safe("https://after-hours-club.com/", ["after-hours-club.com"]))
        self.assertFalse(host_is_safe("https://lyrical-tooth.localsite.io/", ["lyrical-tooth.localsite.io"]))
        self.assertFalse(host_is_safe("http://kaitsuke-shop.local/", []))

    def test_production_purchase_is_skipped(self):
        tmp = tempfile.mkdtemp()
        cfg = cfg_for("https://after-hours-club.com/", tmp)
        cfg["purchase_allowed_hosts"] = ["after-hours-club.com"]
        fs = run_purchase_checks(cfg, mock_export("https://after-hours-club.com/"), tmp)
        self.assertEqual([f.type for f in fs], ["PURCHASE_SKIPPED"])

    def test_report_dir_inside_repo_refused(self):
        here = os.path.dirname(os.path.abspath(__file__))
        with self.assertRaises(SystemExit):
            guard_report_dir(os.path.join(here, "reports"))
        guard_report_dir(tempfile.mkdtemp())

    def test_pick_products(self):
        ex = mock_export("http://x/")
        self.assertEqual({p["type"] for p in pick_test_products(ex)}, {"variable", "simple"})


def _browser_ok():
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch().close()
        return True
    except Exception:
        return False


@unittest.skipUnless(_browser_ok(), "Playwright Chromium not available")
class PurchaseFlow(unittest.TestCase):
    def flow(self, defects):
        tmp = tempfile.mkdtemp()
        with MockSite(defects) as site:
            cfg = cfg_for(site.base, tmp)
            # mock host is 127.0.0.1, which the hard gate allows
            fs = run_purchase_checks(cfg, mock_export(site.base), os.path.join(tmp, "shots"), log=lambda *_: None)
        return fs

    def test_clean_flow(self):
        fs = self.flow(set())
        self.assertEqual([f.to_dict() for f in fs], [])

    def test_defects(self):
        fs = self.flow({"badtotal", "shipping"})
        msgs = " ".join(f.message for f in fs)
        self.assertIn("小計", msgs)
        self.assertIn("送料", msgs)

    def test_wrong_item_in_cart(self):
        fs = self.flow({"wrongitem"})
        self.assertTrue(any("カートの中身" in f.message for f in fs), [f.message for f in fs])

    def test_add_disabled(self):
        fs = self.flow({"addbroken"})
        self.assertTrue(any("ADD TO BAG" in f.message for f in fs), [f.message for f in fs])


if __name__ == "__main__":
    unittest.main()

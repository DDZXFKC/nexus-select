"""Checks against the owner-confirmed category hierarchy (AFTER HOURS CLUB カテゴリー階層設計).

Structure: 3 genders x 4 groups x 25 leaves.
  root  : {gender}                 e.g. mens
  group : {gender}-{group}         e.g. mens-shoes
  leaf  : {gender}-{leaf_key}      e.g. mens-sneakers   (slugs kept from the two-level era)
URL    : /product-category/{gender}/{gender}-{group}/{gender}-{leaf}/
Old URL: /product-category/{gender}/{gender}-{leaf}/  -> 301 to the new URL

Read-only: these checks only report. They never change categories.
"""
from __future__ import annotations

import re
import urllib.parse

from .findings import Finding

GENDERS = ["mens", "womens", "kids"]
GENDER_LABEL = {"mens": "MEN'S", "womens": "WOMEN'S", "kids": "KIDS"}
GROUPS = ["shoes", "clothing", "headwear", "accessories"]
# leaf key -> (group, display name). Keys match nexus-catnav-autoclassify.php / nexus-catnav-redirects.php.
LEAVES = {
    "sneakers": ("shoes", "Sneakers"), "running": ("shoes", "Running"), "basketball": ("shoes", "Basketball"),
    "boots": ("shoes", "Boots"), "sandals": ("shoes", "Sandals & Slides"),
    "tshirt": ("clothing", "T-Shirts"), "ls-tshirts": ("clothing", "Long Sleeve T-Shirts"), "shirts": ("clothing", "Shirts"),
    "polo": ("clothing", "Polo Shirts"), "hoodie": ("clothing", "Hoodies"), "sweatshirts": ("clothing", "Sweatshirts"),
    "knitwear": ("clothing", "Knitwear"), "jacket": ("clothing", "Jackets"), "pants": ("clothing", "Pants"),
    "jeans": ("clothing", "Jeans"), "shorts": ("clothing", "Shorts"),
    "cap": ("headwear", "Caps"), "beanies": ("headwear", "Beanies"), "hats": ("headwear", "Hats"),
    "bag": ("accessories", "Bags"), "wallets": ("accessories", "Wallets"), "jewelry": ("accessories", "Jewelry"),
    "socks": ("accessories", "Socks"), "belts": ("accessories", "Belts"), "eyewear": ("accessories", "Eyewear"),
}
# Use-based leaves must not be assigned to these models without evidence (spec §11).
FACET_LEAVES = {"running", "basketball"}
FACET_EXCLUDE = re.compile(r"Air Force|AF1|\bDunk\b", re.I)


def expected_terms() -> dict[str, str]:
    """slug -> expected parent slug ('' for roots). 3 + 12 + 75 = 90 terms."""
    out: dict[str, str] = {}
    for g in GENDERS:
        out[g] = ""
        for grp in GROUPS:
            out[f"{g}-{grp}"] = g
        for key, (grp, _) in LEAVES.items():
            out[f"{g}-{key}"] = f"{g}-{grp}"
    return out


def expected_path(slug: str, terms: dict[str, str]) -> str:
    chain, cur = [], slug
    while cur:
        chain.append(cur)
        cur = terms.get(cur, "")
    return "/product-category/" + "/".join(reversed(chain)) + "/"


def run_category_spec_checks(data: dict, cfg: dict) -> list[Finding]:
    spec_cfg = cfg.get("category_spec", {})
    if not spec_cfg.get("enabled", True):
        return []
    out: list[Finding] = []
    cats = data.get("categories", [])
    by_slug = {c["slug"]: c for c in cats}
    by_id = {c["id"]: c for c in cats}
    terms = expected_terms()

    # 1. every expected term exists with the expected parent and URL
    for slug, parent in terms.items():
        c = by_slug.get(slug)
        if not c:
            out.append(Finding("CAT_SPEC_MISSING", "HIGH", "設計にあるカテゴリーがデータベースにありません（内部には全カテゴリーを作る仕様）",
                               location=slug, evidence=f"親: {parent or '（第1階層）'}", cause_group="CAT_SPEC_MISSING"))
            continue
        actual_parent = by_id.get(c["parent"], {}).get("slug", "") if c["parent"] else ""
        if actual_parent != parent:
            out.append(Finding("CAT_SPEC_PARENT", "HIGH", "カテゴリーの親が設計と違います",
                               location=slug, evidence=f"設計: {parent or '（第1階層）'} / 現在: {actual_parent or '（第1階層）'}"))
        if c.get("link"):
            path = urllib.parse.urlsplit(c["link"]).path
            if not path.endswith(expected_path(slug, terms)):
                out.append(Finding("CAT_SPEC_URL", "HIGH", "カテゴリーのURLが設計の階層になっていません",
                                   location=slug, page_url=c["link"], evidence=f"設計: {expected_path(slug, terms)}"))
    # 2. extra terms
    for c in cats:
        if c["slug"] not in terms and c["slug"] != "uncategorized":
            out.append(Finding("CAT_SPEC_EXTRA", "REVIEW", "設計にないカテゴリーがあります", judge="人",
                               location=c["slug"], page_url=c.get("link", ""), evidence=c["name"]))

    # 3. per product: root + group + leaf assigned (spec §9), facet rule (spec §11)
    for p in data.get("products", []):
        slugs = {by_id[i]["slug"] for i in p.get("category_ids", []) if i in by_id}
        base = dict(product_id=p["id"], product_name=p.get("name", ""), page_url=p.get("permalink", ""))
        missing = set()
        for s in slugs:
            cur = terms.get(s, "")
            while cur:
                if cur not in slugs:
                    missing.add(cur)
                cur = terms.get(cur, "")
        if missing:
            out.append(Finding("CAT_ANCESTOR_MISSING", "HIGH", "下層カテゴリーに登録されているのに、親カテゴリーが付いていません（第1〜第3階層をすべて付ける仕様）",
                               location=", ".join(sorted(missing)), evidence=", ".join(sorted(slugs)), cause_group="CAT_ANCESTOR_MISSING", **base))
        for g in GENDERS:
            if g in slugs and not any(s.startswith(f"{g}-") and s[len(g) + 1:] in LEAVES for s in slugs):
                out.append(Finding("CAT_LEAF_MISSING", "MEDIUM", f"{GENDER_LABEL[g]}に登録されていますが、末端カテゴリー（Sneakersなど）が付いていません",
                                   location=g, evidence=", ".join(sorted(slugs)), cause_group=f"CAT_LEAF_MISSING:{g}", **base))
        name = p.get("name", "")
        for s in slugs:
            key = s.split("-", 1)[1] if "-" in s else ""
            if key in FACET_LEAVES and FACET_EXCLUDE.search(name):
                out.append(Finding("CAT_FACET_RULE", "HIGH", f"根拠なく{LEAVES[key][1]}に分類されている可能性があります（AF1・Dunkなどは用途カテゴリーに入れない）",
                                   location=s, evidence=name, cause_group=f"CAT_FACET_RULE:{key}", **base))

    # 4. expected counts (spec §13: 197 / 149 / 48 maintained). Published parent products.
    exp = spec_cfg.get("expected_counts") or {}
    prods = data.get("products", [])
    actual = {"total": len(prods)}
    for g in GENDERS:
        gid = by_slug.get(g, {}).get("id")
        actual[g] = sum(1 for p in prods if gid in p.get("category_ids", [])) if gid else 0
    for k, v in exp.items():
        if k in actual and actual[k] != v:
            label = "総商品数" if k == "total" else GENDER_LABEL.get(k, k)
            out.append(Finding("CAT_COUNT_EXPECTED", "HIGH", f"{label}の商品数が想定と違います（想定 {v} / 現在 {actual[k]}）。商品を追加・削除した場合は設定の expected_counts を更新してください",
                               location=k, evidence=f"想定 {v} / 現在 {actual[k]}"))
    return out


def old_category_urls(data: dict, base_url: str) -> list[tuple[str, str, str]]:
    """(old_url, expected_new_url, slug) for each leaf that exists in the DB."""
    out = []
    for c in data.get("categories", []):
        slug = c["slug"]
        for g in GENDERS:
            if slug.startswith(f"{g}-") and slug[len(g) + 1:] in LEAVES and c.get("link"):
                old = urllib.parse.urljoin(base_url, f"product-category/{g}/{slug}/")
                out.append((old, c["link"], slug))
    return out

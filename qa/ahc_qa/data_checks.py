"""Checks run on the read-only WooCommerce export (qa/export/ahc_export.php)."""
from __future__ import annotations

import json
import os
from collections import defaultdict

from .findings import Finding


def _num(v):
    if v in (None, ""):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return "invalid"


class CategoryTree:
    def __init__(self, categories: list[dict], products: list[dict]):
        self.by_id = {c["id"]: c for c in categories}
        self.children = defaultdict(list)
        for c in categories:
            self.children[c["parent"]].append(c["id"])
        self.direct = defaultdict(int)
        for p in products:
            for cid in p.get("category_ids", []):
                self.direct[cid] += 1
        self._subtree_cache: dict[int, set] = {}

    def root_of(self, cid: int) -> dict | None:
        seen = set()
        c = self.by_id.get(cid)
        while c and c["parent"] and c["parent"] in self.by_id and c["id"] not in seen:
            seen.add(c["id"])
            c = self.by_id[c["parent"]]
        return c

    def path(self, cid: int) -> str:
        names, seen = [], set()
        c = self.by_id.get(cid)
        while c and c["id"] not in seen:
            seen.add(c["id"])
            names.append(c["name"])
            c = self.by_id.get(c["parent"])
        return " > ".join(reversed(names))

    def subtree_product_ids(self, cid: int, products: list[dict]) -> set:
        if cid in self._subtree_cache:
            return self._subtree_cache[cid]
        ids = {cid}
        stack = [cid]
        while stack:
            for ch in self.children.get(stack.pop(), []):
                if ch not in ids:
                    ids.add(ch)
                    stack.append(ch)
        prods = {p["id"] for p in products if set(p.get("category_ids", [])) & ids}
        self._subtree_cache[cid] = prods
        return prods


def load_export(path: str) -> dict:
    with open(os.path.expanduser(path), encoding="utf-8") as fh:
        return json.load(fh)


def run_data_checks(data: dict, cfg: dict) -> list[Finding]:
    out: list[Finding] = []
    products = data.get("products", [])
    cats = data.get("categories", [])
    images = {i["id"]: i for i in data.get("images", [])}
    tree = CategoryTree(cats, products)
    pmin, pmax = cfg["price"]["min"], cfg["price"]["max"]
    gender_slugs = set(cfg.get("gender_root_slugs", []))
    residue = [s.lower() for s in cfg.get("brand_residue_patterns", [])]

    # --- site level
    site = data.get("site", {})
    for field in ("blogname", "blogdescription"):
        val = site.get(field) or ""
        if any(r in val.lower() for r in residue):
            out.append(Finding("BRAND_RESIDUE", "HIGH", f"WordPressの設定（{field}）に旧ブランド名が残っています",
                               location=f"設定 → 一般 → {'サイトのタイトル' if field == 'blogname' else 'キャッチフレーズ'}",
                               evidence=val, cause_group="BRAND_RESIDUE:wp-settings"))
    if site.get("theme_mods", {}).get("nexus_pc_hero_video"):
        out.append(Finding("INV_PC_HERO_STATIC", "HIGH", "PCヒーローに動画が設定されています（確定事項：静止画のみ）",
                           location="テーマ設定 nexus_pc_hero_video", evidence=f"attachment id {site['theme_mods']['nexus_pc_hero_video']}"))

    # --- products
    sku_map = defaultdict(list)
    for p in products:
        pid, name = p["id"], (p.get("name") or "").strip()
        base = dict(product_id=pid, product_name=name, page_url=p.get("permalink", ""))
        if not name:
            out.append(Finding("NAME_MISSING", "HIGH", "商品名が空です", **base))
        if not p.get("brands"):
            out.append(Finding("BRAND_MISSING", "HIGH", "ブランド（pa_brand）が設定されていません", **base))
        if not p.get("description_length") and not p.get("short_description_length"):
            out.append(Finding("DESCRIPTION_MISSING", "MEDIUM", "商品説明が空です", **base))

        if p.get("type") == "variable":
            vs = [v for v in p.get("variations", []) if v.get("status") == "publish"]
            if not vs:
                out.append(Finding("VARIABLE_NO_VARIATIONS", "CRITICAL", "公開中のバリエーションがなく、購入できません", **base))
            for v in vs:
                vp = _num(v.get("price"))
                loc = "バリエーション " + ", ".join(f"{k}={val}" for k, val in (v.get("attributes") or {}).items())
                if vp is None:
                    out.append(Finding("VARIATION_PRICE_MISSING", "CRITICAL", "バリエーションに価格がありません",
                                       location=loc, evidence=f"variation {v['id']}", cause_group="PRICE", **base))
                elif vp == "invalid" or vp < pmin or vp > pmax:
                    out.append(Finding("PRICE_INVALID", "HIGH", f"バリエーションの価格が範囲外です（{pmin}〜{pmax}）",
                                       location=loc, evidence=str(v.get("price")), cause_group="PRICE", **base))
                elif v.get("stock_status") == "instock" and not v.get("purchasable"):
                    out.append(Finding("VARIATION_NOT_PURCHASABLE", "HIGH", "在庫ありなのに購入できない設定です",
                                       location=loc, evidence=f"variation {v['id']}", **base))
                if v.get("sku"):
                    sku_map[v["sku"]].append((pid, name, v["id"]))
        else:
            pr = _num(p.get("price"))
            if pr is None:
                out.append(Finding("PRICE_MISSING", "CRITICAL", "価格がありません", cause_group="PRICE", **base))
            elif pr == "invalid" or pr < pmin or pr > pmax:
                out.append(Finding("PRICE_INVALID", "HIGH", f"価格が範囲外です（{pmin}〜{pmax}）",
                                   evidence=str(p.get("price")), cause_group="PRICE", **base))

        if p.get("sku"):
            sku_map[p["sku"]].append((pid, name, None))
        elif p.get("type") != "variable":
            out.append(Finding("SKU_MISSING", "LOW", "SKUが空です", **base))

        # images
        if not p.get("image_id"):
            out.append(Finding("IMAGE_NOT_SET", "HIGH", "メイン画像が登録されていません", **base))
        for iid in [p.get("image_id")] + list(p.get("gallery_ids") or []):
            img = images.get(iid)
            if not img:
                continue
            if not img.get("exists"):
                out.append(Finding("IMAGE_FILE_MISSING", "HIGH", "画像ファイルがサーバーにありません",
                                   image_url=img.get("url", ""), evidence=img.get("file", ""), **base))
            for sname, s in (img.get("sizes") or {}).items():
                if not s.get("exists"):
                    out.append(Finding("IMAGE_SIZE_FILE_MISSING", "MEDIUM", f"縮小画像（{sname}）のファイルがありません",
                                       image_url=img.get("url", ""), location=sname, evidence=s.get("file", ""),
                                       cause_group="IMAGE_SIZE_FILE_MISSING", **base))

        # categories
        cids = p.get("category_ids") or []
        real = [c for c in cids if c in tree.by_id and tree.by_id[c]["slug"] != "uncategorized"]
        if not real:
            out.append(Finding("CATEGORY_NONE", "HIGH", "カテゴリーが設定されていません（または未分類のみ）", **base))
        roots = {tree.root_of(c)["slug"] for c in real if tree.root_of(c)}
        groots = sorted(roots & gender_slugs)
        # Unisex items belong to both MEN'S and WOMEN'S with one product ID (spec §9): not a defect.
        if "kids" in groots and len(groots) > 1:
            out.append(Finding("CATEGORY_GENDER_MIX", "REVIEW", "KIDSと大人用の両方のカテゴリーに登録されています",
                               judge="人", evidence=" / ".join(tree.path(c) for c in real), location=",".join(groots), **base))

    for sku, owners in sku_map.items():
        if len(owners) > 1:
            for pid, name, vid in owners:
                out.append(Finding("SKU_DUPLICATE", "MEDIUM", f"SKU「{sku}」が{len(owners)}か所で使われています",
                                   product_id=pid, product_name=name, location=f"variation {vid}" if vid else "",
                                   evidence=sku, cause_group=f"SKU_DUPLICATE:{sku}"))

    for c in cats:
        direct = tree.direct.get(c["id"], 0)
        if c["count"] != direct:
            out.append(Finding("CATEGORY_COUNT_MISMATCH", "MEDIUM",
                               f"カテゴリーの登録数（{c['count']}）と、実際に公開中の商品数（{direct}）が一致しません",
                               page_url=c.get("link", ""), location=tree.path(c["id"]),
                               evidence=f"term {c['id']} {c['slug']}"))
    return out


def category_snapshot(data: dict) -> list[dict]:
    return sorted(({"id": c["id"], "slug": c["slug"], "name": c["name"], "parent": c["parent"]}
                   for c in data.get("categories", [])), key=lambda c: c["id"])


def check_category_structure(data: dict, snapshot_path: str) -> tuple[list[Finding], bool]:
    """Compare the category tree with the owner-confirmed snapshot.

    Returns (findings, created). The first run saves the snapshot and reports nothing.
    The snapshot is only ever created, never overwritten by this tool.
    """
    cur = category_snapshot(data)
    if not os.path.exists(snapshot_path):
        os.makedirs(os.path.dirname(snapshot_path), exist_ok=True)
        with open(snapshot_path, "w", encoding="utf-8") as fh:
            json.dump(cur, fh, ensure_ascii=False, indent=2)
        return [], True
    with open(snapshot_path, encoding="utf-8") as fh:
        base = {c["id"]: c for c in json.load(fh)}
    now = {c["id"]: c for c in cur}
    out = []
    for cid, c in now.items():
        b = base.get(cid)
        if not b:
            out.append(Finding("INV_CATEGORY_STRUCTURE", "HIGH", "確定形にないカテゴリーが追加されています",
                               location=c["slug"], evidence=json.dumps(c, ensure_ascii=False)))
        elif (b["slug"], b["parent"], b["name"]) != (c["slug"], c["parent"], c["name"]):
            out.append(Finding("INV_CATEGORY_STRUCTURE", "HIGH", "カテゴリーの名前・スラッグ・親が確定形から変わっています",
                               location=c["slug"], evidence=f"確定形 {b['name']}/{b['slug']}/親{b['parent']} → 現在 {c['name']}/{c['slug']}/親{c['parent']}"))
    for cid, b in base.items():
        if cid not in now:
            out.append(Finding("INV_CATEGORY_STRUCTURE", "HIGH", "確定形にあるカテゴリーが削除されています",
                               location=b["slug"], evidence=json.dumps(b, ensure_ascii=False)))
    return out, False

#!/usr/bin/env python3
"""Shoe Palace color decomposition: P0 fixes of docs/color-fullrun-generate-2026-11-19.py.

Assigned to Claude by GPT review caafbc5 / b5c5027 (Muse confirmation 2026-11-19 09:30).
Owner decision 965d6d3: one color master shared by all brands (normalized name = key).
Existing BRAND/PRODUCT rows are kept until migration is confirmed and are honoured
only for their own brand/product.

Two commands (both offline; nothing writes to the sheet):
  recompute  Sheet export (2 tabs) -> recompute derived columns only (swatch status /
             swatch hex / search families) with the new rules. Protected columns
             (ids, colorway, components, manual statuses) are copied, never rebuilt.
             Output: product rows, change list, integrity issues, summary.
             This is what Muse's dry-run (55a4d82) is compared with row by row.
  generate   v8 products.csv + raw JSON + current FULL master -> candidates for products
             not yet in the sheet, plus new master rows (COMMON only, stable ids).

Swatch status (case B, caafbc5), first min(3, n) components only, in this order:
  HOLD      colorway_status HOLD_CONTRADICTION; a displayed component with a missing /
            unknown color_id, token mismatch, scope of another brand/product; or a
            displayed color whose hex_status is CONFLICT.
  UNKNOWN   no components; a displayed slot without a valid #RRGGBB; special tokens
            (multi, multicolor, ...).
  DRAFT     all displayed hex valid, at least one not APPROVED_APPROX.
  CONFIRMED all displayed hex valid and APPROVED_APPROX.
  family_status is NOT a condition.
"""
import argparse
import csv
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

HEX = re.compile(r"#[0-9A-Fa-f]{6}\Z")
ID = re.compile(r"C-\d+\Z")
SPECIAL = {"multi", "multicolor", "multi color", "multi-color", "nocolor", "no color",
           "assorted", "clear", "transparent", "none", "unknown"}
APPROVED = "APPROVED_APPROX"
DERIVED = ["swatch_hex_1", "swatch_hex_2", "swatch_hex_3", "swatch_status",
           "search_families_json", "search_families_candidates_json", "search_families_conflict_json"]
# Output-only diagnostics (never written back, never in changes.csv).
DIAGNOSTIC = ["diag_swatch_reason"]


class DataError(ValueError):
    """Input that must not be silently accepted."""


def norm(value):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value or "").casefold()).strip()


def norm_brand(value):
    return norm(value).replace(" ", "")


# ---------------------------------------------------------------- master
def is_active(row):
    return (row.get("active") or "TRUE").strip().upper() in ("TRUE", "1", "YES")


class Master:
    """Validated color master. Raises on bad ids, duplicate ids, duplicate scope keys.

    Inactive rows (merged/retired) stay in by_id so old references are reported as
    INACTIVE_MASTER_ROW, but they are excluded from by_key: lookup never assigns them and
    they may share a scope key with the active row that replaced them."""

    def __init__(self, rows):
        self.by_id, self.by_key = {}, {}
        for r in rows:
            cid = (r.get("color_id") or "").strip()
            if not ID.fullmatch(cid):
                raise DataError(f"bad color_id: {cid!r}")
            if cid in self.by_id:
                raise DataError(f"duplicate color_id: {cid}")
            key = self.key(r.get("scope_type"), r.get("scope_key"), r.get("token_normalized"))
            if not key[2]:
                raise DataError(f"empty token for {cid}")
            self.by_id[cid] = r
            if not is_active(r):
                continue
            if key in self.by_key:
                raise DataError(f"duplicate scope key: {key} ({self.by_key[key]['color_id']}, {cid})")
            self.by_key[key] = r

    @staticmethod
    def key(scope_type, scope_key, token):
        st = (scope_type or "").strip().upper()
        sk = (scope_key or "").strip()
        if st == "BRAND":
            sk = norm_brand(sk)
        elif st == "COMMON":
            sk = "*"
        return (st, sk, norm(token))

    def lookup(self, token, brand, product_key=None):
        """PRODUCT row for this product, else BRAND row of this brand, else COMMON."""
        n = norm(token)
        for k in ((("PRODUCT", product_key, n),) if product_key else ()) + (
                ("BRAND", norm_brand(brand), n), ("COMMON", "*", n)):
            if k in self.by_key:
                return self.by_key[k]
        return None

    def next_id(self):
        return max((int(c[2:]) for c in self.by_id), default=0) + 1


def product_key(row):
    return "|".join((row.get("shop_code", ""), row.get("market", ""),
                     row.get("supplier_product_id", ""), row.get("supplier_color_key", "")))


def ref_problem(comp, master, brand, pkey):
    """Integrity of one component reference: None if fine, else a reason code."""
    cid = comp.get("color_id")
    if not cid:
        return "NULL_ID"
    m = master.by_id.get(cid)
    if m is None:
        return "ID_NOT_IN_MASTER"
    if not is_active(m):
        return "INACTIVE_MASTER_ROW"
    if norm(m.get("token_normalized")) != norm(comp.get("token_original")):
        return "TOKEN_MISMATCH"
    st, sk, _ = Master.key(m.get("scope_type"), m.get("scope_key"), m.get("token_normalized"))
    if st == "BRAND" and sk != norm_brand(brand):
        return "OTHER_BRAND_SCOPE"
    if st == "PRODUCT" and sk != pkey:
        return "OTHER_PRODUCT_SCOPE"
    if st not in ("COMMON", "BRAND", "PRODUCT"):
        return "BAD_SCOPE_TYPE"
    return None


def swatch(row, master):
    """Return (status, [hex1, hex2, hex3], reasons, all_component_issues)."""
    comps = json.loads(row.get("components_json") or "[]")
    if not isinstance(comps, list):
        raise DataError(f"components_json not a list: {row.get('supplier_product_id')}")
    positions = [c.get("position") for c in comps]
    if positions != list(range(1, len(comps) + 1)):
        raise DataError(f"component order broken: {row.get('supplier_product_id')} {positions}")
    brand, pkey = row.get("brand_id", ""), product_key(row)
    issues = [(c["position"], p) for c in comps if (p := ref_problem(c, master, brand, pkey))]
    # Row consistency: component_count and the original colorway must match the components.
    original = [t.strip() for t in (row.get("colorway_original") or "").split("/") if t.strip()]
    if [norm(t) for t in original] != [norm(c.get("token_original")) for c in comps]:
        issues.append((0, "COLORWAY_COMPONENTS_MISMATCH"))
    if (row.get("component_count") or str(len(comps))) != str(len(comps)):
        issues.append((0, "COMPONENT_COUNT_MISMATCH"))
    shown = comps[:3]
    hexes, reasons = [], []
    hold = row.get("colorway_status") == "HOLD_CONTRADICTION"
    if hold:
        reasons.append("HOLD_CONTRADICTION")
    row_issues = [p for pos, p in issues if pos == 0]
    if row_issues:
        hold = True
        reasons.extend(row_issues)
    unknown = not comps
    if unknown:
        reasons.append("NO_COMPONENTS")
    draft = False
    for c in shown:
        problem = ref_problem(c, master, brand, pkey)
        m = master.by_id.get(c.get("color_id")) if not problem else None
        if problem:
            hold = True
            reasons.append(f"SLOT{c['position']}:{problem}")
            hexes.append("")
            continue
        if (m.get("hex_status") or "").strip() == "CONFLICT":
            hold = True
            reasons.append(f"SLOT{c['position']}:HEX_CONFLICT")
            hexes.append("")
            continue
        if norm(m.get("token_normalized")) in SPECIAL:
            unknown = True
            reasons.append(f"SLOT{c['position']}:SPECIAL")
            hexes.append("")
            continue
        hx = (m.get("display_hex") or "").strip()
        if not HEX.fullmatch(hx):
            unknown = True
            reasons.append(f"SLOT{c['position']}:NO_VALID_HEX")
            hexes.append("")
            continue
        hexes.append(hx.upper())
        if (m.get("hex_status") or "").strip() != APPROVED:
            draft = True
    hexes += [""] * (3 - len(hexes))
    status = "HOLD" if hold else "UNKNOWN" if unknown else "DRAFT" if draft else "CONFIRMED"
    if status != "CONFIRMED":
        hexes = [h if status == "DRAFT" else "" for h in hexes]
    return status, hexes, reasons, issues


def families(row, master):
    """Search families: confirmed / candidate / conflict kept apart (all components)."""
    confirmed, candidates, conflict = [], [], []
    for c in json.loads(row.get("components_json") or "[]"):
        m = master.by_id.get(c.get("color_id"))
        if not m or ref_problem(c, master, row.get("brand_id", ""), product_key(row)):
            continue
        fam = (m.get("family_internal") or "").strip()
        if not fam:
            continue
        fs = m.get("family_status")
        target = confirmed if fs == "CONFIRMED" else conflict if fs == "CONFLICT" else candidates
        if fam not in target:
            target.append(fam)
    return (confirmed, [f for f in candidates if f not in confirmed],
            [f for f in conflict if f not in confirmed])


# ---------------------------------------------------------------- recompute
def recompute(master_rows, product_rows):
    master = Master(master_rows)
    seen, out, changes, integrity = set(), [], [], []
    counts = Counter()
    for row in product_rows:
        pid = row.get("supplier_product_id", "")
        key = product_key(row)
        if not pid:
            raise DataError("product row without supplier_product_id")
        if key in seen:
            raise DataError(f"duplicate product row: {key}")
        seen.add(key)
        status, hexes, reasons, issues = swatch(row, master)
        conf, cand, confl = families(row, master)
        new = dict(row)
        new.update({"swatch_hex_1": hexes[0], "swatch_hex_2": hexes[1], "swatch_hex_3": hexes[2],
                    "swatch_status": status,
                    "search_families_json": json.dumps(conf, ensure_ascii=False),
                    "search_families_candidates_json": json.dumps(cand, ensure_ascii=False),
                    "search_families_conflict_json": json.dumps(confl, ensure_ascii=False),
                    "diag_swatch_reason": ";".join(reasons)})
        for col in DERIVED:
            if (row.get(col) or "") != (new.get(col) or ""):
                changes.append({"supplier_product_id": pid, "column": col,
                                "before": row.get(col) or "", "after": new.get(col) or ""})
        for pos, problem in issues:
            integrity.append({"supplier_product_id": pid, "position": pos, "problem": problem})
        counts[f"swatch_status:{status}"] += 1
        counts[f"transition:{row.get('swatch_status') or '-'}->{status}"] += 1
        out.append(new)
    return out, changes, integrity, dict(sorted(counts.items()))


# ---------------------------------------------------------------- generate
NON_COLOR = re.compile(r"\b(\d+\s*(pack|pk|pcs?|ct)|pack|set|size|one size|limit|qty|edition|"
                       r"gs|ps|td|xs|s|m|l|xl|xxl|\d{4})\b", re.I)
KNOWN_SUFFIX = re.compile(r"\s*(free shipping|limit \d+)\s*$", re.I)


def slug(text):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", norm(text))).strip("-")


def title_rule_ok(title, candidate, handle, tag_families, token_families):
    """TITLE_CANDIDATE -> CONFIRMED_BY_TITLE_RULE only when (c4aac99c):
    last parenthesis of the title (known suffix allowed after it) equals the candidate,
    handle ends with the candidate's slug at a '-' boundary, the candidate is not a
    non-color text, and no contradiction with the store's Color_ tags."""
    t = KNOWN_SUFFIX.sub("", title or "").rstrip()
    m = re.search(r"\(([^()]*)\)\s*$", t)
    if not m or norm(m.group(1)) != norm(candidate):
        return False
    s = slug(candidate)
    h = (handle or "").lower()
    if not s or not (h == s or h.endswith("-" + s)):
        return False
    if NON_COLOR.search(candidate):
        return False
    known = [f for f in token_families if f]
    if tag_families and known and not set(known) & set(tag_families):
        return False
    return True


def generate(products, raw_by_id, master_rows, existing_keys, observed_at, shop_code, market):
    """Candidates for products not in the sheet. New master rows are COMMON only.
    shop_code/market are explicit (no default store); every product in products.csv must
    belong to that store. Only supplier_color_key 'single' (1 product id = 1 color) is
    supported; stores with several colors per product id need their own key contract."""
    if not shop_code or not market:
        raise DataError("shop_code and market are required")
    master = Master(master_rows)
    next_id = master.next_id()
    new_master, rows = [], []
    token_products = defaultdict(set)
    token_instock = defaultdict(set)
    ids = [p.get("product_id", "") for p in products]
    dup = [i for i, c in Counter(ids).items() if c > 1]
    if dup:
        raise DataError(f"duplicate product ids in products.csv: {dup[:5]}")
    for p in products:
        pid = p.get("product_id", "")
        if not pid:
            raise DataError("product row without product_id")
        if pid not in raw_by_id:
            raise DataError(f"raw missing for product {pid}")
        if str(raw_by_id[pid].get("id")) != pid:
            raise DataError(f"raw id mismatch for {pid}")
    for p in products:
        pid, brand = p["product_id"], p.get("brand", "")
        pkey = f"{shop_code}|{market}|{pid}|single"
        if pkey in existing_keys:
            continue
        raw = raw_by_id[pid]
        tags = raw.get("tags") or []
        cw = (p.get("color_name") or "").strip()
        toks = [(o.strip(), norm(o)) for o in cw.split("/") if o.strip()] if cw else []
        comps = []
        for o, n in toks:
            m = master.lookup(n, brand, pkey)
            if m is None:
                m = {"color_id": f"C-{next_id}", "scope_type": "COMMON", "scope_key": "*",
                     "token_normalized": n, "token_original": o, "family_internal": "",
                     "display_hex": "", "family_status": "UNKNOWN", "hex_status": "UNKNOWN",
                     "source_type": "AUTO_NEW_TOKEN", "checked_at": observed_at[:10], "active": "TRUE"}
                next_id += 1
                master = Master(list(master.by_id.values()) + [m])
                new_master.append(m)
            comps.append({"position": len(comps) + 1, "token_original": o, "color_id": m["color_id"]})
            token_products[m["color_id"]].add(pid)
            if p.get("in_stock") == "True":
                token_instock[m["color_id"]].add(pid)
        status = p.get("color_name_status", "")
        if status == "TITLE_CANDIDATE":
            tag_fams = {t[6:].casefold() for t in tags if t.startswith("Color_")}
            tok_fams = [(master.lookup(n, brand, pkey) or {}).get("family_internal", "") for _, n in toks]
            status = ("CONFIRMED_BY_TITLE_RULE"
                      if title_rule_ok(p.get("title_original"), cw, raw.get("handle"), tag_fams, tok_fams)
                      else "TITLE_CANDIDATE")
        elif not cw:
            status = "UNKNOWN"
        row = {"shop_code": shop_code, "market": market, "supplier_product_id": pid,
               "supplier_color_key": "single", "brand_id": brand,
               "colorway_original": cw, "colorway_status": status,
               "components_json": json.dumps(comps, ensure_ascii=False),
               "component_count": str(len(comps)), "source_url": p.get("source_url", ""),
               "store_color_tags_json": json.dumps([t for t in tags if t.startswith("Color_")]),
               "store_main_color_tags_json": json.dumps([t for t in tags if t.startswith("MAIN_COLOR_")]),
               "observed_at": observed_at}
        row["component_count"] = str(len(comps))
        st, hexes, reasons, _ = swatch(row, master)
        conf, cand, confl = families(row, master)
        # A single main family only when every component resolved to one family;
        # CONFIRMED only when every component's family_status is CONFIRMED.
        cms = [master.by_id[c["color_id"]] for c in comps]
        fams = [(x.get("family_internal") or "") for x in cms]
        single = bool(fams) and all(fams) and len(set(fams)) == 1
        main_status = ("" if not single else "CONFIRMED" if all(x.get("family_status") == "CONFIRMED" for x in cms)
                       else "DRAFT")
        row.update({"swatch_hex_1": hexes[0], "swatch_hex_2": hexes[1], "swatch_hex_3": hexes[2],
                    "swatch_status": st, "diag_swatch_reason": ";".join(reasons),
                    "search_families_json": json.dumps(conf, ensure_ascii=False),
                    "search_families_candidates_json": json.dumps(cand, ensure_ascii=False),
                    "search_families_conflict_json": json.dumps(confl, ensure_ascii=False),
                    "main_family_internal": fams[0] if single else "",
                    "main_family_status": main_status})
        rows.append(row)
    stats = [{"color_id": cid, "distinct_products": len(v), "distinct_in_stock": len(token_instock[cid])}
             for cid, v in sorted(token_products.items())]
    return rows, new_master, stats


def load_raw(pages):
    """Raw contract: every product needs a non-empty id. The same id twice with IDENTICAL
    content (page overlap) is accepted and counted; different content stops the run."""
    raw_by_id, dups = {}, 0
    for page in pages:
        for p in page.get("products", []):
            pid = str(p.get("id") or "").strip()
            if not pid:
                raise DataError("raw product without id")
            if pid in raw_by_id:
                if raw_by_id[pid] != p:
                    raise DataError(f"conflicting raw records for {pid}")
                dups += 1
                continue
            raw_by_id[pid] = p
    return raw_by_id, dups


# ---------------------------------------------------------------- io
def read_table(path):
    """CSV with header, or the sheet JSON export (list of rows, first row = header)."""
    path = Path(path)
    if path.suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        head = data[0]
        return [dict(zip(head, r + [""] * (len(head) - len(r)))) for r in data[1:]]
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields=None):
    fields = fields or (list(rows[0].keys()) if rows else [])
    with Path(path).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def digest(rows):
    h = hashlib.sha256()
    for r in rows:
        h.update(json.dumps(r, sort_keys=True, ensure_ascii=False).encode())
    return h.hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("recompute")
    r.add_argument("--master", required=True)
    r.add_argument("--products", required=True)
    r.add_argument("--output", required=True, type=Path)
    g = sub.add_parser("generate")
    g.add_argument("--master", required=True)
    g.add_argument("--sheet-products", required=True)
    g.add_argument("--v8-products", required=True)
    g.add_argument("--raw-dir", required=True, type=Path)
    g.add_argument("--observed-at", help="raw batch time; default = raw dir name YYYYMMDD_HHMMSS")
    g.add_argument("--shop-code", required=True)
    g.add_argument("--market", required=True)
    g.add_argument("--output", required=True, type=Path)
    a = ap.parse_args(argv)
    a.output.mkdir(parents=True, exist_ok=False)
    master_rows = read_table(a.master)
    if a.cmd == "recompute":
        products = read_table(a.products)
        first = recompute(master_rows, products)
        second = recompute(master_rows, products)
        if digest(first[0]) != digest(second[0]):
            raise DataError("rerun mismatch")
        out, changes, integrity, counts = first
        fields = list(products[0].keys()) if products else []
        fields += [c for c in DERIVED + DIAGNOSTIC if c not in fields]
        write_csv(a.output / "product_color_recomputed.csv", out, fields)
        write_csv(a.output / "changes.csv", changes, ["supplier_product_id", "column", "before", "after"])
        write_csv(a.output / "integrity_issues.csv", integrity, ["supplier_product_id", "position", "problem"])
        summary = {"products": len(out), "changes": len(changes), "integrity_issues": len(integrity),
                   "hash": digest(out), "rerun_match": True, "counts": counts}
    else:
        raw_by_id, raw_dups = load_raw([json.loads(fn.read_text(encoding="utf-8"))
                                        for fn in sorted(a.raw_dir.glob("page_*.json"))])
        observed = a.observed_at
        if not observed:
            m = re.fullmatch(r"(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})", a.raw_dir.name)
            if not m:
                raise DataError("--observed-at required (raw dir name is not YYYYMMDD_HHMMSS)")
            observed = "{}-{}-{}T{}:{}:{}".format(*m.groups())
        existing = {product_key(r) for r in read_table(a.sheet_products)}
        products = read_table(a.v8_products)
        rows, new_master, stats = generate(products, raw_by_id, master_rows, existing, observed,
                                           a.shop_code, a.market)
        rows2, new_master2, _ = generate(products, raw_by_id, master_rows, existing, observed,
                                         a.shop_code, a.market)
        if digest(rows) != digest(rows2) or digest(new_master) != digest(new_master2):
            raise DataError("rerun mismatch")
        write_csv(a.output / "product_color_new.csv", rows)
        write_csv(a.output / "color_master_new.csv", new_master)
        write_csv(a.output / "color_id_distinct_counts.csv", stats,
                  ["color_id", "distinct_products", "distinct_in_stock"])
        summary = {"new_products": len(rows), "new_master": len(new_master), "hash": digest(rows),
                   "raw_identical_duplicates": raw_dups,
                   "rerun_match": True, "observed_at": observed,
                   "counts": dict(Counter(f"swatch_status:{r['swatch_status']}" for r in rows))}
    (a.output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except DataError as e:
        print(f"DATA ERROR: {e}", file=sys.stderr)
        sys.exit(2)

"""Pick swatch-check fixtures from the products that really exist in Local.

Input: woo_components.csv (collector/color_woo_export.py) and a file of Local SP products,
one "supplier_product_id,status" per line (status = publish/draft). Only DRAFT products are
used (GPT 5dc4c1b: no writes to published Local products in the first fixture run).
Output: one id per check category (1/2/3/4+ colors, repeated color, UNKNOWN, special Multi,
HOLD, no components) as an allowlist (--out). Categories with no Local draft are filled from
the sheet with products that are NOT in Local, written to --fixtures-out as
"supplier_product_id,colorway_original" for tools/ahc_create_swatch_fixture.php (FX-SP- drafts).
Run: python3 tools/pick_swatch_fixtures.py --components woo_components.csv --local-ids sp_local_ids.txt --out fixtures.txt
"""
import argparse
import csv
from collections import defaultdict

CATS = ["1色", "2色", "3色", "4色以上", "同色反復", "未確定", "特殊色Multi", "HOLD", "構成色なし"]


def category_hits(rows):
    st = rows[0]["swatch_status"]
    comps = sorted((r for r in rows if r["position"] != "0"), key=lambda r: int(r["position"]))
    names = [r["token_original"].strip().lower() for r in comps]
    n = len(comps)
    hits = []
    if not comps:
        hits.append("構成色なし")
    if st == "CONFIRMED":
        hits += {1: ["1色"], 2: ["2色"], 3: ["3色"]}.get(n, ["4色以上"] if n >= 4 else [])
        if n >= 2 and len(set(names)) < n:
            hits.append("同色反復")
    if st == "UNKNOWN" and comps and not any(x.startswith("multi") for x in names):
        hits.append("未確定")
    if any(x.startswith("multi") for x in names):
        hits.append("特殊色Multi")
    if st == "HOLD":
        hits.append("HOLD")
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--components", required=True)
    ap.add_argument("--local-ids", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--fixtures-out", required=True)
    a = ap.parse_args()
    status = {}
    for x in open(a.local_ids, encoding="utf-8"):
        if x.strip():
            pid, st = (x.strip().split(",") + [""])[:2]
            status[pid] = st
    local = [p for p, st in status.items() if st == "draft"]
    groups = defaultdict(list)
    with open(a.components, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            groups[r["supplier_product_id"]].append(r)
    picked = {}
    for pid in local:
        if pid not in groups:
            continue
        for c in category_hits(groups[pid]):
            picked.setdefault(c, pid)
    fixture = {}
    for pid in sorted(groups):
        if pid in status:
            continue
        for c in category_hits(groups[pid]):
            if c not in picked:
                fixture.setdefault(c, pid)
    ids, fx = [], []
    for c in CATS:
        if c in picked:
            pid, where = picked[c], "Local下書き"
        elif c in fixture:
            pid, where = fixture[c], "FIXTURE作成"
        else:
            pid, where = None, "シートにも該当なし"
        print(f"{c}\t{where}\t{pid or ''}\t{groups[pid][0]['colorway_original'] if pid else ''}")
        if pid and pid not in ids:
            ids.append(pid)
            if where == "FIXTURE作成":
                fx.append(pid)
    missing = sum(1 for p in local if p not in groups)
    print(f"local_sp={len(status)} drafts={len(local)} drafts_in_sheet={len(local) - missing} allowlist={len(ids)} fixtures_to_create={len(fx)}")
    with open(a.out, "w", encoding="utf-8") as f:
        f.write("\n".join(ids) + "\n")
    with open(a.fixtures_out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["supplier_product_id", "colorway_original"])
        for pid in fx:
            w.writerow([pid, groups[pid][0]["colorway_original"]])


if __name__ == "__main__":
    main()

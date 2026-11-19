"""Pick swatch-check fixtures from the products that really exist in Local.

Input: woo_components.csv (collector/color_woo_export.py) and a file of supplier_product_ids
present in Local (one per line, from the SP-<id> parent SKUs). Output: one id per check
category (1/2/3/4+ colors, repeated color, UNKNOWN, special Multi, HOLD, no components),
printed with the category, and written to --out as an allowlist file.
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
    a = ap.parse_args()
    local = [x.strip() for x in open(a.local_ids, encoding="utf-8") if x.strip()]
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
    ids = []
    for c in CATS:
        pid = picked.get(c)
        print(f"{c}\t{pid or '（Localに該当なし）'}\t{groups[pid][0]['colorway_original'] if pid else ''}")
        if pid and pid not in ids:
            ids.append(pid)
    missing = sum(1 for p in local if p not in groups)
    print(f"local_ids={len(local)} in_sheet={len(local) - missing} not_in_sheet={missing} fixtures={len(ids)}")
    with open(a.out, "w", encoding="utf-8") as f:
        f.write("\n".join(ids) + "\n")


if __name__ == "__main__":
    main()

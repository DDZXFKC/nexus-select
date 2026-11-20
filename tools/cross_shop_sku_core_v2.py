#!/usr/bin/env python3
"""GLM 2026-11-20 matching v2: strict SKU core equality, color never a gate.

Independent from legacy cross_shop_corr.py (v1 is superseded). Pure CSV tool,
no production writes, no fuzzy matching or guesswork. Every FL/input row gets a
decision; GLM must inspect all newly AUTO pairs before activation.
"""
import argparse
import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

VERSION = "cross-shop-sku-core-v2"
SEPARATORS = re.compile(r"[-/\s.]+")
# One to three decimal color digits, separated from the base SKU.
COLOR_SUFFIX = re.compile(r"^(.+?)[-/\s.]+(\d{1,3})$")
ALIASES = {"HOKA": "HOKA", "HOKA ONE ONE": "HOKA", "UGG": "UGG",
           "VANS": "VANS", "NIKE": "NIKE"}
WEAK_TOKENS = frozenset(("NIKE", "VANS", "UGG", "HOKA", "ONE", "SHOE",
                         "SHOES", "SNEAKER", "SNEAKERS", "THE", "FOR",
                         "MEN", "MENS", "WOMEN", "WOMENS", "KIDS",
                         "BLACK", "WHITE", "GREY", "GRAY", "BLUE",
                         "BROWN", "RED", "PINK", "GREEN", "TAN", "BEIGE",
                         "LOW", "HIGH", "MID", "SIZE", "COLOR", "COLOUR"))
RESULT_FIELDS = ("fl_source_id", "fl_sku", "fl_name", "brand", "sku_core",
                 "status", "reason", "candidate_count", "sp_source_id",
                 "sp_sku", "sp_name", "sp_name_raw", "fl_name_raw")
OLD_FIELDS = ("fl_source_id", "fl_sku", "fl_name", "old_status",
              "new_status", "new_reason", "new_sku_core", "new_sp_source_id",
              "new_sp_sku", "new_sp_name")
NEW_AUTO_FIELDS = ("fl_source_id", "fl_sku", "fl_name",
                   "sp_source_id", "sp_sku", "sp_name", "sku_core")


def canonical(raw):
    return unicodedata.normalize("NFKC", str(raw or "")).strip().upper()


def normalize_sku(raw):
    return SEPARATORS.sub("", canonical(raw))


def sku_core(raw):
    value = canonical(raw)
    # Strip ONLY an explicitly separated decimal suffix with length 1..3.
    # Do not extrapolate to embedded digits, alphabetic color codes or longer suffixes.
    match = COLOR_SUFFIX.fullmatch(value)
    if match and normalize_sku(match.group(1)):
        return normalize_sku(match.group(1))
    return normalize_sku(value)


def brand_norm(raw):
    key = " ".join(canonical(raw).split())
    if key not in ALIASES:
        raise ValueError("unapproved brand: " + str(raw))
    return ALIASES[key]


def tokens(name):
    normalized = canonical(name)
    return {word for word in re.findall(r"[A-Z0-9]+", normalized)
            if word not in WEAK_TOKENS and (len(word) >= 3 or word.isdigit())}


def name_conflict(fl, sp):
    """Conservative detector, not a positive match requirement.

    Contradictory brands or disjoint non-generic model words => VERIFY. No
    substantive names on either side => no positive evidence of conflict.
    """
    if brand_norm(fl["brand"]) != brand_norm(sp["brand"]):
        return "BRAND_CONFLICT"
    a, b = tokens(fl.get("name")), tokens(sp.get("name"))
    if a and b and not (a & b):
        return "NAME_MODEL_CONFLICT"
    return ""


def validate(rows, label):
    if not rows:
        raise ValueError(label + " source corpus empty")
    ids = set()
    for idx, row in enumerate(rows, 1):
        for field in ("source_id", "brand", "sku", "name"):
            if field not in row:
                raise ValueError(label + " missing field " + field)
        sid = str(row["source_id"]).strip()
        if not sid or sid in ids:
            raise ValueError(label + " missing/duplicate source_id line " + str(idx))
        ids.add(sid)
        brand_norm(row["brand"])
        if not sku_core(row["sku"]):
            raise ValueError(label + " missing manufacturer SKU line " + str(idx))
        if not isinstance(row["name"], str):
            raise ValueError(label + " invalid name line " + str(idx))


def evaluate(fl_rows, sp_rows):
    """One result per FL row, no deletion or deduplication of multiple SKUs."""
    validate(fl_rows, "FL")
    validate(sp_rows, "SP")
    index = defaultdict(list)
    for sp in sp_rows:
        index[(brand_norm(sp["brand"]), sku_core(sp["sku"]))].append(sp)
    output = []
    for fl in fl_rows:
        brand, core = brand_norm(fl["brand"]), sku_core(fl["sku"])
        candidates = index.get((brand, core), [])
        record = {
            "fl_source_id": fl["source_id"], "fl_sku": fl["sku"],
            "fl_name": fl["name"], "fl_name_raw": fl["name"],
            "sp_name_raw": "", "brand": brand, "sku_core": core,
            "status": "NG", "reason": "NO_EXACT_CORE", "candidate_count": len(candidates),
            "sp_source_id": "", "sp_sku": "", "sp_name": "",
        }
        if len(candidates) > 1:
            record.update(status="VERIFY", reason="CORE_COLLISION")
        elif len(candidates) == 1:
            sp = candidates[0]
            issue = name_conflict(fl, sp)
            record.update(status="VERIFY" if issue else "AUTO",
                          reason=issue or "EXACT_CORE",
                          sp_source_id=sp["source_id"], sp_sku=sp["sku"],
                          sp_name=sp["name"], sp_name_raw=sp["name"])
        output.append(record)
    # A single supplier row may not be AUTO for two different FL source rows.
    by_sp = defaultdict(list)
    for out in output:
        if out["status"] == "AUTO":
            by_sp[out["sp_source_id"]].append(out)
    for group in by_sp.values():
        if len(group) > 1:
            for item in group:
                item["status"], item["reason"] = "VERIFY", "REVERSE_COLLISION"
    return output


def old_sixty_and_auto(old_rows, current, fl_rows, old_holds=("HOLD_NO_COLOR", "HOLD_LEGACY_NUMERIC")):
    """Old 60 rows are addressed via exact FL source identity, no fuzzy joins."""
    # v1 corr CSV stores brand+fl_code without source_id; map ONLY by exact
    # brand+original FL listing code. Never substitute manufacturer SKU or name.
    fl_code_to_id = {}
    for fl in fl_rows:
        brand = brand_norm(fl["brand"])
        raw_code = canonical(fl.get("code", ""))
        if not raw_code:
            raise ValueError("FL code required for old-v1 join: " + fl["source_id"])
        key = (brand, raw_code)
        if key in fl_code_to_id:
            raise ValueError("duplicate FL legacy code " + repr(key))
        fl_code_to_id[key] = fl["source_id"]
    old_index = {}
    unresolved_old = []
    for r in old_rows:
        if r.get("source_id", r.get("fl_source_id", "")):
            sid = str(r.get("source_id", r.get("fl_source_id")))
        else:
            key = (brand_norm(r["brand"]), canonical(r["fl_code"]))
            sid = fl_code_to_id.get(key, "")
        if not sid:
            unresolved_old.append((r.get("brand", ""), r.get("fl_code", "")))
            continue
        if sid in old_index:
            raise ValueError("duplicate v1 mapping for FL source " + sid)
        old_index[sid] = r
    if unresolved_old:
        raise ValueError("v1 rows unresolved by exact FL code: " + repr(unresolved_old))
    current_ids = {r["fl_source_id"] for r in current}
    missing = sorted(s for s, r in old_index.items()
                     if r.get("status", r.get("old_status")) in old_holds and s not in current_ids)
    if missing:
        raise ValueError("old HOLD rows missing in v2: " + repr(missing))
    changed, new_auto = [], []
    for r in current:
        prior = old_index.get(r["fl_source_id"])
        previous = prior.get("status", prior.get("old_status")) if prior else "NOT_IN_V1"
        if previous in old_holds:
            changed.append({
                "fl_source_id": r["fl_source_id"], "fl_sku": r["fl_sku"],
                "fl_name": r["fl_name"], "old_status": previous,
                "new_status": r["status"], "new_reason": r["reason"],
                "new_sku_core": r["sku_core"], "new_sp_source_id": r["sp_source_id"],
                "new_sp_sku": r["sp_sku"], "new_sp_name": r["sp_name"],
            })
        if r["status"] == "AUTO" and (not prior or previous != "AUTO" or
                    prior.get("sp_source_id", "") != r["sp_source_id"]):
            new_auto.append({field: r[field] for field in NEW_AUTO_FIELDS})
    return changed, new_auto


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as fp:
        return list(csv.DictReader(fp))


def write_csv(path, rows, fields):
    target = Path(path)
    if target.exists():
        raise ValueError("refuse overwrite " + str(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fields, extrasaction="ignore",
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--fl", required=True, help="All FL rows, with verified manufacturer SKU")
    p.add_argument("--sp", required=True, help="All SP corpus incl. unsellable")
    p.add_argument("--v1", required=True, help="Original v1 corr CSV with stable FL ID")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--expected-old-holds", type=int, default=60)
    args = p.parse_args()
    paths = (args.fl, args.sp, args.v1)
    fl, sp, old = (read_csv(x) for x in paths)
    results = evaluate(fl, sp)
    old_sixty, new_auto = old_sixty_and_auto(old, results, fl)
    if len(old_sixty) != args.expected_old_holds:
        raise ValueError("old HOLD coverage mismatch: " + str(len(old_sixty)))
    folder = Path(args.out_dir)
    for name in ("matching-v2-all.csv", "matching-v2-old60.csv",
                 "matching-v2-new-auto.csv", "matching-v2-summary.json"):
        if (folder / name).exists():
            raise ValueError("refuse overwrite existing " + name)
    counts = Counter(r["status"] for r in results)
    old_counts = Counter(r["new_status"] for r in old_sixty)
    summary = {"schema": VERSION, "fl_rows": len(fl), "sp_rows": len(sp),
               "old_hold_rows": len(old_sixty), "statuses": dict(counts),
               "old60_destinations": dict(old_counts), "new_auto_count": len(new_auto),
               "input_sha256": {name: hashlib.sha256(Path(path).read_bytes()).hexdigest()
                                for name, path in zip(("fl", "sp", "v1"), paths)},
               "rule": "SKU_CORE_EXACT_ONLY; COLOR_IGNORED; NAMES_CONFLICT_ONLY",
               "glM_review": "PENDING: zero wrong AUTO required"}
    folder.mkdir(parents=True, exist_ok=True)
    write_csv(folder / "matching-v2-all.csv", results, RESULT_FIELDS)
    write_csv(folder / "matching-v2-old60.csv", old_sixty, OLD_FIELDS)
    write_csv(folder / "matching-v2-new-auto.csv", new_auto, NEW_AUTO_FIELDS)
    (folder / "matching-v2-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()

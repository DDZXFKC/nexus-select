#!/usr/bin/env python3
"""GLM P1 human-only evidence queue for NO_COLOR and LEGACY.

NEVER updates corr, manual seed, AUTO, Stage3 or shop listings.
Provides diagnostic candidate reports, not implied matching authority.
"""
import argparse
import csv
import json
import re
import unicodedata
from pathlib import Path


def norm(value):
    return unicodedata.normalize("NFKC", str(value or "")).upper().strip()


def tokens(value):
    return set(re.findall(r"[A-Z]{2,}|[0-9]{2,}", norm(value)))


def numeric_runs(value):
    return re.findall(r"\d{3,}", norm(value))


def candidates_for(corr_row, fl_row, sp_rows):
    """Diagnostic rank, not eligibility or matching predicate."""
    if corr_row["status"] not in ("HOLD_NO_COLOR", "HOLD_LEGACY_NUMERIC"):
        return []
    brand = norm(corr_row["brand"])
    fl_code = norm(corr_row["fl_code"])
    fl_name = tokens(fl_row.get("name", ""))
    numbers = numeric_runs(fl_code)
    candidates = []
    for sp in sp_rows:
        if norm(sp.get("brand")) != brand:
            continue
        style = norm(sp.get("style", ""))
        name_overlap = sorted(fl_name & tokens(sp.get("name", "")))
        style_hint = any(len(n) >= 3 and (style.endswith(n) or n.endswith(style))
                         for n in numbers if style)
        if not name_overlap and not style_hint:
            continue
        candidates.append({
            "fl_code": fl_code, "brand": brand,
            "queue": corr_row["status"],
            "sp_source_id": sp.get("source_id", ""),
            "sp_style": style, "sp_color": norm(sp.get("color", "")),
            "style_suffix_hint": "1" if style_hint else "0",
            "name_overlap_tokens": "|".join(name_overlap),
            "human_review_required": "1",
            "suggestion_only": "1",
            "match_status": "UNVERIFIED_CANDIDATE",
        })
    return sorted(candidates, key=lambda row: (
        -int(row["style_suffix_hint"]),
        -len(row["name_overlap_tokens"].split("|")) if row["name_overlap_tokens"] else 0,
        row["sp_source_id"],
    ))


FIELDS = ("brand", "fl_code", "queue", "sp_source_id", "sp_style", "sp_color",
          "style_suffix_hint", "name_overlap_tokens",
          "human_review_required", "suggestion_only", "match_status")


def load(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def report(corr_rows, fl_rows, sp_rows):
    if len(corr_rows) != len(fl_rows):
        raise ValueError("corr/FL row count mismatch")
    rows = []
    for corr, fl in zip(corr_rows, fl_rows):
        if norm(corr["fl_code"]) != norm(fl["code"]):
            raise ValueError("FL row order mismatch")
        if corr["status"] not in ("HOLD_NO_COLOR", "HOLD_LEGACY_NUMERIC"):
            continue
        hints = candidates_for(corr, fl, sp_rows)
        if hints:
            rows.extend(hints)
        else:
            rows.append({
                "brand": norm(corr["brand"]), "fl_code": norm(corr["fl_code"]),
                "queue": corr["status"], "sp_source_id": "", "sp_style": "",
                "sp_color": "", "style_suffix_hint": "0",
                "name_overlap_tokens": "", "human_review_required": "1",
                "suggestion_only": "1", "match_status": "NO_EVIDENCED_HINT",
            })
    return rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--corr", required=True)
    p.add_argument("--fl", required=True)
    p.add_argument("--sp-full-corpus", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    rows = report(load(args.corr), load(args.fl), load(args.sp_full_corpus))
    dest = Path(args.out)
    if dest.exists():
        raise ValueError("will not overwrite existing file")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("x", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"rows": len(rows),
                      "all_human_review_required": True,
                      "auto_or_manual_mapping_written": False},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()

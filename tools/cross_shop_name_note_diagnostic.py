#!/usr/bin/env python3
"""P2 read-only ADV_NAME_NOTE diagnostic refinement.

No mutation of AUTO, Stage3, tags or identity_key. Recommendations, not gates.
A core change that alters AUTO output requires GLM re-review separately.
"""
import argparse
import csv
import json
import re
import unicodedata
from pathlib import Path

STOP = frozenset(("HOKA", "UGG", "VANS", "NIKE", "WHITE", "BLACK",
                  "GREY", "GRAY", "MEN", "WOMEN", "MENS", "WOMENS",
                  "SHOE", "SHOES", "SNEAKER", "SNEAKERS", "COLOR",
                  "COLOUR", "THE", "AND", "WITH", "FOR"))
FIELDS = ("brand", "fl_code", "sp_source_id", "status",
          "raw_name_different", "normalized_name_different",
          "fl_content_tokens", "sp_content_tokens",
          "shared_content_tokens", "content_overlap",
          "recommended_adv_name_note", "existing_adv_name_note",
          "diagnostic_only")


def normalize_name(raw):
    name = unicodedata.normalize("NFKC", str(raw or "")).upper()
    name = re.sub(r"[-‐–−ー_/]+", " ", name)
    return " ".join(name.split())


def content_tokens(raw):
    return {x for x in re.findall(r"[A-Z0-9]+", normalize_name(raw))
            if x not in STOP and (len(x) >= 2 or x.isdigit())}


def diagnostic(corr_rows, fl_rows, sp_rows, threshold=0.4):
    """Jaccard threshold does not alter matching or adoption."""
    if not 0 <= threshold <= 1:
        raise ValueError("threshold outside [0,1]")
    if len(corr_rows) != len(fl_rows):
        raise ValueError("corr/FL count mismatch")
    sp_map = {r["source_id"]: r for r in sp_rows}
    if len(sp_map) != len(sp_rows):
        raise ValueError("duplicate SP source id")
    out = []
    for c, fl in zip(corr_rows, fl_rows):
        if c["fl_code"] != str(fl.get("code", "")).strip().upper():
            raise ValueError("FL row mismatch")
        if c.get("status") != "AUTO":
            continue
        sp = sp_map.get(c["sp_source_id"])
        if sp is None:
            raise ValueError("AUTO references unknown SP source id: " + c["sp_source_id"])
        a = str(fl.get("name", ""))
        b = str(sp.get("name", ""))
        ta, tb = content_tokens(a), content_tokens(b)
        shared = ta & tb
        overlap = len(shared) / len(ta | tb) if (ta | tb) else 1.0
        # Absence of either name is insufficient evidence to warn.
        flag = bool(a.strip() and b.strip() and ta and tb and overlap < threshold)
        out.append({
            "brand": c["brand"], "fl_code": c["fl_code"],
            "sp_source_id": c["sp_source_id"], "status": "AUTO",
            "raw_name_different": str(a != b).lower(),
            "normalized_name_different": str(normalize_name(a) != normalize_name(b)).lower(),
            "fl_content_tokens": "|".join(sorted(ta)),
            "sp_content_tokens": "|".join(sorted(tb)),
            "shared_content_tokens": "|".join(sorted(shared)),
            "content_overlap": f"{overlap:.4f}",
            "recommended_adv_name_note": str(flag).lower(),
            "existing_adv_name_note": str("ADV_NAME_NOTE" in
                                          c.get("tags", "").split("|")).lower(),
            "diagnostic_only": "1",
        })
    return out


def load(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def main():
    p = argparse.ArgumentParser()
    for arg in ("corr", "fl", "sp-full-corpus", "out"):
        p.add_argument("--" + arg, required=True)
    p.add_argument("--threshold", type=float, default=0.4)
    args = p.parse_args()
    rows = diagnostic(load(args.corr), load(args.fl),
                      load(args.sp_full_corpus), args.threshold)
    dest = Path(args.out)
    if dest.exists():
        raise ValueError("refusing overwrite")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("x", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"diagnostics": len(rows), "modified_auto_or_stage3": False}))


if __name__ == "__main__":
    main()

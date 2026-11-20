#!/usr/bin/env python3
"""Conservative read-only triage of P1 name-aid suggestions.

Input is the already verified suggestion-only report plus full SP corpus and
aligned FL/corr rows. No AUTO, manual mappings or matching-core modifications.
Preserves all 60 HOLD rows, even if no candidate survives strict evidence gates.
"""
import argparse
import csv
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

# Generic color/brand/product terms cannot, alone, justify owner review.
WEAK = frozenset(("HOKA", "UGG", "VANS", "NIKE", "ONE", "SHOE", "SHOES",
                  "SNEAKER", "SNEAKERS", "MEN", "WOMEN", "MENS", "WOMENS",
                  "BLACK", "WHITE", "GREY", "GRAY", "BLUE", "BROWN",
                  "PINK", "RED", "GREEN", "BEIGE", "TAN", "COLOR", "COLOUR",
                  "LOW", "HIGH", "MID", "CLASSIC", "ORIGINAL", "NEW"))


def canon(value):
    s = unicodedata.normalize("NFKC", str(value or "")).upper()
    return re.sub(r"[-‐–−ー_/]+", " ", s)


def title_features(value):
    s = canon(value)
    words = re.findall(r"[A-Z0-9]+", s)
    distinctive = {v for v in words if len(v) >= 3 and v not in WEAK and not v.isdigit()}
    generations = set()
    # Names must retain a SINGLE numeric model generation, e.g. BONDI 7.
    for a, b in zip(words, words[1:]):
        if a not in WEAK and re.fullmatch(r"\d{1,2}", b):
            generations.add((a, b))
    return distinctive, generations, set(words)


def refine(corr_rows, fl_rows, sp_rows, suggestions, max_per_fl=5):
    if len(corr_rows) != len(fl_rows):
        raise ValueError("unaligned FL/corr input")
    if max_per_fl < 1:
        raise ValueError("max_per_fl must be positive")
    sp_map = {r["source_id"]: r for r in sp_rows}
    if len(sp_map) != len(sp_rows):
        raise ValueError("duplicate SP source IDs")
    hints = defaultdict(list)
    for row in suggestions:
        if row.get("queue") not in ("HOLD_NO_COLOR", "HOLD_LEGACY_NUMERIC"):
            raise ValueError("candidate not HOLD queue")
        if row.get("human_review_required") != "1" or row.get("suggestion_only") != "1":
            raise ValueError("non-manual suggestion input")
        hints[(row["brand"], row["fl_code"], row["queue"])].append(row)
    output = []
    for c, f in zip(corr_rows, fl_rows):
        if c["fl_code"] != f["code"].strip().upper():
            raise ValueError("corr / FL row ordering differs")
        if c["status"] not in ("HOLD_NO_COLOR", "HOLD_LEGACY_NUMERIC"):
            continue
        key = (c["brand"], c["fl_code"], c["status"])
        fl_dist, fl_gen, fl_all = title_features(f.get("name", ""))
        eligible = []
        for suggestion in hints.get(key, []):
            sid = suggestion.get("sp_source_id", "")
            sp = sp_map.get(sid)
            if not sp:
                continue
            sp_dist, sp_gen, sp_all = title_features(sp.get("name", ""))
            conflicting_gen = False
            for model in {a for a, _ in fl_gen} & {a for a, _ in sp_gen}:
                if {b for a, b in fl_gen if a == model}.isdisjoint(
                        {b for a, b in sp_gen if a == model}):
                    conflicting_gen = True
            if conflicting_gen:
                continue
            suffix = suggestion.get("style_suffix_hint") == "1"
            exact_gen = sorted(fl_gen & sp_gen)
            distinctive = sorted(fl_dist & sp_dist)
            # A generic name-token overlap alone is too weak.
            if not (suffix or exact_gen or distinctive):
                continue
            strength = ("STYLE_SUFFIX" if suffix else
                        "MODEL_GENERATION" if exact_gen else "DISTINCTIVE_NAME")
            score = (100 if suffix else 0) + (40 if exact_gen else 0) + (
                10 * len(distinctive))
            eligible.append({**suggestion, "evidence_strength": strength,
                             "model_generation": "|".join(a + ":" + b for a, b in exact_gen),
                             "distinctive_overlap": "|".join(distinctive),
                             "review_score": str(score),
                             "match_status": "HUMAN_REVIEW_CANDIDATE"})
        eligible.sort(key=lambda v: (-int(v["review_score"]), v["sp_source_id"]))
        if eligible:
            output.extend(eligible[:max_per_fl])
        else:
            output.append({
                "brand": c["brand"], "fl_code": c["fl_code"], "queue": c["status"],
                "sp_source_id": "", "sp_style": "", "sp_color": "",
                "style_suffix_hint": "0", "name_overlap_tokens": "",
                "human_review_required": "1", "suggestion_only": "1",
                "match_status": "NO_STRONG_CANDIDATE", "evidence_strength": "",
                "model_generation": "", "distinctive_overlap": "", "review_score": "0",
            })
    return output


FIELDS = ("brand", "fl_code", "queue", "sp_source_id", "sp_style", "sp_color",
          "style_suffix_hint", "name_overlap_tokens", "human_review_required",
          "suggestion_only", "match_status", "evidence_strength",
          "model_generation", "distinctive_overlap", "review_score")


def load(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main():
    p = argparse.ArgumentParser()
    for arg in ("corr", "fl", "sp-full-corpus", "suggestions", "out"):
        p.add_argument("--" + arg, required=True)
    p.add_argument("--max-per-fl", type=int, default=5)
    args = p.parse_args()
    output = refine(load(args.corr), load(args.fl),
                    load(args.sp_full_corpus), load(args.suggestions),
                    args.max_per_fl)
    dest = Path(args.out)
    if dest.exists():
        raise ValueError("output exists")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("x", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(output)
    print(json.dumps({"rows": len(output),
                      "covered_holds": len({(r["brand"], r["fl_code"], r["queue"]) for r in output}),
                      "auto": 0, "manual_mapping_writes": 0}))


if __name__ == "__main__":
    main()

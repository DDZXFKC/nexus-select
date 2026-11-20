#!/usr/bin/env python3
"""Generate owner review shortlist and auditable counts from pinned real P1 outputs.

Read-only on source inputs; never changes corr AUTO, Stage3 or manual mappings.
Does NOT create matches. Designed for Muse's local verify-p0/verify-corr assets.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from cross_shop_name_aid_refine import refine


def load(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare(corr, fl, sp, suggestions, expected_holds=None, max_per_fl=5):
    hold_codes = ("HOLD_NO_COLOR", "HOLD_LEGACY_NUMERIC")
    if len(corr) != len(fl):
        raise ValueError("corr/FL count mismatch")
    expected = {(r["brand"], r["fl_code"], r["status"])
                for r in corr if r["status"] in hold_codes}
    if len(expected) != sum(r["status"] in hold_codes for r in corr):
        raise ValueError("duplicate HOLD identity")
    if expected_holds is not None and len(expected) != expected_holds:
        raise ValueError("HOLD count changed: " + str(len(expected)))
    orig_keys = {(r["brand"], r["fl_code"], r["queue"]) for r in suggestions}
    if orig_keys != expected:
        raise ValueError("suggestion HOLD coverage mismatch, missing=" +
                         repr(sorted(expected - orig_keys)) + ", extra=" +
                         repr(sorted(orig_keys - expected)))
    if any(r.get("suggestion_only") != "1" or
           r.get("human_review_required") != "1" for r in suggestions):
        raise ValueError("unverified suggestion authority")
    output = refine(corr, fl, sp, suggestions, max_per_fl)
    after_keys = {(r["brand"], r["fl_code"], r["queue"]) for r in output}
    if after_keys != expected:
        raise ValueError("refined HOLD coverage mismatch")
    if any(r.get("suggestion_only") != "1" or
           r.get("human_review_required") != "1" or
           r.get("match_status") not in
           ("HUMAN_REVIEW_CANDIDATE", "NO_STRONG_CANDIDATE")
           for r in output):
        raise ValueError("unsafe automatic adoption in owner report")
    queue_counts = Counter(r["status"] for r in corr if r["status"] in hold_codes)
    before_counts = Counter((r["brand"], r["fl_code"], r["queue"])
                            for r in suggestions
                            if r["sp_source_id"])
    after_counts = Counter((r["brand"], r["fl_code"], r["queue"])
                           for r in output
                           if r["sp_source_id"])
    review = []
    for brand, code, status in sorted(expected):
        count_before = before_counts.get((brand, code, status), 0)
        count_after = after_counts.get((brand, code, status), 0)
        review.append({"brand": brand, "fl_code": code, "hold_reason": status,
                       "candidate_before": count_before,
                       "candidate_after": count_after,
                       "human_review": "REQUIRED",
                       "decision": "UNREVIEWED"})
    summary = {
        "hold_count": len(expected),
        "hold_statuses": dict(sorted(queue_counts.items())),
        "original_report_rows": len(suggestions),
        "original_candidate_rows": sum(bool(r["sp_source_id"]) for r in suggestions),
        "refined_report_rows": len(output),
        "refined_candidate_rows": sum(bool(r["sp_source_id"]) for r in output),
        "no_strong_candidate_holds": sum(r["match_status"] == "NO_STRONG_CANDIDATE"
                                         for r in output),
        "owner_review_holds": sum(x["candidate_after"] > 0 for x in review),
        "auto_adopted": 0,
        "manual_mapping_writes": 0,
        "max_per_hold": max_per_fl,
    }
    return output, review, summary


def write_csv(path, fields, rows):
    target = Path(path)
    if target.exists():
        raise ValueError("output already exists: " + str(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def main():
    p = argparse.ArgumentParser()
    for arg in ("corr", "fl", "sp-full-corpus", "suggestions", "out-dir"):
        p.add_argument("--" + arg, required=True)
    p.add_argument("--expected-holds", type=int, default=60)
    p.add_argument("--max-per-fl", type=int, default=5)
    args = p.parse_args()
    paths = [args.corr, args.fl, args.sp_full_corpus, args.suggestions]
    outdir = Path(args.out_dir)
    if any((outdir / name).exists() for name in
           ("owner-candidates.csv", "hold-coverage.csv", "summary.json", "review.md")):
        raise ValueError("refuse to overwrite existing output")
    if len(set(str(Path(x).resolve()) for x in paths)) != len(paths):
        raise ValueError("input paths must be distinct")
    result, coverage, summary = prepare(
        load(args.corr), load(args.fl), load(args.sp_full_corpus),
        load(args.suggestions), args.expected_holds, args.max_per_fl)
    summary["input_sha256"] = {label: digest(path) for label, path in
        zip(("corr", "fl", "sp", "suggestions"), paths)}
    summary["normalization"] = "P1_READ_ONLY_REFINEMENT"
    outdir.mkdir(parents=True, exist_ok=True)
    write_csv(outdir / "owner-candidates.csv",
              ("brand", "fl_code", "queue", "sp_source_id", "sp_style", "sp_color",
               "style_suffix_hint", "name_overlap_tokens", "human_review_required",
               "suggestion_only", "match_status", "evidence_strength",
               "model_generation", "distinctive_overlap", "review_score"), result)
    write_csv(outdir / "hold-coverage.csv",
              ("brand", "fl_code", "hold_reason", "candidate_before",
               "candidate_after", "human_review", "decision"), coverage)
    (outdir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8")
    report = [
        "# 実60件の候補絞り込み・オーナー確認用監査",
        "",
        "- 合計HOLD: " + str(summary["hold_count"]),
        "- 元候補レポート行: " + str(summary["original_report_rows"]),
        "- 元の候補実行数: " + str(summary["original_candidate_rows"]),
        "- 絞り込み後レポート行: " + str(summary["refined_report_rows"]),
        "- 絞り込み後候補件数: " + str(summary["refined_candidate_rows"]),
        "- 強い候補が無いHOLD: " + str(summary["no_strong_candidate_holds"]),
        "- 目視要確認HOLD: " + str(summary["owner_review_holds"]),
        "- AUTO採用: 0（このスクリプトは採用処理を持たない）",
        "",
        "## 確認対象の明細",
        "",
        " `owner-candidates.csv` は**確定リンクではなく候補**。"
        " `hold-coverage.csv` は全HOLDの前後件数を追跡。",
        " 所有者の人目確認後もこのレポートだけで手動対応表を更新しない。",
        "",
        "## SHA-256入力証跡",
        "",
    ]
    report += ["- " + k + ": `" + v + "`" for k, v in
               sorted(summary["input_sha256"].items())]
    (outdir / "review.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()

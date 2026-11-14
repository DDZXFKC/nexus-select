"""Command line entry point.

    python3 -m ahc_qa --config config.json [--checks data,crawl,purchase] [--fresh] [--set-baseline]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time

from . import __version__
from .findings import FindingSet, compare_with_baseline, now_iso, write_reports

ALL_CHECKS = ["data", "crawl", "purchase"]


def load_config(path: str) -> dict:
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "..", "config.example.json"), encoding="utf-8") as fh:
        cfg = json.load(fh)
    if path:
        with open(path, encoding="utf-8") as fh:
            user = json.load(fh)
        for k, v in user.items():
            if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
    cfg["report_dir"] = os.path.expanduser(cfg["report_dir"])
    cfg["export_json"] = os.path.expanduser(cfg["export_json"])
    return cfg


def guard_report_dir(report_dir: str) -> None:
    """Refuse to write reports inside a git repository (the repo is public)."""
    d = os.path.abspath(report_dir)
    while True:
        if os.path.isdir(os.path.join(d, ".git")):
            sys.exit(f"レポートの出力先 {report_dir} がGitリポジトリ（{d}）の中にあります。公開リポジトリへの漏えいを防ぐため、リポジトリの外を指定してください。")
        parent = os.path.dirname(d)
        if parent == d:
            return
        d = parent


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ahc_qa", description="AFTER HOURS CLUB 品質検査（第1段階）")
    ap.add_argument("--config", default="", help="設定ファイル（JSON）")
    ap.add_argument("--checks", default=",".join(ALL_CHECKS), help="実行する検査: data,crawl,purchase")
    ap.add_argument("--fresh", action="store_true", help="巡回を最初からやり直す（既定は中断地点から再開）")
    ap.add_argument("--set-baseline", action="store_true", help="今回の結果を基準として保存する")
    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    checks = [c.strip() for c in args.checks.split(",") if c.strip()]
    for c in checks:
        if c not in ALL_CHECKS:
            sys.exit(f"不明な検査: {c}")
    root = cfg["report_dir"]
    guard_report_dir(root)
    run_id = time.strftime("%Y%m%d-%H%M%S")
    run_dir = os.path.join(root, "runs", run_id)
    state_dir = os.path.join(root, "state")
    os.makedirs(run_dir, exist_ok=True)
    os.makedirs(state_dir, exist_ok=True)
    log_path = os.path.join(run_dir, "run.log")

    def log(msg: str):
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    started = now_iso()
    log(f"AHC QA {__version__} 開始: {cfg['base_url']} 検査={checks}")
    fs = FindingSet()
    export = {}
    timings = {}

    if os.path.exists(cfg["export_json"]):
        from .data_checks import load_export
        export = load_export(cfg["export_json"])
        log(f"商品データ: {len(export.get('products', []))} 点（{export.get('exported_at','')} 書き出し）")
    elif "data" in checks or "purchase" in checks:
        log(f"商品データ {cfg['export_json']} がありません。READMEの手順1で書き出してください。data/purchase 検査は省略します。")

    if "data" in checks and export:
        t = time.time()
        from .data_checks import check_category_structure, run_data_checks
        try:
            fs.extend(run_data_checks(export, cfg))
            from .category_spec import run_category_spec_checks
            fs.extend(run_category_spec_checks(export, cfg))
            cat_f, created = check_category_structure(export, os.path.join(state_dir, "category_structure.json"))
            fs.extend(cat_f)
            if created:
                log("カテゴリー構造の確定形を state/category_structure.json に保存しました（次回から変更を検出します）")
        except Exception as e:
            log(f"data 検査でエラー（他の検査は続行）: {type(e).__name__}: {e}")
        timings["data"] = round(time.time() - t, 1)
        log(f"data 検査 完了（{timings['data']}秒）")

    if "crawl" in checks:
        t = time.time()
        from .crawl import Crawler
        try:
            cr = Crawler(cfg, state_dir, export)
            if args.fresh and os.path.exists(cr.state_path):
                os.remove(cr.state_path)
            fs.extend(cr.run(resume=not args.fresh, log=log))
            log(f"巡回 {len(cr.pages)} ページ、画像 {len(cr.images_checked)} 枚")
            # a finished crawl should start fresh next time
            if os.path.exists(cr.state_path):
                with open(cr.state_path, encoding="utf-8") as fh:
                    if not json.load(fh).get("queue"):
                        shutil.move(cr.state_path, os.path.join(run_dir, "crawl_state.json"))
        except Exception as e:
            log(f"crawl 検査でエラー（他の検査は続行）: {type(e).__name__}: {e}")
        timings["crawl"] = round(time.time() - t, 1)
        log(f"crawl 検査 完了（{timings['crawl']}秒）")

    if "purchase" in checks and export:
        t = time.time()
        from .purchase import run_purchase_checks
        try:
            fs.extend(run_purchase_checks(cfg, export, os.path.join(run_dir, "screenshots"), log=log))
        except Exception as e:
            log(f"purchase 検査でエラー: {type(e).__name__}: {e}")
        timings["purchase"] = round(time.time() - t, 1)
        log(f"purchase 検査 完了（{timings['purchase']}秒）")

    baseline_path = os.path.join(state_dir, "baseline.json")
    diff = compare_with_baseline(fs, baseline_path)
    meta = {"version": __version__, "base_url": cfg["base_url"], "checks": checks, "started_at": started,
            "finished_at": now_iso(), "timings_seconds": timings, "run_id": run_id}
    paths = write_reports(fs, run_dir, meta, diff)
    if args.set_baseline or diff["baseline"] is None:
        shutil.copyfile(paths["json"], baseline_path)
        log("今回の結果を基準（state/baseline.json）として保存しました")
    latest = os.path.join(root, "latest")
    try:
        if os.path.islink(latest) or os.path.exists(latest):
            os.remove(latest)
        os.symlink(run_dir, latest)
    except OSError:
        pass
    c = fs.counts()
    log("結果: " + " / ".join(f"{k} {v}" for k, v in c.items()) + f"（新規 {diff['new']}、解決 {len(diff['resolved'])}）")
    log(f"レポート: {paths['html']}")
    return 2 if c["CRITICAL"] else (1 if c["HIGH"] else 0)


if __name__ == "__main__":
    sys.exit(main())

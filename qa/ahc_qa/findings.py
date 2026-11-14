"""Findings, severities, baseline comparison and report output."""
from __future__ import annotations

import csv
import hashlib
import html
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "REVIEW"]
SEVERITY_ORDER = {s: i for i, s in enumerate(SEVERITIES)}

# Human-readable Japanese labels for each finding type.
TYPE_LABELS = {
    "PRICE_MISSING": "価格の欠落",
    "PRICE_INVALID": "不正な価格",
    "VARIATION_PRICE_MISSING": "バリエーションの価格欠落",
    "VARIABLE_NO_VARIATIONS": "バリエーションが1つもない",
    "VARIATION_NOT_PURCHASABLE": "購入できないバリエーション",
    "NAME_MISSING": "商品名の欠落",
    "BRAND_MISSING": "ブランド名の欠落",
    "DESCRIPTION_MISSING": "商品説明の欠落",
    "IMAGE_NOT_SET": "商品画像の登録漏れ",
    "IMAGE_FILE_MISSING": "画像ファイルが存在しない",
    "IMAGE_SIZE_FILE_MISSING": "縮小画像ファイルが存在しない",
    "SKU_MISSING": "SKUの欠落",
    "SKU_DUPLICATE": "SKUの重複",
    "CATEGORY_NONE": "カテゴリー未設定",
    "CATEGORY_GENDER_MIX": "KIDSと大人用への同時登録",
    "CAT_SPEC_MISSING": "設計にあるカテゴリーがない",
    "CAT_SPEC_PARENT": "カテゴリーの親が設計と違う",
    "CAT_SPEC_URL": "カテゴリーのURLが設計と違う",
    "CAT_SPEC_EXTRA": "設計にないカテゴリー",
    "CAT_ANCESTOR_MISSING": "親カテゴリーの付け忘れ",
    "CAT_LEAF_MISSING": "末端カテゴリーの付け忘れ",
    "CAT_FACET_RULE": "用途カテゴリーの誤分類の可能性",
    "CAT_COUNT_EXPECTED": "商品数が想定と違う",
    "CAT_NEEDS_REVIEW": "自動分類できなかった商品",
    "SCHEME_MISMATCH": "http/https の混在リンク",
    "CAT_OLD_URL": "旧カテゴリーURLの転送不良",
    "CAT_CURRENT_HIGHLIGHT": "現在地のハイライト不良",
    "CAT_LIST_DUPLICATE": "商品一覧の重複表示",
    "INV_NO_ALL_GROUP_LINK": "確定事項違反：ALL SHOESなどの重複リンク",
    "CATEGORY_COUNT_MISMATCH": "カテゴリーの商品数の不一致",
    "BRAND_RESIDUE": "旧ブランド名の残存",
    "HTTP_ERROR": "HTTPエラー",
    "BROKEN_LINK": "リンク切れ",
    "REDIRECT_CHAIN": "リダイレクトの繰り返し",
    "REDIRECT_LOOP": "リダイレクトのループ",
    "TITLE_MISSING": "ページタイトルの欠落",
    "FETCH_ERROR": "ページ取得の失敗",
    "IMAGE_HTTP_ERROR": "画像の表示エラー",
    "IMAGE_BROKEN": "画像ファイルの破損",
    "INV_PC_HERO_STATIC": "確定事項違反：PCヒーローは静止画のみ",
    "INV_NO_HEADER_DROPDOWN": "確定事項違反：ヘッダーのドロップダウン廃止",
    "INV_EMPTY_CATEGORY_HIDDEN": "確定事項違反：空カテゴリーの非表示",
    "INV_LOGO": "確定事項違反：承認済みロゴ",
    "INV_PRODUCT_VERTICAL_GALLERY": "確定事項違反：商品ページは縦スクロール",
    "INV_CATEGORY_STRUCTURE": "確定事項違反：カテゴリー構造",
    "PURCHASE_FLOW": "購入機能の不具合",
    "PURCHASE_SKIPPED": "購入機能の検査を実行できなかった",
}


@dataclass
class Finding:
    type: str
    severity: str
    message: str
    judge: str = "Python"  # Python / AI / 人
    product_id: int | None = None
    product_name: str = ""
    page_url: str = ""
    image_url: str = ""
    location: str = ""
    evidence: str = ""
    screenshot: str = ""
    cause_group: str = ""
    status: str = "未修正"
    origin: str = ""  # 既存 / 新規 (filled by baseline comparison)
    extra: dict = field(default_factory=dict)

    def key(self) -> str:
        """Stable identity used for baseline comparison (ignores message wording)."""
        page = "" if self.extra.get("page_count") else self.page_url
        raw = "|".join([self.type, str(self.product_id or ""), page, self.image_url, self.location])
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict:
        d = asdict(self)
        d["key"] = self.key()
        d["type_label"] = TYPE_LABELS.get(self.type, self.type)
        return d


class FindingSet:
    def __init__(self) -> None:
        self.items: list[Finding] = []
        self._seen: set[str] = set()

    def add(self, f: Finding) -> None:
        if f.severity not in SEVERITY_ORDER:
            raise ValueError(f"unknown severity {f.severity}")
        k = f.key()
        if k in self._seen:
            return
        self._seen.add(k)
        if not f.cause_group:
            f.cause_group = f.type
        self.items.append(f)

    def extend(self, fs) -> None:
        for f in fs:
            self.add(f)

    def sorted(self) -> list[Finding]:
        return sorted(self.items, key=lambda f: (SEVERITY_ORDER[f.severity], f.cause_group, f.page_url, f.product_id or 0))

    def counts(self) -> dict:
        c = {s: 0 for s in SEVERITIES}
        for f in self.items:
            c[f.severity] += 1
        return c


def compare_with_baseline(fs: FindingSet, baseline_path: str) -> dict:
    """Mark each finding 既存/新規 and list resolved keys. Returns summary."""
    if not os.path.exists(baseline_path):
        for f in fs.items:
            f.origin = "初回"
        return {"baseline": None, "new": 0, "existing": 0, "resolved": []}
    with open(baseline_path, encoding="utf-8") as fh:
        base = json.load(fh)
    base_keys = {b["key"]: b for b in base.get("findings", [])}
    cur_keys = set()
    new = existing = 0
    for f in fs.items:
        k = f.key()
        cur_keys.add(k)
        if k in base_keys:
            f.origin = "既存"
            existing += 1
        else:
            f.origin = "新規"
            new += 1
    resolved = [b for k, b in base_keys.items() if k not in cur_keys]
    return {"baseline": baseline_path, "new": new, "existing": existing, "resolved": resolved}


def write_reports(fs: FindingSet, out_dir: str, meta: dict, diff: dict) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    items = [f.to_dict() for f in fs.sorted()]
    payload = {"meta": meta, "counts": fs.counts(), "baseline_diff": {k: v for k, v in diff.items() if k != "resolved"},
               "resolved": diff.get("resolved", []), "findings": items}
    jpath = os.path.join(out_dir, "findings.json")
    with open(jpath, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    cpath = os.path.join(out_dir, "findings.csv")
    cols = ["severity", "origin", "type_label", "type", "cause_group", "judge", "product_id", "product_name",
            "page_url", "image_url", "location", "message", "evidence", "screenshot", "status", "key"]
    with open(cpath, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for d in items:
            w.writerow(d)

    hpath = os.path.join(out_dir, "report.html")
    with open(hpath, "w", encoding="utf-8") as fh:
        fh.write(render_html(payload))
    return {"json": jpath, "csv": cpath, "html": hpath}


def render_html(payload: dict) -> str:
    e = html.escape
    meta, counts, items = payload["meta"], payload["counts"], payload["findings"]
    groups: dict[str, list] = {}
    for d in items:
        groups.setdefault((d["severity"], d["cause_group"]), []).append(d)
    colors = {"CRITICAL": "#B00020", "HIGH": "#C2410C", "MEDIUM": "#A16207", "LOW": "#4B5563", "REVIEW": "#1D4ED8"}
    parts = [
        "<!doctype html><html lang='ja'><head><meta charset='utf-8'><title>AHC 品質検査レポート</title>",
        "<style>body{font-family:-apple-system,'Hiragino Sans',sans-serif;margin:32px;color:#111;max-width:1200px}"
        "table{border-collapse:collapse;width:100%;font-size:13px;margin:8px 0 24px}td,th{border:1px solid #ddd;padding:6px 8px;text-align:left;vertical-align:top}"
        "th{background:#f5f5f5}.sev{color:#fff;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:600}"
        ".cards{display:flex;gap:12px;flex-wrap:wrap}.card{border:1px solid #ddd;border-radius:8px;padding:12px 16px;min-width:110px}"
        ".card b{display:block;font-size:24px}details{margin:12px 0}summary{cursor:pointer;font-weight:600;font-size:15px}"
        ".new{color:#B00020;font-weight:600}</style></head><body>",
        f"<h1>AFTER HOURS CLUB 品質検査レポート</h1><p>実行日時：{e(meta.get('finished_at',''))}　対象：{e(meta.get('base_url',''))}　"
        f"検査：{e(', '.join(meta.get('checks', [])))}</p>",
        "<div class='cards'>",
    ]
    for s in SEVERITIES:
        parts.append(f"<div class='card'><span class='sev' style='background:{colors[s]}'>{s}</span><b>{counts.get(s,0)}</b></div>")
    bd = payload.get("baseline_diff", {})
    parts.append(f"<div class='card'>新規<b>{bd.get('new',0)}</b></div><div class='card'>解決済み<b>{len(payload.get('resolved',[]))}</b></div></div>")
    parts.append("<h2>原因ごとの一覧</h2>")
    for (sev, group), ds in sorted(groups.items(), key=lambda kv: (SEVERITY_ORDER[kv[0][0]], kv[0][1])):
        label = ds[0]["type_label"]
        parts.append(f"<details {'open' if sev in ('CRITICAL','HIGH') else ''}><summary><span class='sev' style='background:{colors[sev]}'>{sev}</span> "
                     f"{e(label)}（{e(group)}）— {len(ds)}件</summary><table><tr><th>状態</th><th>判定</th><th>商品</th><th>ページ／画像</th><th>内容</th><th>根拠</th></tr>")
        for d in ds[:500]:
            prod = f"{d['product_id'] or ''} {e(d['product_name'] or '')}"
            where = " ".join(x for x in [
                f"<a href='{e(d['page_url'])}'>{e(d['page_url'])}</a>" if d["page_url"] else "",
                f"<br><a href='{e(d['image_url'])}'>{e(d['image_url'])}</a>" if d["image_url"] else "",
                f"<br>{e(d['location'])}" if d["location"] else ""] if x)
            origin = f"<span class='new'>{e(d['origin'])}</span>" if d["origin"] == "新規" else e(d["origin"])
            parts.append(f"<tr><td>{origin}</td><td>{e(d['judge'])}</td><td>{prod}</td><td>{where}</td><td>{e(d['message'])}</td><td>{e(d['evidence'])}</td></tr>")
        if len(ds) > 500:
            parts.append(f"<tr><td colspan='6'>ほか {len(ds)-500} 件（CSVを参照）</td></tr>")
        parts.append("</table></details>")
    if payload.get("resolved"):
        parts.append(f"<h2>前回から解決したもの（{len(payload['resolved'])}件）</h2><table><tr><th>種類</th><th>商品／ページ</th></tr>")
        for b in payload["resolved"][:300]:
            parts.append(f"<tr><td>{e(b.get('type_label',''))}</td><td>{e(str(b.get('product_id') or ''))} {e(b.get('page_url',''))}</td></tr>")
        parts.append("</table>")
    parts.append("</body></html>")
    return "".join(parts)


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

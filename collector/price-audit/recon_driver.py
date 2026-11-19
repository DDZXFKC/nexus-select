#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shoe Palace 価格検証 第2段階 再照合ドライバー（1ファイル完結・標準ライブラリのみ）

== 入力パスの前提（すべて --base からの相対。--base のデフォルトは '.'） ==
  out-v8-a/variants.csv   : 163商品スコープ・1,796行（仕様書の variants ヘッダどおり）
  out-v8-a/products.csv   : 163行（brand 列をガード判定に使用）
  out-v8-a/issues.csv     : 1,340行（product_id, variant_id, reason）
  out-v8-b/variants.csv   : a とバイト一致しているはず（sha256 で確認・記録する）
  out-v8-b/products.csv   : 参考確認（バイト一致チェックのみ）
  out-v8-b/issues.csv     : 参考確認（同上）
  audit163.json           : 第1段階監査結果（results / sheet_issues / scope / sheet_variants_checked）
  sheet_prices.csv        : シート書き出し。列: row, product_id, variant_id,
                            price_minor, compare_at_price_minor, regular_price_minor
                            （値は minor 単位の整数、空欄は空文字）

== 出力（--base 直下） ==
  recon-verdicts.csv  : 87バリアント×3フィールド=261行の判定
                        (product_id, variant_id, field, sheet_value, v8a_value, v8b_value,
                         classification, basis, audit_row, brand)
  recon-summary.md    : 分類件数・代表例・結論ドラフト・ガード適用状況・警告一覧
  size-pending.csv    : cm_status != MATCHED の保留リスト（根拠項目・ガード付き）

== 分類（classification 値） ==
  reproduced          : 再現（v8-a/b ともシートと不一致 → シート側が古い／別時点の疑い）
  non_reproduced      : 非再現（v8-b ではシート値と一致 = v8-a のみの現象）
  rule_difference     : 条件差（regular_price_minor の導出ルール差で説明可能）
  audit_not_reproduced: 監査指摘が今回の照合では一致として解消（シート更新済み等の疑い）
  v8b_only_mismatch   : v8-b のみ不一致（a/b 出力差異に起因。要調査）
  sheet_row_missing   : sheet_prices.csv に該当行なし（判定不可）
  invalid_value       : 数値変換不能な値を含む
  fatal_missing_input : variants.csv(a/b) 側に該当バリアントが無い

== ガード（本ドライバーが守るもの） ==
  - HOKA / UGG     : 出典・体系不明の参照値は確定にしない
  - BIRKENSTOCK    : scoped のみ（scoped 判定不能は保留）
  - 価格レイヤー（minor 単位）のみの検証。原価計算はしない
  - ライブ取得・カート・購入・価格反映は禁止（ローカルファイル入出力のみ）

実行例: python3 recon_driver.py --base /path/to/workdir
"""

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PRICE_FIELDS = ('price_minor', 'compare_at_price_minor', 'regular_price_minor')

REASON_TO_FIELD = {
    'price_minor_mismatch': 'price_minor',
    'compare_at_price_minor_mismatch': 'compare_at_price_minor',
    'regular_price_minor_mismatch': 'regular_price_minor',
}

CLASS_JA = {
    'reproduced': '再現（シート側が古い／別時点の疑い）',
    'non_reproduced': '非再現（v8-a のみの現象）',
    'rule_difference': '条件差（導出ルール差で説明可能）',
    'audit_not_reproduced': '監査指摘が今回の照合では解消（シート更新済み等の疑い）',
    'v8b_only_mismatch': 'v8-b のみ不一致（a/b 差異に起因。要調査）',
    'sheet_row_missing': 'sheet_prices.csv に該当行なし（判定不可）',
    'invalid_value': '数値変換不能（要シート再確認）',
    'fatal_missing_input': '入力欠落（v8 側にバリアントなし）',
}

GUARD_HOKA_UGG = {'HOKA', 'UGG'}
GUARD_BIRKENSTOCK = 'BIRKENSTOCK'

# 前回指摘の87バリアント（検証用の期待値。audit163.json の sheet_issues と突き合わせる）
EXPECTED_87 = (
    ("7593210839246", "43109336809678"), ("7593210839246", "43109336842446"),
    ("7593210839246", "43109336875214"), ("7593210839246", "43109336907982"),
    ("7593210839246", "43109337530574"), ("7593210839246", "43109337563342"),
    ("7593210839246", "43109337596110"), ("7593210839246", "43109337628878"),
    ("7593210839246", "43109337661646"), ("7593210839246", "43109337694414"),
    ("7593210839246", "43109337727182"), ("7593210839246", "43109337759950"),
    ("7593210839246", "43109337792718"), ("7593210839246", "43109337825486"),
    ("7596417417422", "43121197547726"), ("7596417417422", "43121197580494"),
    ("7596417417422", "43121197613262"), ("7596417417422", "43121197646030"),
    ("7596417417422", "43121197678798"), ("7596417417422", "43121197711566"),
    ("7596417417422", "43121197744334"), ("7596417417422", "43121197777102"),
    ("7596417417422", "43121197809870"), ("7596417417422", "43121197842638"),
    ("7596417417422", "43121197875406"), ("7596417417422", "43121197908174"),
    ("7596417417422", "43121197940942"), ("7596417417422", "43121197973710"),
    ("7602246811854", "43137804599502"), ("7602246811854", "43137804632270"),
    ("7602246811854", "43137804665038"), ("7602246811854", "43137804697806"),
    ("7602246811854", "43137804730574"), ("7602246811854", "43137804763342"),
    ("7602246811854", "43137804796110"), ("7602246811854", "43137804828878"),
    ("7602246811854", "43137804861646"), ("7602246811854", "43137804894414"),
    ("7602246811854", "43137804927182"), ("7602246811854", "43137804959950"),
    ("7602246811854", "43137804992718"), ("7602246811854", "43137805025486"),
    ("7602585174222", "43138796585166"), ("7602585174222", "43138796617934"),
    ("7602585174222", "43138796650702"), ("7602585174222", "43138796683470"),
    ("7602585174222", "43138796716238"), ("7602585174222", "43138796749006"),
    ("7602585174222", "43138796781774"), ("7602585174222", "43138796814542"),
    ("7602585174222", "43138796847310"), ("7602585174222", "43138796880078"),
    ("7602585174222", "43138796912846"), ("7602585174222", "43138796945614"),
    ("7602585174222", "43138796978382"), ("7602585174222", "43138797011150"),
    ("7602585174222", "43138797043918"), ("7602585174222", "43138797076686"),
    ("7602585174222", "43138797109454"),
    ("7621953224910", "43203725656270"), ("7621953224910", "43203725689038"),
    ("7621953224910", "43203725721806"), ("7621953224910", "43203725754574"),
    ("7621953224910", "43203725787342"), ("7621953224910", "43203725820110"),
    ("7621953224910", "43203725852878"), ("7621953224910", "43203725885646"),
    ("7621953224910", "43203725918414"), ("7621953224910", "43203725951182"),
    ("7621953224910", "43203725983950"), ("7621953224910", "43203726016718"),
    ("7621953224910", "43203726049486"), ("7621953224910", "43203726082254"),
    ("7701693038798", "43547680735438"), ("7701693038798", "43547680768206"),
    ("7701693038798", "43547680800974"), ("7701693038798", "43547680833742"),
    ("7701693038798", "43547680866510"), ("7701693038798", "43547680899278"),
    ("7701693038798", "43547680932046"), ("7701693038798", "43547680964814"),
    ("7701693038798", "43547680997582"), ("7701693038798", "43547681030350"),
    ("7701693038798", "43547681063118"), ("7701693038798", "43547681095886"),
    ("7701693038798", "43547681128654"), ("7701693038798", "43547681161422"),
)


# ---------------------------------------------------------------- 基本ユーティリティ

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def normalize_minor(v):
    """空文字/None -> None（空）。他は int。変換不能は ('INVALID', raw) を返す。"""
    if v is None:
        return None
    s = str(v).strip()
    if s == '':
        return None
    try:
        return int(s)
    except ValueError:
        return ('INVALID', s)


def fmt_minor(v) -> str:
    if v is None:
        return ''
    if isinstance(v, tuple):
        return 'INVALID:' + str(v[1])
    return str(v)


def is_invalid(v) -> bool:
    return isinstance(v, tuple)


# ---------------------------------------------------------------- ローダー

def load_csv_rows(path):
    with path.open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def load_variants(path, label, warnings):
    rows = {}
    n = 0
    for r in load_csv_rows(path):
        n += 1
        key = ((r.get('product_id') or '').strip(), (r.get('variant_id') or '').strip())
        if key in rows:
            warnings.append(f'{label}/variants.csv: 主キー重複 {key}')
        rows[key] = r
    return rows, n


def load_brand_map(path):
    m = {}
    for r in load_csv_rows(path):
        m[(r.get('product_id') or '').strip()] = (r.get('brand') or '').strip()
    return m


def load_issues(path):
    return [((r.get('product_id') or '').strip(),
             (r.get('variant_id') or '').strip(),
             (r.get('reason') or '').strip()) for r in load_csv_rows(path)]


def load_sheet_prices(path, warnings):
    by_key, by_row = {}, {}
    n = 0
    for r in load_csv_rows(path):
        n += 1
        raw_row = (r.get('row') or '').strip()
        key = ((r.get('product_id') or '').strip(), (r.get('variant_id') or '').strip())
        rec = {
            'row': raw_row,
            'price_minor': normalize_minor(r.get('price_minor')),
            'compare_at_price_minor': normalize_minor(r.get('compare_at_price_minor')),
            'regular_price_minor': normalize_minor(r.get('regular_price_minor')),
        }
        if key in by_key:
            warnings.append(f'sheet_prices.csv: キー重複 {key}')
        by_key[key] = rec
        if raw_row:
            if raw_row in by_row:
                warnings.append(f'sheet_prices.csv: 行番号重複 {raw_row}')
            by_row[raw_row] = key
    return by_key, by_row, n


def check_audit_results(results, warnings):
    n = len(results)
    bad = odd = 0
    for it in results:
        if isinstance(it, dict):
            if it.get('errors') or it.get('warnings'):
                bad += 1
        else:
            odd += 1
    if odd:
        warnings.append(f'audit163.json: results に dict 形式でない要素 {odd} 件（PASS 判定から除外）')
    return n, bad, (n > 0 and bad == 0 and odd == 0)


# ---------------------------------------------------------------- 判定ロジック

def expected_regular(price, compare_at):
    """v8 の regular_price_minor 期待値ルール:
    compare_at が存在し 0 < compare_at かつ compare_at >= price なら compare_at、それ以外は None(空)。"""
    if price is None or compare_at is None:
        return None
    if is_invalid(price) or is_invalid(compare_at):
        return None
    if compare_at > 0 and compare_at >= price:
        return compare_at
    return None


def classify(field, sheet, va, vb, sheet_vals, va_vals, audit_all_pass):
    if is_invalid(sheet) or is_invalid(va) or is_invalid(vb):
        return 'invalid_value', '数値変換不能な値を含むため判定保留（該当セルの再確認・再書き出し要）'

    if sheet == va:
        if sheet == vb:
            basis = ('監査指摘だが今回の照合では v8-a/b いずれとも一致。監査実行時のシート値と今回の書き出し値が異なる'
                     '（シート更新済み等）の疑い')
            if audit_all_pass:
                basis += '。なお raw(Shopify生データ) と v8 出力は監査全件 PASS'
            return 'audit_not_reproduced', basis
        return 'v8b_only_mismatch', 'v8-a とは一致するが v8-b と不一致（a/b 出力差異に起因。要調査）'

    if sheet == vb:
        return 'non_reproduced', 'v8-b ではシート値と一致（v8-a のみの現象）'

    # sheet != va かつ sheet != vb
    if field == 'regular_price_minor':
        sp, sc = sheet_vals['price_minor'], sheet_vals['compare_at_price_minor']
        ap, ac = va_vals['price_minor'], va_vals['compare_at_price_minor']
        if sp == ap and sc == ac and not is_invalid(sp) and not is_invalid(sc):
            exp = expected_regular(sp, sc)
            if sheet != exp:
                return 'rule_difference', (
                    'シートの price/compare_at は v8-a と一致。regular_price_minor は v8 ルール'
                    '（compare_at が存在し 0 より大で price 以上なら compare_at、それ以外は空）の期待値 '
                    f'{"空" if exp is None else exp} と異なる保持であり、導出ルール差で説明可能')

    basis = 'v8-a / v8-b のいずれのスナップショット値とも不一致'
    if audit_all_pass:
        basis += ('。raw(Shopify生データ) と v8 出力の照合は監査で全件 PASS のため、'
                  'シート側値が v8-a スナップショットより古い／別時点である疑い')
    return 'reproduced', basis


def draft_conclusion(cls_counter, a_b_identical, audit_all_pass, extra_list):
    lines = []
    total = sum(cls_counter.values())
    rep = cls_counter.get('reproduced', 0)
    rule = cls_counter.get('rule_difference', 0)
    nonrep = cls_counter.get('non_reproduced', 0)
    v8b_only = cls_counter.get('v8b_only_mismatch', 0)
    cleared = cls_counter.get('audit_not_reproduced', 0)
    inv = cls_counter.get('invalid_value', 0)
    miss = cls_counter.get('sheet_row_missing', 0)
    fatal = cls_counter.get('fatal_missing_input', 0)
    if fatal:
        lines.append(f'- 入力欠落 {fatal}/{total} 件。out-v8-a/b の variants.csv に該当バリアントが無い。入力を揃えて再実行を。')
    if miss:
        lines.append(f'- シート行欠落 {miss}/{total} 件。sheet_prices.csv に該当行が無く判定不可。書き出し範囲（監査 row 1026〜1657）の再確認を。')
    if inv:
        lines.append(f'- 数値変換不能 {inv}/{total} 件。sheet_prices.csv の該当セル（minor 単位の整数のはず）の再確認・再書き出しを。')
    if rep:
        b = f'- 再現 {rep}/{total} 件：v8-a・v8-b いずれのスナップショット値とも不一致'
        if audit_all_pass:
            b += ('。raw と v8 の照合は監査全件 PASS のため v8 側価格レイヤーは raw と一致しており、'
                  '**シート側が v8-a スナップショットより古い／別時点の値**である可能性が高い')
        lines.append(b + '。')
    if rule:
        lines.append(f'- 条件差 {rule}/{total} 件：regular_price_minor の導出ルール差'
                     '（v8: compare_at が存在し 0 より大で price 以上なら compare_at、それ以外は空）'
                     'で説明可能。シート側の保持ルールを明文化し、一致方向を決めることを推奨。')
    if nonrep:
        tail = ('a/b はバイト一致のはずのため入力混在の疑い。要調査。' if a_b_identical
                else 'a/b 間に出力差が実在する。v8 パイプライン側の要調査。')
        lines.append(f'- 非再現 {nonrep}/{total} 件：v8-b ではシート値と一致（v8-a のみの現象）。{tail}')
    if v8b_only:
        lines.append(f'- v8-b のみ不一致 {v8b_only}/{total} 件：a/b 出力差異に起因。v8 パイプラインの要調査。')
    if cleared:
        lines.append(f'- 監査指摘解消 {cleared}/{total} 件：監査実行時のシート値と今回の sheet_prices.csv が異なる'
                     '（シートが監査後に更新された等）可能性。シート更新履歴との突き合わせを推奨。')
    if extra_list:
        lines.append(f'- 監査未指摘の追加不一致 {len(extra_list)} 件（sheet_prices.csv 全行との直接照合で発見）。'
                     '監査スコープ外か監査後のシート変更の疑い。代表: '
                     + '; '.join(f'{k[0]}/{k[1]} {f} ({note})' for k, f, note in extra_list[:3]))
    if not any((rep, rule, nonrep, v8b_only, cleared, inv, miss, fatal, extra_list)):
        lines.append('- 差分はすべて解消。シートと v8-a/b の価格3点は完全一致。')
    return lines


# ---------------------------------------------------------------- 出力

VERDICT_COLS = ['product_id', 'variant_id', 'field', 'sheet_value', 'v8a_value', 'v8b_value',
                'classification', 'basis', 'audit_row', 'brand']
PENDING_COLS = ['product_id', 'variant_id', 'sku', 'brand', 'size_original', 'cm', 'cm_status',
                'cm_source_url', 'cm_source_url_present', 'cm_model', 'cm_age_group',
                'cm_size_system', 'cm_reference_type', 'guard', 'guard_note']


def write_csv(path, cols, rows):
    with path.open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def write_summary(path, ctx):
    L = []
    A = L.append
    A('# Shoe Palace 価格再照合サマリ（第2段階）')
    A('')
    A(f'- 生成時刻(UTC): {ctx["now"]}')
    A('- ドライバー: recon_driver.py（1ファイル・標準ライブラリのみ。ライブ取得・カート・購入・価格反映なし）')
    A(f'- 監査スコープ（踏襲）: {ctx["scope"] or "(audit163.json に scope なし)"}')
    A('- 検証レイヤー: 価格（minor 単位）のみ。原価計算は実施しない。')
    A('')
    A('## 入力検証')
    A('')
    for name, (ha, hb, same) in ctx['hashes'].items():
        mark = '一致' if same else '**不一致**'
        A(f'- out-v8-a vs out-v8-b `{name}`: バイト{mark}（sha256 a={ha[:12]}… / b={hb[:12]}…）')
    if not ctx['variants_identical']:
        A('- **注意**: variants.csv がバイト不一致。「最新確認済み観測 = v8-a」の前提が崩れる可能性あり、'
          'non_reproduced / v8b_only_mismatch の解釈に注意。')
    A(f'- variants.csv: a={ctx["a_n"]}行 / b={ctx["b_n"]}行（1,796 期待。主キー重複は警告欄参照）')
    A(f'- products.csv: {ctx["p_n"]}行（163 期待） / issues.csv: {ctx["i_n"]}件（1,340 期待）')
    A(f'- sheet_prices.csv: {ctx["sheet_n"]}行（87 期待）')
    A(f'- audit163.json: results={ctx["results_n"]}件（非PASS {ctx["res_bad"]}件）/ '
      f'sheet_issues={ctx["sheet_issues_n"]}件 / sheet_variants_checked={ctx["checked"]}')
    if ctx['checked'] is not None:
        try:
            if int(ctx['checked']) != ctx['a_n']:
                A(f'- **注意**: sheet_variants_checked({ctx["checked"]}) と variants.csv 行数({ctx["a_n"]})が不一致')
        except (TypeError, ValueError):
            A(f'- **注意**: sheet_variants_checked の値が数値として読めない: {ctx["checked"]!r}')
    A('')
    A('## 分類結果（監査 sheet_issues = 87バリアント × 3フィールド = 261件）')
    A('')
    A('| classification | 件数 | 意味 |')
    A('|---|---:|---|')
    for cls in ('reproduced', 'rule_difference', 'non_reproduced', 'v8b_only_mismatch',
                'audit_not_reproduced', 'sheet_row_missing', 'invalid_value', 'fatal_missing_input'):
        A(f'| {cls} | {ctx["cls_counter"].get(cls, 0)} | {CLASS_JA.get(cls, "")} |')
    A(f'| **合計** | **{sum(ctx["cls_counter"].values())}** | |')
    A('')
    A('## 代表例（各分類 最大3件、監査 row 昇順）')
    A('')
    any_example = False
    for cls in ('reproduced', 'rule_difference', 'non_reproduced', 'v8b_only_mismatch',
                'audit_not_reproduced', 'sheet_row_missing', 'invalid_value', 'fatal_missing_input'):
        rows_ = ctx['examples'].get(cls)
        if not rows_:
            continue
        any_example = True
        A(f'### {cls}（{CLASS_JA.get(cls, "")}）')
        for r in rows_[:3]:
            A(f'- ({r["product_id"]}, {r["variant_id"]}) field={r["field"]} row={r["audit_row"] or "?"} '
              f'sheet={r["sheet_value"] or "(空)"} v8a={r["v8a_value"] or "(空)"} v8b={r["v8b_value"] or "(空)"} '
              f'brand={r["brand"] or "?"}')
        A('')
    if not any_example:
        A('（判定対象なし）')
        A('')
    A('## 差分87バリアントのブランド分布（products.csv の brand 列）')
    A('')
    if ctx['brand87']:
        for b, c in ctx['brand87'].most_common():
            A(f'- {b or "(brand 空または products 行なし)"}: {c}バリアント')
    else:
        A('- (対象なし)')
    A('')
    A('## 結論（機械ドラフト）')
    A('')
    for line in ctx['conclusion']:
        A(line)
    A('')
    A('## ガード適用状況')
    A('')
    A('- HOKA / UGG: 出典・体系不明の参照値は確定にしない（size-pending.csv の guard 列で管理）')
    A('- BIRKENSTOCK: scoped のみ扱い（scoped 判定不能は保留）')
    A('- 本ドライバーの価格判定は保存済みスナップショット照合のみに基づく。原価計算・参照値の確定・ライブ系操作を含まない')
    A(f'- size-pending.csv: 計 {ctx["pending_n"]} 件（cm_status != MATCHED）')
    for g in ('HOKA_UGG_UNVERIFIED_REFERENCE', 'HOKA_UGG_GUARDED',
              'BIRKENSTOCK_SCOPED', 'BIRKENSTOCK_NOT_SCOPED', 'none'):
        c = ctx['guard_stats'].get(g, 0)
        if c:
            A(f'  - guard={g}: {c} 件')
    A('')
    A('## 警告・注意')
    A('')
    if ctx['warnings']:
        for w in ctx['warnings']:
            A(f'- {w}')
    else:
        A('- なし')
    path.write_text('\n'.join(L) + '\n', encoding='utf-8')


# ---------------------------------------------------------------- メイン

def main(argv=None):
    ap = argparse.ArgumentParser(description='Shoe Palace 価格検証 第2段階 再照合ドライバー')
    ap.add_argument('--base', default='.', help='入出力の基準ディレクトリ（既定: カレント）')
    args = ap.parse_args(argv)

    base = Path(args.base)
    pa, pb = base / 'out-v8-a', base / 'out-v8-b'
    req = [pa / 'variants.csv', pa / 'products.csv', pa / 'issues.csv',
           pb / 'variants.csv', pb / 'products.csv', pb / 'issues.csv',
           base / 'audit163.json', base / 'sheet_prices.csv']
    missing = [str(p) for p in req if not p.is_file()]
    if missing:
        print('[FATAL] 入力ファイルが見つかりません:', file=sys.stderr)
        for m in missing:
            print('  - ' + m, file=sys.stderr)
        return 2

    warnings = []
    now = datetime.now(timezone.utc).isoformat(timespec='seconds')

    # --- a/b バイト一致（クロスチェック） ---
    hashes = {}
    for name in ('variants.csv', 'products.csv', 'issues.csv'):
        ha, hb = sha256_file(pa / name), sha256_file(pb / name)
        hashes[name] = (ha, hb, ha == hb)
    variants_identical = hashes['variants.csv'][2]
    if not variants_identical:
        warnings.append('out-v8-a と out-v8-b の variants.csv がバイト不一致。前提（a/b 完全一致）と矛盾。')

    # --- 正規ビュー構築 ---
    a_variants, a_n = load_variants(pa / 'variants.csv', 'out-v8-a', warnings)
    b_variants, b_n = load_variants(pb / 'variants.csv', 'out-v8-b', warnings)
    brand_map = load_brand_map(pa / 'products.csv')
    p_n = len(brand_map)
    issues_a = load_issues(pa / 'issues.csv')
    i_n = len(issues_a)
    sheet_by_key, sheet_by_row, sheet_n = load_sheet_prices(base / 'sheet_prices.csv', warnings)
    audit = json.loads((base / 'audit163.json').read_text(encoding='utf-8-sig'))
    scope = audit.get('scope', '')
    results = audit.get('results') or []
    res_n, res_bad, audit_all_pass = check_audit_results(results, warnings)
    sheet_issues = audit.get('sheet_issues') or []
    checked = audit.get('sheet_variants_checked')

    if a_n != 1796:
        warnings.append(f'out-v8-a/variants.csv が {a_n} 行（1,796 期待）')
    if p_n != 163:
        warnings.append(f'out-v8-a/products.csv が {p_n} 行（163 期待）')
    if i_n != 1340:
        warnings.append(f'out-v8-a/issues.csv が {i_n} 件（1,340 期待）')

    # --- 監査 sheet_issues を (pid, vid, field) の対象へ展開 ---
    targets = []
    for it in sheet_issues:
        if not isinstance(it, dict):
            warnings.append('audit163.json: dict 形式でない sheet_issue 要素を読み飛ばし')
            continue
        reason = str(it.get('reason', '')).strip()
        field = REASON_TO_FIELD.get(reason)
        if field is None:
            warnings.append(f'audit163.json: 未知の reason "{reason}"（対象外として読み飛ばし）')
            continue
        pid = str(it.get('product_id', '')).strip()
        vid = str(it.get('variant_id', '')).strip()
        row = str(it.get('row', '')).strip()
        if not pid or not vid:
            key = sheet_by_row.get(row) if row else None
            if key:
                pid, vid = key
            else:
                warnings.append(f'audit163.json: キー解決不能の sheet_issue (row={row}, reason={reason})')
                continue
        targets.append((pid, vid, field, reason, row))

    target_keys = {(pid, vid) for pid, vid, _, _, _ in targets}
    expected_keys = set(EXPECTED_87)
    if target_keys != expected_keys:
        miss_k = expected_keys - target_keys
        extra_k = target_keys - expected_keys
        if miss_k:
            warnings.append(f'audit sheet_issues に前回指摘87件のうち {len(miss_k)} キーの指摘がない（例: {sorted(miss_k)[:3]}）')
        if extra_k:
            warnings.append(f'audit sheet_issues に前回指摘以外のキーが {len(extra_k)} 件ある（例: {sorted(extra_k)[:3]}）')
    sheet_keys = set(sheet_by_key.keys())
    if sheet_keys != expected_keys:
        miss_s = expected_keys - sheet_keys
        extra_s = sheet_keys - expected_keys
        if miss_s:
            warnings.append(f'sheet_prices.csv に87対象のうち {len(miss_s)} キーが無い（例: {sorted(miss_s)[:3]}）')
        if extra_s:
            warnings.append(f'sheet_prices.csv に87対象外のキーが {len(extra_s)} 件ある（例: {sorted(extra_s)[:3]}）')

    # --- 261件の判定 ---
    verdict_rows = []
    for pid, vid, field, reason, row in targets:
        key = (pid, vid)
        va_row = a_variants.get(key)
        vb_row = b_variants.get(key)
        brand = brand_map.get(pid, '')
        sheet_rec = sheet_by_key.get(key)
        va_vals = {f: (normalize_minor(va_row.get(f)) if va_row else None) for f in PRICE_FIELDS}
        vb_vals = {f: (normalize_minor(vb_row.get(f)) if vb_row else None) for f in PRICE_FIELDS}
        sheet_vals = None
        if va_row is None or vb_row is None:
            cls = 'fatal_missing_input'
            basis = 'out-v8-a/b の variants.csv に該当バリアントが存在しない'
        elif sheet_rec is None:
            cls = 'sheet_row_missing'
            basis = f'sheet_prices.csv に該当行なし（監査の指摘 row={row or "?"}）。判定不可'
        else:
            sheet_vals = {f: sheet_rec[f] for f in PRICE_FIELDS}
            cls, basis = classify(field, sheet_vals[field], va_vals[field], vb_vals[field],
                                  sheet_vals, va_vals, audit_all_pass)
            srow = sheet_rec['row']
            if row and srow and row != srow:
                basis += f'。注意: 監査 row={row} と sheet_prices row={srow} が不一致（要確認）'
        verdict_rows.append({
            'product_id': pid, 'variant_id': vid, 'field': field,
            'sheet_value': fmt_minor(sheet_vals[field]) if sheet_vals else '',
            'v8a_value': fmt_minor(va_vals[field]),
            'v8b_value': fmt_minor(vb_vals[field]),
            'classification': cls, 'basis': basis,
            'audit_row': row, 'brand': brand,
        })

    # --- 監査未指摘の追加差分（sheet_prices.csv 全行 × 3フィールドの直接照合） ---
    audited_triples = {(pid, vid, fld) for pid, vid, fld, _, _ in targets}
    extra_list = []
    for key, rec in sheet_by_key.items():
        va_row = a_variants.get(key)
        if va_row is None:
            warnings.append(f'sheet_prices.csv: v8-a variants.csv に存在しないキー {key}（照合対象外）')
            continue
        for fld in PRICE_FIELDS:
            if (key[0], key[1], fld) in audited_triples:
                continue
            sv = rec[fld]
            av = normalize_minor(va_row.get(fld))
            if is_invalid(sv) or is_invalid(av):
                extra_list.append((key, fld, 'invalid_value'))
            elif sv != av:
                extra_list.append((key, fld, f'sheet={fmt_minor(sv)} v8a={fmt_minor(av)}'))

    # --- サイズ保留リスト（cm_status != MATCHED）＋ ガード ---
    pending_rows = []
    guard_stats = Counter()
    for key in sorted(a_variants):
        r = a_variants[key]
        status = (r.get('cm_status') or '').strip()
        if status == 'MATCHED':
            continue
        pid, vid = key
        brand = brand_map.get(pid, '')
        brand_u = brand.upper()
        src_url = (r.get('cm_source_url') or '').strip()
        ref_type = (r.get('cm_reference_type') or '').strip()
        size_system = (r.get('cm_size_system') or '').strip()
        guard, guard_note = '', ''
        if brand_u in GUARD_HOKA_UGG:
            if not src_url or ref_type.upper() in ('', 'UNKNOWN'):
                guard = 'HOKA_UGG_UNVERIFIED_REFERENCE'
                guard_note = '出典・体系不明の参照値は確定にしない（ガード）→ 保留'
            else:
                guard = 'HOKA_UGG_GUARDED'
                guard_note = 'HOKA/UGG は参照値を確定扱いにしない（ガード継続）'
        elif brand_u == GUARD_BIRKENSTOCK:
            if 'scoped' in (size_system + ' ' + ref_type).lower():
                guard = 'BIRKENSTOCK_SCOPED'
                guard_note = 'BIRKENSTOCK scoped のみ扱い（ガード準拠）'
            else:
                guard = 'BIRKENSTOCK_NOT_SCOPED'
                guard_note = 'scoped 判定不能のため保留（ガード: BIRKENSTOCK は scoped のみ）'
        guard_stats[guard or 'none'] += 1
        pending_rows.append({
            'product_id': pid, 'variant_id': vid,
            'sku': (r.get('sku') or '').strip(),
            'brand': brand,
            'size_original': (r.get('size_original') or '').strip(),
            'cm': (r.get('cm') or '').strip(),
            'cm_status': status,
            'cm_source_url': src_url,
            'cm_source_url_present': 'yes' if src_url else 'no',
            'cm_model': (r.get('cm_model') or '').strip(),
            'cm_age_group': (r.get('cm_age_group') or '').strip(),
            'cm_size_system': size_system,
            'cm_reference_type': ref_type,
            'guard': guard,
            'guard_note': guard_note,
        })

    # --- 集計と出力 ---
    cls_counter = Counter(r['classification'] for r in verdict_rows)
    examples = {}
    def _rowkey(r):
        s = r.get('audit_row', '')
        return int(s) if s.isdigit() else 10 ** 12
    for r in sorted(verdict_rows, key=_rowkey):
        examples.setdefault(r['classification'], []).append(r)
    brand87 = Counter((brand_map.get(pid, '') or '(brand 空または products 行なし)')
                      for pid, vid in sorted(target_keys))
    conclusion = draft_conclusion(cls_counter, variants_identical, audit_all_pass, extra_list)

    ctx = {
        'now': now, 'scope': scope, 'hashes': hashes,
        'variants_identical': variants_identical,
        'a_n': a_n, 'b_n': b_n, 'p_n': p_n, 'i_n': i_n, 'sheet_n': sheet_n,
        'results_n': res_n, 'res_bad': res_bad, 'sheet_issues_n': len(sheet_issues),
        'checked': checked,
        'cls_counter': cls_counter, 'examples': examples, 'brand87': brand87,
        'conclusion': conclusion, 'warnings': warnings,
        'pending_n': len(pending_rows), 'guard_stats': dict(guard_stats),
    }

    out_verdicts = base / 'recon-verdicts.csv'
    out_summary = base / 'recon-summary.md'
    out_pending = base / 'size-pending.csv'
    write_csv(out_verdicts, VERDICT_COLS, verdict_rows)
    write_csv(out_pending, PENDING_COLS, pending_rows)
    write_summary(out_summary, ctx)

    for w in warnings:
        print('[WARN] ' + w, file=sys.stderr)
    print(f'[OK] {out_verdicts} ({len(verdict_rows)}行)')
    print(f'[OK] {out_pending} ({len(pending_rows)}行)')
    print(f'[OK] {out_summary}')
    fatal = cls_counter.get('fatal_missing_input', 0)
    return 1 if (fatal or not verdict_rows) else 0


if __name__ == '__main__':
    sys.exit(main())

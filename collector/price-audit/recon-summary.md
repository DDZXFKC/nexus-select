# Shoe Palace 価格再照合サマリ（第2段階）

- 生成時刻(UTC): 2026-11-19T05:14:29+00:00
- ドライバー: recon_driver.py（1ファイル・標準ライブラリのみ。ライブ取得・カート・購入・価格反映なし）
- 監査スコープ（踏襲）: saved_snapshot_consistency_not_live_checkout_or_tax_verification
- 検証レイヤー: 価格（minor 単位）のみ。原価計算は実施しない。

## 入力検証

- out-v8-a vs out-v8-b `variants.csv`: バイト一致（sha256 a=b4a9f67719bc… / b=b4a9f67719bc…）
- out-v8-a vs out-v8-b `products.csv`: バイト一致（sha256 a=df14ec9a6c2b… / b=df14ec9a6c2b…）
- out-v8-a vs out-v8-b `issues.csv`: バイト一致（sha256 a=659e0afcd68a… / b=659e0afcd68a…）
- variants.csv: a=1796行 / b=1796行（1,796 期待。主キー重複は警告欄参照）
- products.csv: 163行（163 期待） / issues.csv: 428件（1,340 期待）
- sheet_prices.csv: 1796行（87 期待）
- audit163.json: results=1796件（非PASS 0件）/ sheet_issues=261件 / sheet_variants_checked=1796

## 分類結果（監査 sheet_issues = 87バリアント × 3フィールド = 261件）

| classification | 件数 | 意味 |
|---|---:|---|
| reproduced | 261 | 再現（シート側が古い／別時点の疑い） |
| rule_difference | 0 | 条件差（導出ルール差で説明可能） |
| non_reproduced | 0 | 非再現（v8-a のみの現象） |
| v8b_only_mismatch | 0 | v8-b のみ不一致（a/b 差異に起因。要調査） |
| audit_not_reproduced | 0 | 監査指摘が今回の照合では解消（シート更新済み等の疑い） |
| sheet_row_missing | 0 | sheet_prices.csv に該当行なし（判定不可） |
| invalid_value | 0 | 数値変換不能（要シート再確認） |
| fatal_missing_input | 0 | 入力欠落（v8 側にバリアントなし） |
| **合計** | **261** | |

## 代表例（各分類 最大3件、監査 row 昇順）

### reproduced（再現（シート側が古い／別時点の疑い））
- (7621953224910, 43203725656270) field=price_minor row=1026 sheet=16500 v8a=7997 v8b=7997 brand=HOKA
- (7621953224910, 43203725656270) field=compare_at_price_minor row=1026 sheet=0 v8a=16500 v8b=16500 brand=HOKA
- (7621953224910, 43203725656270) field=regular_price_minor row=1026 sheet=(空) v8a=16500 v8b=16500 brand=HOKA

## 差分87バリアントのブランド分布（products.csv の brand 列）

- HOKA: 87バリアント

## 結論（機械ドラフト）

- 再現 261/261 件：v8-a・v8-b いずれのスナップショット値とも不一致。raw と v8 の照合は監査全件 PASS のため v8 側価格レイヤーは raw と一致しており、**シート側が v8-a スナップショットより古い／別時点の値**である可能性が高い。

## ガード適用状況

- HOKA / UGG: 出典・体系不明の参照値は確定にしない（size-pending.csv の guard 列で管理）
- BIRKENSTOCK: scoped のみ扱い（scoped 判定不能は保留）
- 本ドライバーの価格判定は保存済みスナップショット照合のみに基づく。原価計算・参照値の確定・ライブ系操作を含まない
- size-pending.csv: 計 288 件（cm_status != MATCHED）
  - guard=HOKA_UGG_UNVERIFIED_REFERENCE: 284 件
  - guard=none: 4 件

## 警告・注意

- out-v8-a/issues.csv が 428 件（1,340 期待）
- sheet_prices.csv に87対象外のキーが 1709 件ある（例: [('4631411785774', '32576475955246'), ('4631411785774', '32576476020782'), ('4631411785774', '32576476086318')]）

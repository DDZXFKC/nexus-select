# Shoe Palace 価格検証 第2段階 再照合 実行結果（魔王）

- 実行: 2026-11-19（JST）
- ドライバー: GLM作成 `collector/price-audit/recon_driver.py`（1ファイル・標準ライブラリのみ）
- 出力: `collector/price-audit/recon-verdicts.csv`（261行）、`collector/price-audit/recon-summary.md`、`collector/price-audit/size-pending.csv`（288行）

## 結果

- 監査 sheet_issues 261件（87バリアント×3フィールド）は **全件 reproduced（再現）**。rule_difference / non_reproduced / v8b_only_mismatch / audit_not_reproduced は全て0件。
- 対象87バリアントは **全て HOKA**。
- sheet_prices.csv 全1,796行との直接照合でも、監査未指摘の追加不一致は無し。不一致はこの87バリアントに限定される。
- 代表例（row 1026、HOKA 7621953224910 / 43203725656270）: シート price=16500・compare_at=0・regular=（空）に対し、v8-a／v8-b とも price=7997・compare_at=16500・regular=16500。シート側の price に定価側の値が入り、セール価格が入っていない形。
- raw と v8 の照合は第1段階監査で全件 PASS のため、v8 側価格レイヤーは raw と一致。結論はドライバーの機械ドラフトどおり「シート側が v8 スナップショットより古い／別時点の値」の可能性が高い。
- size-pending.csv は288件（うち guard=HOKA_UGG_UNVERIFIED_REFERENCE が284件、none が4件）。ガードに従い確定値にはしていない。

## 入力の出どころ（再現性のため記録）

- out-v8-a / out-v8-b: 全ストア出力（out-v8-a・out-v8-b）から163商品スコープを抽出。両ランは元ファイル時点でバイト一致しており、抽出後も variants / products / issues すべてバイト一致（variants md5 d75ef2e80c10d45d0c28bc091ccca83b、issues md5 8b3640d7ccd7f89d879f702d90c1c292）。
- audit163.json: collector/price-audit/audit163.json（第1段階監査結果、そのまま使用）。
- sheet_prices.csv: 監査が比較した「シート」の特定から行った。監査スクリプト shoepalace_price_audit.py の audit_sheet は、WooCommerce形式CSV（Type=variation、sp_product_id / sp_variant_id / sp_price_minor / sp_compare_at_price_minor / sp_regular_price_minor）と比較する仕様。その実物は sp-repair-exec の sheet_repaired.csv（全9ラウンド）で、**全ラウンドとも監査の261件を完全再現**（row・キー・理由が全件一致）することを確認した。価格3列は reconcile の全ラウンドを通じて一度も更新されていない。書き出しには最新ラウンド out5-reconcile-b を使用し、同梱する（`collector/price-audit/sheet_prices_snapshot_2026-11-19.csv`）。

## 注意（前提との差異2点、いずれも判定への影響なし）

1. 初回実行では out163 の variants.csv を out-v8-a として使ったため「a/b バイト不一致」の警告が出た。out163 は cm_reference_type 列が無く cm 系フィールドが古い生成のものだったが、**価格3フィールドは全行で全ストア抽出と一致**しており、判定結果は再実行後も同一（261件 reproduced）だった。正式結果は全ストア抽出で再実行した本結果を正とする。
2. issues.csv は163スコープで428件（ドライバーの期待値1,340件は out163 世代の数）。判定ロジックは issues.csv に依存しない。

## 次の判断（GPTレビューへ）

- シート側（Woo取り込み用シート）の sp_price_minor 等の価格3列を、v8 の値で更新するかどうか。更新する場合は実シートへの書き込み担当は魔王。
- HOKA 87バリアントは全てセール価格帯の商品とみられる形（シート=定価、v8=セール価格）。シート生成側の価格マッピング（price に compare_at が入る経路）の確認が要るかどうか。

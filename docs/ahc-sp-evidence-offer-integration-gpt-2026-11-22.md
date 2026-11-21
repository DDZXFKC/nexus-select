# AFTER HOURS CLUB サイト継続実装：SP照合証拠→在庫確認候補（2026-11-22）

## 今回の新規実装
- `tools/ahc-stock-sp-evidence-offers-staging.php`: WordPressフィルター `ahc_inline_verified_offers` の候補供給元。既存の `tools/ahc-stock-sp-live-adapter-staging.php`（ライブ在庫/価格照会）に先行する証拠ゲート。
- `tests/test_ahc_stock_sp_evidence_offers.php`: PHP CLI向けの独立9シナリオテストコード。

## 判定
- 商品ID、親SKU `SP-<supplier_product_id>`、Woo variation IDおよびSKU、SP variant.idおよびSKU、公式URL、検証状態・出典を全て要求。
- CSVの同一variationの証拠0件または重複2件以上、列欠損、URL偽装、SKU相違は候補を出さない。
- **初期状態では原価供給フィルターの実装がないため候補0件。** `ahc_sp_verified_landed_estimate_jpy` が全費目検収済みの正の整数JPYを返したときだけ候補になる。
- 商品管理シートが正本。GitHubのCSVは2026-11-21の実測証拠スナップショットであり、シートの代替正本として扱わない。
- 77行の既存実証を再利用。未証拠1,636 variation（151商品）はHOLDのまま。
- このモジュールはWP書込み・価格更新・カート操作を一切しない。ライブアダプターと最終価格計算を接続しても、Woo本番に入れるのはステージングE2E後のみ。

## フィルター依存関係
1. `ahc_inline_verified_offers` → 本モジュール（CSV証拠＋全原価の見積り）。
2. `ahc_inline_check_one_offer` → 既存 `ahc-stock-sp-live-adapter-staging.php`（現在価格/サイズ別在庫）。
3. `ahc_inline_recomputed_sale_price` → オーナー承認の全費目販売価格式（**未実装**、nullによりfail closed）。

## 次のブロッカー
- 原価式の最終承認情報（為替、現地税、国際国内送料、関税、輸入消費税、代行費、決済手数料、利益下限/丸め）と検証済み商品ごとの費用。
- XServerステージングでCSV配置とライブHTTP疎通・Woo/Store API禁止経路のE2E。
- テストコードはGitHub登録済みだが、この実行ターンではXServer/実PHPへの接続実行は行っていないため、テスト合格と記載しない。

## 導入前の注意
- ステージングでのみ、非公開ディレクトリのCSVを `AHC_SP_EVIDENCE_CSV` に設定する。公開GitHubのURLをWordPressに直接読み込ませない。
- PHP追加モジュールは既存 `ahc-stock-inline-endpoints-staging.php` を正本として使う。`ahc-stock-inline-cart-gate-staging.php` は同時有効化しない（Ajax action競合）。
- UIと商品のサイズ値、SKU、商品ID、カート遷移挙動は変更していない。

# 手順1結果：Shopify取得スクリプトの特定（2026-11-16）

統合最終案（docs/integrated-nomaou-collection-final-2026-11-16.md）手順1の実施結果。

## 結論
- Shoe Palace／Kith／Patta の products.json 取得は、2026-11-15 にその場実行（使い捨てコマンド）で行われており、**取得スクリプトのファイルは残っていない**。
- 取得方法は確定している：各店の `/collections/<slug>/products.json`（limit=250・ページ送り）を取得し、生JSONを保存した。生JSONの実物が証拠として残っている。
- 変換側のスクリプトは残っている（下記）。

## 残っている実物（本フォルダに同梱）
- `build_shoepalace_prep.py`：生JSON→WooCommerceインポート用CSV変換（Shoe Palace分）
- `build_sp_final.py`：最終CSV生成
- `sample_shoepalace_products.json`：Shoe Palace（Vans Premium Old Skool 36コレクション）の生JSONサンプル（先頭2商品に切り詰め）。形式は標準Shopify products.json（id/title/handle/vendor/product_type/tags/variants[sku・price・compare_at_price・available]/images/options）。

## 生JSONの所在（VM ~/workspace/fl-scrape/、全件）
- Shoe Palace：shoepalace-ugg_raw.json（81商品）／shoepalace-hoka_raw.json（68）／shoepalace-vans-premium-old-skool-36_raw.json（14）
- Kith：kith_footwear_raw.json／kith_kith_raw.json／kith_mens-footwear-boots_raw.json（計2,019商品）
- Patta：patta_bottoms_raw.json／patta_patta-x-carhartt_raw.json／patta_tops-all_raw.json（計113商品）

## 含意
- 共通入口の shopify_json 取得部品は、新規実装とする（仕様は上記の確定済み方法どおり。サンプルJSONを形式のリファレンスとする）。
- 対象コレクション（slug）は店ごとに設定ファイルで持つ形にする。

報告：魔王ちゃん（2026-11-16）

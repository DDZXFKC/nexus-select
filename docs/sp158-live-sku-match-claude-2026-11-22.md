# SP 158 商品 実測 SKU 照合：全件 PASS（Claude、2026-11-22 02:40 JST）

relay-to-claude-stockcheck-start-2026-11-22.md（400f4a9）の 1 への回答。

## 結果
- **158 商品すべて、1,713 variation すべてが PASS。HOLD は 0 件。**
- 照合の条件：
  - サイト側の親 SKU `SP-<id>` が、Shoe Palace の実際の Shopify 商品 ID と完全に一致すること。
  - サイト側の variation SKU が、その商品の Shopify の `variants[].sku` と完全に一致すること。
  - サイズの文字は使っていない。元データ（サイト・シート・CSV）は何も変更していない。
- 結果ファイル：`data/xserver-export/sp158-live-sku-match-2026-11-22.csv`（1,713 行）。列は次のとおり。
  - サイト側：Woo の product_id、variation_id、SKU
  - Shopify 側（実測）：product_id、variant_id、variant_sku
  - 商品 URL、available、price（セント）、取得時刻

## 取得方法
- URL：GPT が商品管理ブックから出した `sp158-source-urls-from-sheet-2026-11-21.csv`（95b8dca）。
- iMac の Chrome で、Shoe Palace 公式の `/products/<handle>.js` を 158 回読んだ。
  - 1 件ずつ 1.5 秒間隔。2026-11-21 17:35:17Z〜17:39:37Z（JST 02:35〜02:39）。
  - HTTP エラー・403・429 は 0 件。
- 転送ミスがないか検算した。ブラウザ上の値とファイルの値が、次の 4 つすべて一致した。
  - variant 件数：1,713
  - variant_id の合計：75623306044824942
  - SKU の合計：35995790670（サイト側の SKU の合計とも一致）
  - available の件数：804
  - price の合計：23508531

## 注意
- available と price は、取得した時点の値。購入時には在庫確認で改めて読む（決定済みの仕様どおり）。
- 1,713 件中、その時点で在庫ありは 804 件。

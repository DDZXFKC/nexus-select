# Shoe Palace 158商品 SKU照合結果（2026-11-21）

## 判定
- Woo親商品: **158件** / Woo variation: **1,713件**（入力CSVの全行を分類）
- **PASS：7商品・77バリエーション**
- **HOLD：151商品・1,636バリエーション**
- 行単位の既存supplier証拠77件との厳密不一致：**0件**
- URL欠損：**0件**（158商品すべてsource_urlあり）

## 入力とロジック
- Woo元データ：`data/xserver-export/sp-variation-skus-2026-11-21.csv`
- 商品URL正本由来の一覧：`data/xserver-export/sp158-source-urls-from-sheet-2026-11-21.csv`
- supplierの実測証拠：`data/xserver-export/supplier-url-evidence-sample-2026-11-21.csv`（7商品77行、supplier variant SKU・variant ID・時刻含む）
- Woo親 `parent_sku = SP-<supplier_product_id>`、variation SKU完全一致、variation ID完全一致、URL完全一致、supplier variant ID非空、検証時刻非空、status=verified を全て要求した。
- 証拠のない1,636行は `SUPPLIER_VARIANT_EVIDENCE_MISSING` としてHOLD。URLがあることだけではPASSにしない。
- 同じSKUの出現やサイズ表記を使った推定補完はしていない。元のSKU、サイズ、商品IDに変更はない。

## 出力
- `data/xserver-export/sp158-variation-match-result-2026-11-21.csv`：全1,713行（Woo IDs・supplier IDs・URL・時刻・理由コード）
- `data/xserver-export/sp158-product-match-summary-2026-11-21.csv`：全158商品（PASS/HOLD内訳）

## 制約と続き
このPASSは**2026-11-21の保存済み証拠に対するID/SKUの照合PASS**であり、リアルタイム在庫・現在価格・購入許可の合格を意味しない。151商品のsupplier `/products/<handle>.js` に含まれる `id` と `variants[].sku/id` の実測取得・保存が次の工程。ここではライブ取得成功を主張しない。購入機能を本番解放していない。

カラー等の別用途のSP158 Local apply結果とは独立したSKU照合です。

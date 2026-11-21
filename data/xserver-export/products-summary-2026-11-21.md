# XServer 商品の実データ要約（Claude、2026-11-21 18:1x、Chrome＋管理画面 REST で取得）

- 取得元：after-hours-club.com の WooCommerce REST（/wc/v3/products?status=any）。全件 619 件。
- 商品 meta：**買付先URLは保存されていない**。
  - 入っているのは `_ahc_color_components_context`（shop_code・market・supplier_product_id）だけ。それも 158 件のみ（461 件には無い）。
  - **店は SKU の頭で分かる**。

## SKU の頭ごとの件数とメイン画像
| 頭 | 件数 | 公開 | 画像なし | 正方形 | 正方形でない | PNG | JPEG | WebP |
|---|---|---|---|---|---|---|---|---|
| FL（Foot Locker） | 345 | 125 | 0 | 341 | 4 | 341 | 3 | 1 |
| SP（Shoe Palace、SP-<Shopify product id>） | 158 | 158 | 0 | 4 | 154 | 2 | 156 | 0 |
| MERGED（統合済み） | 58 | 54 | 4 | 54 | 0 | 54 | 0 | 0 |
| CV（Converse） | 26 | 0 | 25 | 1 | 0 | 1 | 0 | 0 |
| NK（Nike） | 11 | 1 | 8 | 3 | 0 | 3 | 0 | 0 |
| NOTRE | 8 | 6 | 0 | 8 | 0 | 8 | 0 | 0 |
| PT（Patta） | 4 | 4 | 0 | 4 | 0 | 4 | 0 | 0 |
| CW・LN・PROTO・AS・EW・NB | 各1〜2 | — | 0 | 全部 | 0 | 全部 | 0 | 0 |

## 画像の是正対象（メイン画像。ギャラリーは別途確認）
- **SP の 154 件**：公開中。メインが Shoe Palace の JPEG（2329×1100〜1800 前後、グレー背景）。サイトで見えている「グレー・横長」の正体はこれ。
  - オーナー決定どおり、メーカー品番が一致する Stadium Goods の PNG に差し替える。
  - 21376 は済み。21357 は PNG だが 2048×1166 で、正方形でない。
  - SP の 2304×2304 の JPEG 3件（19189・19198・19207）と、2329×2328 の2件（19461・19480）は、正方形だが背景未確認。
- **FL の 4 件**：6374（WebP 1200×1500）、6546（JPEG 1280×736）、6640（JPEG 1280×721）、9834（JPEG 1280×656）。
- **画像なし 37 件**：CV 25（すべて下書き）、NK 8（下書き）、MERGED 4（下書き）。
- FL・MERGED・その他の PNG 1600×1600 は正方形。背景（透過・白）は実画面で抜き取り確認する予定。

## GPT 向け（verified_offers）
- 商品と買付先をつなぐ鍵は SKU。
  - FL-<FL の品番>
  - SP-<Shoe Palace の Shopify product id>
  - NOTRE-<メーカー品番>
  - MERGED-<元の SKU>
- WordPress 側に URL の meta は無い。対応表はシート／収集データ側から作る必要がある。
- 619 件の「商品ID・状態・SKU・画像形式・縦横」の一覧は、Claude が Chrome で読み出せる。CSV が要るなら言ってほしい。この作業環境から XServer へは直接つながらないため、ブラウザ経由になる。

# Shoe Palace 情報修正Python：実行報告2（再実行・魔王ちゃん→GPT検収依頼）

実行：2026-11-18 魔王ちゃん（VM上。原本・DB・シート・本番への書き込みなし）
対象コード：21caec84 の shoepalace_repair.py、86972dee の shoepalace_sheet_reconcile.py
依頼文書：docs/shoepalace-repair-execution-report1-gpt-review-2026-11-18.md（0b243759）

## 再実行1：混合25件 repair（前回と同一入力・cm参照なし）
- 終了コード0。25商品（在庫あり13＋なし12＋不明0）／225バリアント。2回実行で出力一致。入力ハッシュ前後一致。
- cm_status：MISSING 210、NOT_APPLICABLE 15。非靴（帽子・アパレル等）は NOT_APPLICABLE になり、cm_reference_missing は付かなくなった（issues は前回251→240）。
- 色：「100 Roses Mens Boxers (Red/Grey) Free Shipping」は color_name=Red/Grey で抽出できた（タグ Color_Grey／Color_Red と照合済み）。

## 再実行2：靴25件 repair（前回と同一入力・同一cm参照244行）
- 終了コード0。25商品／359バリアント。2回実行で出力一致。
- cm_status：MATCHED 241、MISSING 118（前回と同じ内訳。キッズC表記と換算表の範囲外）。
- 新規の指摘：color_name_unknown が前回1件→6件に増えた。全て New Balance「1000」シリーズで、題名の括弧色が具体的（例：Sea Salt/Astro Dust）なのに対し Color_ タグが汎用色（Beige／Red）で、タグ裏付けが取れず抽出を拒否している。タグ側の色が汎用分類である限り、この方式では正規の色名が落ちる。GPTの判断がほしい。

## 照合：既存3ブランド163商品と Woo prep CSV（--woo-prep）
- コマンド：shoepalace_sheet_reconcile.py --woo-prep --sheet shoepalace-woo-import-prep.csv --raw UGG raw／HOKA raw／Vans raw --cm-reference ＜Vans分のみ30行＞ --output ＜新規dir＞
- 終了コード0。2回実行で出力一致。
- 結果：163商品（在庫あり158＋全サイズ在庫なし5＋不明0）、1,796バリアント（在庫あり827）。シート行数1,959＝163＋1,796 で検算一致。
- sheet_issues は **0件**：SKU重複なし、親SKU（SP-<product ID>）と variation の Parent 一致、全行照合成功、未照合なし。
- 元CSVの保持：元20列・1,959行すべて保持され、元のセルの値の不一致は0件。追加された派生列は sp_ 16列（sp_product_id／sp_variant_id／sp_source_url／sp_color_name／sp_color_tags／sp_coupon_tag_codes／sp_coupon_tag_status／sp_description_ja／sp_description_ja_status／sp_size_original／sp_cm／sp_cm_status／sp_compare_at_price_minor／sp_regular_price_minor／sp_price_minor／sp_currency）。
- ハッシュ前後一致：prep CSV 9af214a1129f49aada66662528bc0ea3、UGG raw 0ffc22de25e52e9d0e3068214dcaf80c、HOKA raw e79b6b18cba3c00945101a013f25db10、Vans raw 7e28ec99d05b6d1d1d3aed4d8ca66fca。
- repair側issues 1,845件：cm_reference_missing 1,612、japanese_description_pending 163、color_name_unknown 70。
  - cm：今回の参照は Vans の30行のみ用意できたため、照合できたのは184バリアント。UGG と HOKA の公式サイズ表が手元の換算表資産（size_charts.json）に無く、1,612件が不足として残った。不足分の補充には UGG／HOKA 公式サイズ表の取得が要る（推測では埋めていない）。
  - 色：color_name_unknown 70／163件。再実行2と同じく、題名の具体色とタグの汎用色が一致せず抽出を拒否したものが中心とみられる。

## 残る論点（GPT判断待ち）
1. 色のタグ裏付け方式：タグが汎用色の商品で題名の具体色をどう扱うか（落としたままにするか、タグと併記するか）。
2. UGG／HOKA の公式サイズ表の取得を次工程にするか。
3. 検収合格なら、全店11,777件への展開手順。

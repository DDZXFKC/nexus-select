# GPT訂正：商品管理ブックのシートを正本として横断する（2026-11-21）

## オーナー指摘と責任
オーナー「CSVなんて使ってないやろがそもそも。シートのデータを横断してるやろ。誰がCSVの検証始めた？」。**旧CSVの検証を始めたのはGPT**であり、正本の取り違え。GPTが提出した`docs/gpt-response-owner-sp-rescrape-plan-2026-11-21.md`の「旧CSV検証」「11,756商品JSONを正本化」部分はオーナーの現行指示により**撤回**。同文書は履歴として残すが実行の根拠にしない。今後旧CSVの監査・URL再発掘・JSON正本化を実行しない。

## 正本
Google Sheets 「AFTER HOURS CLUB 商品管理」
https://docs.google.com/spreadsheets/d/1JdQnCxqS5gqrX6-4hcJBGEx_qFCuJsufUjedbkWnJsg/edit

店舗ごとのシートを維持して横断し、別店舗の在庫・原価・SKUを混合しない。
- `商品カラー`：A=shop_code、C=supplier_product_id、S=source_url。商品IDと買付URLの**同一行の直接対応**。
- `Shoe Palace店舗`：L=商品URL、その他K=カラー/N=仕入価格/O=通貨等。
- `サイズ別在庫`：A=商品ID、B=販売店、F=サイズ、G=在庫状態、H=価格、K=商品URL、L=確認日時。
- `商品マスター`：A=商品ID、D=販売店、L=商品URL。商品の総合管理。
- `SP価格検証`：A=親SKU、B=Shopify商品ID、数式・照合結果は既存のまま尊重。
- 設定シートも正本。未確定費用をゼロ扱いせず、販売判定は要求時点のライブ確認と切り分ける。

## GPTが今回Google Sheetsコネクタで直接実行した読み取り専用横断
- `商品カラー` A:C + S:T を行2～12,000で分割走査した結果、SP = **11,777商品ID**、IDごとのURL重複競合0件、URL欠損・形式不正0件。
- `Shoe Palace店舗` L列を行2～11,800まで分割読取し、URLを持つ行 **11,756件**、ユニークURL **11,756件**。
- `商品カラー`のSP商品ID→URLを`Shoe Palace店舗`URLと文字列完全一致で横断すると **11,710件**。
- これは**2シート間のURL一致数**であり、Woo/XServerの158 SP商品と1,713 variationの照合結果ではない。商品カラーと店舗シートの母集団の差分（現状67の商品カラー側IDと46店舗側URL）は、取得日や収集範囲の相違の可能性を含むので、未確認原因を推測で埋めない。
- どのシートも書き換えていない。

## 今後の処理順（GPT/Claude/Muse）
1. 商品管理ブック`商品カラー`のSP行について`shop_code=SP`かつ`supplier_product_id`とURLを厳密に保持し、Woo親SKU `SP-<supplier_product_id>`と結合する。結果はGitHubに記録するが、商品管理ブックのデータを無断改変しない。
2. `Shoe Palace店舗`・`商品マスター`・`サイズ別在庫`を、同じ仕入先の商品URL・shop_codeで横断する。`サイズ別在庫`のサイズ・在庫は履歴スナップショットであって、**Woo variation SKU / Shopify variant SKUの同一性を示すとは限らない**。不足する固有SKUはXServerの読み取りと公式Shopifyデータで検証して照合する。
3. XServer現行158商品の親SKU・1,713 variation SKUとの照合は実データが揃った範囲でのみMATCH。欠損は理由付きHOLD。既知の7商品77件のSKU完全一致は回帰基準。
4. ライブ在庫・価格は購入時に確認。シートにある「在庫状態」を現在の確実な在庫として扱わない。
5. 削除は具体的な対象と影響を提示し、オーナーの個別承認まで実行しない。旧CSVやWoo商品をこの判断で無断削除しない。

## 作業停止事項
**旧pricing CSVの検証、URL発掘、CSVからシートへの逆輸入、11,756商品JSONを新しい正本と呼ぶ作業を停止。** 必要があっても正本はGoogle Sheets、GitHubは指示と結果の正本として用途を分離する。2分ごとの自律監視はGPT会話自体ではできない。

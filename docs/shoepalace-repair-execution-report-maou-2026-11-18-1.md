# Shoe Palace 情報修正Python：実行報告1（魔王ちゃん→GPT検収依頼）

実行：2026-11-18 魔王ちゃん（VM上で実行。原本・DB・シート・本番への書き込みなし）
対象コード：collector/shoepalace_repair.py（38149972）、collector/shoepalace_sheet_reconcile.py（49794798）
依頼文書：docs/shoepalace-repair-execution-gpt-2026-11-18.md

## 実行1：GitHubサンプル
- コマンド：python3 shoepalace_repair.py --raw sample_shoepalace_products.json --output ＜新規dir＞
- 終了コード0。2商品／39バリアント（在庫あり23）。issues 41件（cm_reference_missing 39、japanese_description_pending 2）。
- 別出力先で2回実行し、出力は完全一致（diff差分なし）。入力ファイルのハッシュは実行前後で一致（a110353838e25e62ce738fd0cbde92fe）。

## 実行2：実データ25商品（最新バッチ page_1 の先頭25件、混合カテゴリ）
- 原本：iMac ahc_data/raw_json/Shoe_Palace/20261118_045314/page_1.json（250商品）から先頭25商品を抽出。抽出ファイルのハッシュ b6dd58ca72db1be16c19f54253bd5781、実行前後一致。
- 終了コード0。25商品（在庫あり13＋全サイズ在庫なし12＋不明0＝25で検算一致）／225バリアント（在庫あり31）。
- issues 251件：cm_reference_missing 225、japanese_description_pending 25、color_name_unknown 1。
- 定価の復元はバリアント単位で確認（例：GOORIN BROS帽子 price 1998／compare_at 5000 → regular_price_minor 5000）。先頭バリアントからの流用はしていない。

## 実行3：実データ靴25商品＋cm参照あり
- 対象：同page_1から RUNNING／LIFESTYLE かつ題名に Shoes を含む NIKE／JORDAN／ADIDAS／NEWBALANCE の25商品（359バリアント）。
- cm参照：既存の公式サイズ換算表 size-guide-data/size_charts.json の verified 行だけを brand,department,size_original,cm に変換（244行）。不完全な行6件は除外し、重複の競合はなし。※NEWBALANCE のキーは raw の vendor 表記「NEWBALANCE」に合わせた（換算表側のキーは new_balance で、そのままでは一致しない）。
- 終了コード0。25商品（在庫あり13＋なし12＋不明0）／359バリアント（在庫あり45）。2回実行で出力一致。
- cm入力できたのは241／359。残り118件は cm_reference_missing のまま空欄（推測で埋めていない）。不足の内訳の例：キッズの 4C／5C／6C 等のC表記（換算表にキッズ靴の行が無い）、換算表の開始サイズより小さい 4／4.5 の一部。
- issues：cm_reference_missing 118、japanese_description_pending 25。日本語説明の参照データは手元に無いため全件PENDING（未生成として扱った）。

## reconcile（シート照合）の結果：ID列の問題で未実行、判断依頼
- 現在のShoe Palaceの「シート」にあたる現物は、サイト取り込み用CSV shoepalace-woo-import-prep.csv（親＋バリエーション、SKU付き1,959行）で、Googleスプレッドシート側にShoe Palace専用タブは無い（商品マスターワークブックのタブは商品マスター／サイズ別在庫／Notre収集／Converse収集など）。
- このCSVの列は ID（Woo側ID）／Type／SKU／Name／Published／… で、Shopifyの product_id／variant_id 列が無い。そのため reconcile は商品名で推測せず未実行にした。
- ただし SKU は安定したキーになっている実測がある：UGG raw のバリアントSKU 556件すべてが、このCSVのSKU列に存在した。
- 判断依頼：reconcile を SKU キーでも実行できるようにするか、それとも別のシート（product_id列を持つもの）を正とするか、GPTの指示がほしい。

## 気づいた点（GPTへの確認）
1. 非靴（帽子のOSサイズ、アパレル等）でも全バリアントに cm_reference_missing が付く（実行2で225／225）。cmの不足扱いは靴だけに限るべきではないか。
2. 色の分離ができない例：「100 Roses Mens Boxers (Red/Grey) Free Shipping」。括弧が題名の末尾にないため color_name が取れない。タグには Color_Grey があり color_tags には入っている。
3. cm換算表のブランドキーの表記ゆれ（new_balance と NEWBALANCE）。参照CSVを作る側で vendor 表記に合わせる前提でよいか。

## 未完了
- reconcile の実行（上記の判断待ち）。
- 全件（11,777件）への拡張は、GPTの検収合格のあとで。
- 日本語説明文の生成は対象外（参照なしのため全件PENDING）。

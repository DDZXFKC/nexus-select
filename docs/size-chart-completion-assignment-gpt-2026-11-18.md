# ブランドサイズ表の完成：GPTへの作成依頼（2026-11-18）

## オーナーの言葉（原文）

- 「サイズ表は商品に紐付けるより、ブランドに紐付けた方がよさそうだね」
- 「このサイズ表もシートに保存な」
- 「シートで、ブランド、キッズかメンズかを判定してサイズ表と紐付け」
- 「そのサイズ表完成させようか」
- 「取り扱いブランド、全部書き足して」
- 「gptに作らせて」

## 依頼内容

ブランド×区分（Men／Women／Kids）の公式サイズ表データを、取り扱いブランド全部について完成させてください。成果物はCSVファイル（チャットでダウンロードできる形）でください。列は brand,department,size_original,cm,source_url の5列です。

## ルール

- 出典はブランド公式のサイズチャートのみ（公式地域サイト・公式日本サイトを含む）。転載サイト・販売店の換算表は使わない。
- cmはJP/CMラベル値（靴の箱・タグに印字される日本サイズ）を使う。公式表に足長（foot length）しかないブランドは、cmを空欄にし、その旨をサマリーに書く。足長で埋めない。
- 推測・他ブランドの表・一般的な換算式で埋めない。公式表に無いサイズは入れない。
- キッズのsize_originalは C／Y 表記（例：10.5C、3.5Y）で、Shoe Palaceのバリアント表記に合わせる。
- サイズの範囲は公式表の全範囲を入れる（現在データで不足している範囲だけでなく、表として完成させる）。

## 作成済み（13ブランド・592行、専用ブック「ブランドサイズ表」に保存済み）

NIKE（Men/Women/Kids）、JORDAN（Men/Women/Kids）、ADIDAS（Men/Women）、NEWBALANCE（Men/Women/Kids）、VANS（Men/Women/Kids）、ASICS（Men/Women）、ON RUNNING（Men/Women）、PUMA（Men/Women/Kids）、CROCS（Men/Women/Kids）、SALOMON（Men/Women）

この13ブランドは作り直し不要ですが、次の不足分は追加してください。
- ADIDAS Kids（公式キッズ表にJPラベル値が無いことは確認済み。あれば出典付きで、無ければその旨をサマリーに）
- ASICS Kids、ON RUNNING Kids
- VANS Men（6.5未満と12.5等のハーフ）、VANS Kids（10C以下のトドラー範囲）、VANS Women（12以上と5未満）
- NEWBALANCE Kids（日本公式表の飛び：2C、6C、12.5C、2.5Y、6Yは公式表に無い。別公式出典があれば）
- PUMA Men（15以上と4未満）、PUMA Women（5.5未満と11.5以上）、PUMA Kids（10C未満）
- CROCSのハーフサイズ（公式に無ければ無しでよい）

## 新規に作成するブランド（Shoe Palace取扱分、残り不足件数つき）

- CONVERSE Men 1,084／Women 198／Kids 242（公式cmは足長のみと確認済み。JPラベル値の公式出典があればそれを使う）
- HOKA Men 903／Women 549／Kids 56（ブランド表としての作成は可。適用側の注意は魔王ちゃん側で扱う）
- SAUCONY Men 873／Women 93／Kids 179（SAUCONY KIDS表記分を含む）
- REEBOK Men 348／Women 83／Kids 65
- BIRKENSTOCK Women 249／Men 83（EU表記が主なら、US→cmの公式対応を出典付きで）
- UGG Men 102／Women 188／Kids 240（ブランド表としての作成は可）
- CHAMPION Kids 228／Men 136
- ANTA Men 212／Kids 30
- VEJA Women 209／Men 40
- RALPH LAUREN Men 175
- UNDER ARMOUR Men 145／Kids 24
- TIMBERLAND Men 105／Kids 99
- TEVA Men 75／Women 68
- DC SHOES Men 70
- DR. MARTENS Men 65／Women 28
- ED HARDY Kids 53／Women 22
- LOCI Women 47／Men 11
- BBC INTERNATIONAL Kids 44
- PF FLYERS Men 27
- OFF WHITE FTW Men 27
- HEELYS Kids 25
- MAISON ARTICLE Men 24
- TRETORN Men 22／Women 14
- OOFOS Men 22
- HEY DUDE Men 12

## 成果物

1. CSVファイル（上記の新規ブランド＋不足分追加分。作成済み13ブランドの既存行は含めない）
2. チャット本文に短いサマリー：ブランドごとに「完成／JPラベル値が公式に無く空欄／公式表が見つからない」のどれかと、出典URLの一覧

完成判定はGPT側でお願いします。魔王ちゃんは受け取り後、専用ブック「ブランドサイズ表」へ統合し、repairへ再適用して結果を報告します。

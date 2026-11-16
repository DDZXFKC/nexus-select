# 各ショップの収集方法（実績・2026-11-16時点）

魔王ちゃんから3者（GPT／Claude／GLM）への事実共有。
先日の欠落ルール相談では「実際に何を使って取ったか」を説明していなかった。統合ルールの前提として、以下を正とする。

## 店舗別

### BSTN（収集済み2,172件）
- 方法：チャッピー（GPT）が設計・作成したPythonコレクターで収集（2026-11-13〜14、実行は魔王ちゃんがiMacで実施）。結果はSQLite DBに保存。
- 現在のデータは、このDBから読み出して変換したもの。新規のライブ取得はしていない。

### Foot Locker
- 第1弾（432件）：スクリプトで検索ページのHTMLを直接取得し、ページ埋め込みの商品JSONを解析して抽出。
- 第2弾（メンズ13ブランド評価順4,510件・全94ページ＋他カテゴリーの上位48件セット）：Chrome拡張「Web Scraper」を自宅iMacのChromeで魔王ちゃんが実行（サイトマップ名 footlocker-com-2026-11-15）。
- 備考：Foot Lockerは規約で自動収集が禁止されている。評価順の取得は、リスクを提示した上でオーナーが明示的に規約ルールを上書き指示した例外。

### Notre（342件、ベストセラー順）
- 方法：スクリプトでコレクションページHTML（sort_by=best-selling）を取得し、埋め込みデータ（initData）から順位と商品名を抽出。価格・定価は products.json で補完。

### Converse（US公式、192行／実質約40種）
- 方法：スクリプトの直接取得が403で不可だったため、実ブラウザで開き、評価順（Ratings High to Low）に並べ替えて、グリッドの商品タイルを読み取って記録。

### Shoe Palace（163件＝UGG 81＋HOKA 68＋Vans Premium Old Skool 36 14）
- 方法：Shopifyの /collections/＜コレクション＞/products.json（limit=250・ページ送り）で全件取得。バリアント別SKU・価格・在庫可否・画像・説明文（body_html）まで取得できている。生JSONとCSVを保存済み。
- **今回のcm欠落の発生箇所**：products.jsonの元データに「cm」という項目は最初から存在しない。cm併記は投入準備の段階で、ブランド別サイズ換算表（自前で作成した参照表）を引いて生成していた。UGG乳児サイズ（1C/2C/3C）の行が換算表になかったことが欠落の発生箇所であり、スクレイピングで取りこぼしたのではない。

### Kith（2,019件）
- 方法：Shoe Palaceと同方式。Shopifyの /collections/＜slug＞/products.json で全件取得（kithコレクション／footwear／boots等）。

### Patta（113件）
- 方法：同方式。Shopifyの /collections/＜slug＞/products.json（pattaclothing.us）で取得。

### 6pm（1,286件＝バッグ535＋靴651＋ドレス100）
- 方法：自作スクリプト（sixpm_pull.py等）で、一覧ページの構造化データ（products.list）と商品ページを取得。

### Onitsuka
- モデル別件数のみ把握。商品データは未収集。

## 混同しやすい別系統について
GLM製の商品発掘システム（sourcing）は、ブランド公式サイトからの直接取得を試みた別の系統で、adidas／ASICS／HOKA／Converse／Salomonの公式サイトは403等で取得不可と確定している。上記の「今ある商品データ」は、この系統では取っていない。

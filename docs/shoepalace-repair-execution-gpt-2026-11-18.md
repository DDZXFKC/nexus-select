# Shoe Palace 情報修正Python：実行・検収依頼（GPT→Muse）
対象はShoe Palaceのみ。GPTが実装担当。Grokは除外。画像加工、価格計算、本番書込、他店の調査は対象外。
## 1. 既存資産の確認
- iMacの保存済み最新バッチ ahc_data/raw_json/Shoe_Palace/20261118_045314/page_1.json〜page_48.json（報告11,777件）を読み取り専用で使用。旧実行分と混ぜない。
- 現在のShoe PalaceシートをCSVとして別ファイルに書き出す。既存タブ名、列名、行粒度、商品ID/variant IDの有無、取得バッチを確認する。3ブランド163件のシートなら対応する3ブランド原本を使い、全店バッチと同一範囲だと仮定しない。
- 既存の公式サイズ換算表（kids-size-cm-chart-2026-11-16.md等）を確認。ブランド・サイズ体系・対象年齢/性別・モデル差と公式出典を保ったまま、曖昧な対応は採用せず、実際に一意と確認できる行だけ brand,department,size_original,cm のCSVに変換。UGG乳児サイズの欠落は推測で埋めない。現行のキーが粗くて区別できない場合はGPTへ具体例を報告し、該当行を保留。
- 日本語説明の既存データがあれば商品IDと説明文の対応を確認して product_id,description_ja のCSVを用意。なければ未生成として扱う。
## 2. まず既存GitHubサンプルで実行
branch integration/grok-review の collector/shoepalace_repair.py (38149972) と collector/shoepalace_sheet_reconcile.py (49794798) を同一ディレクトリに取得。
python3 collector/shoepalace_repair.py --raw docs/ahc-collect/sample_shoepalace_products.json --output /tmp/sp-repair-sample-20261118
出力先は未存在の専用ディレクトリ。原本・DB・シートを書き換えない。次に現物シートのID列を確認して、対応する原本から20〜30商品の全variantを抽出し実行する。
python3 collector/shoepalace_sheet_reconcile.py --sheet "$SHEET_CSV" --product-id-column "$PRODUCT_ID_COLUMN" --raw "$SAMPLE_RAW" --cm-reference "$CM_CSV" --output "$NEW_OUTPUT_DIR"
variant単位シートなら --variant-id-column に現物列名を追加。日本語参照があれば --ja-reference を追加。シートに安定したIDがなければ商品名で推測せず、現物ヘッダーと匿名化した数行をGPTへ。実行前に各変数の実パスを確認。シート範囲に対応する原本のみ使用。
## 3. 受入
- 原本と既存シートのハッシュが実行前後一致。既存シートの元列・元行を維持し、追加の sp_ 派生列と変更一覧を確認する。既存の欠落・誤りがある列そのものへの適用は現物の列対応を確認してから（現行コードは派生列出力のみ）。
- 商品ID・variant IDが完全一致すること。重複・未照合・不足は報告。全商品数＝在庫あり＋全サイズ在庫なし＋不明。サイズ別価格・定価を先頭variantから流用しない。compare_at_priceの0と未取得を区別。
- 色の末尾括弧が本当に色かを現物のタグ・商品属性と照合し、色以外の括弧は誤分離しない。現行コードの候補出力を確認する。
- Code_タグは商品側の証拠であって適用確定ではない。価格への割引適用なし。URLはhandleから組み立てたものを既存URLと照合する。
- 公式cmの未照合は空欄＋理由。非靴や異なるサイズ体系は推測換算なし。日本語説明の原文との対応、未生成の区別。画像情報保持、画像加工なし。
- 同一入力を別出力先で2回実行し、出力の一致確認。実行コマンド、終了コード、件数、欠落一覧、現物の列対応、代表例、差分を非機密範囲でGitHubのdocsへ記録。実行失敗ならtracebackと入力構造を共有。
## 4. 完成判定
少数実データの結果をGPTが検収し、必要な修正を実施。合格後に同一店舗の対象全件へ拡張する。現時点で実シートヘッダー、公式換算表、iMacの実行結果はGPT未確認。全件完了とは判定しない。オーナー操作・追加承認は不要。Museが実行し、結果はGitHubで共有する。
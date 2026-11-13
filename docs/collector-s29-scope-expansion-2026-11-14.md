# §29 対象拡大の設計と実行（オーナー直接指示による）

背景：オーナーが「対象を広げる設計を急げ」と魔王ちゃんへ直接指示。チャッピー側の追加実装が0件だったため、既存の検証済みコードの範囲内で魔王ちゃんが設計・実行した。新規コードは書いていない（使ったのは stage3_catalog.py の既存スコープ規則と設定の追加だけ）。

## 設計
- 店舗は増やさない。新規11店舗の検証結果どおり、許可根拠があるのはBSTNのみ。
- BSTN内の対象を、既存の listing_scope が許す範囲で広げる：
  - 性別：Men に加えて Women / Kids
  - カテゴリー：All Products 配下の Footwear / Apparel / Accessories / Lifestyle
- カテゴリー名は推測ではなく、BSTNの一覧ページ自体に含まれるリンクから実在分を列挙して確定した（Men 26件・Women 19件・Kids 11件のカテゴリー値を確認。ログ categories.log）。
- 実行単位はカテゴリーごと：discover が全ページを歩き、安定性を確認してから候補をキュー化し、先頭10商品を詳細処理する（--limit 10）。予算は1実行あたり300リクエスト、間隔5秒は維持。全件HOLD・公開0は不変。

## 第1バッチ（実行中〜完了分は実行報告で追記）
1. Women ~ All Products ~ Footwear
2. Men ~ All Products ~ Apparel
3. Kids ~ All Products ~ Footwear

## 残りの拡大候補（同方式で継続可能）
- Men/Women/Kids × Accessories、Men/Women × Lifestyle、Women Apparel
- 既存 Men Footwear の詳細処理の継続（キュー再開）

各カテゴリーの商品数・ページ数と詳細処理結果は実行ログ（s29-expand.log）と各出力フォルダの report.json に残る。

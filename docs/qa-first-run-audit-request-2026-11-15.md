# QA初回実行の結果と監査依頼（2026-11-15）

宛先：チャッピー（監査担当）。参考：Claude（実装担当）。
実行者：Claude Code（iMac）。登録：魔王ちゃん。

## 実行概要

- 実行ID：20261115-071551（2026-11-15 07:15:51〜08:05:14 JST、約50分）
- 検査：data / crawl / purchase の3種を実施し完走
- 巡回：1,473ページ、画像8,783枚
- 結果：CRITICAL 1 / HIGH 796 / MEDIUM 4 / LOW 0 / REVIEW 0（合計801件、新規1・既存800、解決2）
- ベースライン保存済み（~/ahc-qa-reports/state/baseline.json）。レポート実物は公開リポジトリに載せない方針のため iMac の ~/ahc-qa-reports/runs/20261115-071551/ に保管（report.html / findings.json / findings.csv）
- 注意：カテゴリー階層検査（category_spec）は本実行の開始後に追加されたため、本結果には含まれない。次回実行から有効。

## 内訳と魔王ちゃんの一次切り分け

### 1. BRAND_RESIDUE：727件（本文363＋ページタイトル364）
「NEXUS SELECT」表記の残存。タイトルとフッターの名称統一はオーナー判断待ちの別件であり、監査対象からは外してほしい（件数の大半を占めるため分離して数えた）。

### 2. PURCHASE_FLOW：7件
- webkit/PC のみ CRITICAL 1件：「カートに商品が入っていません（追加1件、カート0行）」
- 他の3組合せ（webkit/SP、chromium/PC、chromium/SP）はカート通過後に同じHIGH 2件ずつ：
  - チェックアウトの入力欄（billing_last_name）がありません
  - 注文追跡ページが表示されません（HTTP 404、/order-tracking/）

監査で判定してほしい点：
- billing_last_name と /order-tracking/ は、サイト側の不具合か、検査側の想定（項目ID・URL）が実サイトと食い違っているだけか。実サイトのチェックアウト項目構成と注文追跡ページの正しいURLを確認したうえで判定してほしい。
- webkit/PC のカート失敗は、他の組合せでカートが通っているため、WebKit特有の実不具合か検査環境（Cookie/セッション）の問題かの切り分けが必要。

### 3. 空カテゴリー（KIDS）へのリンク：31件（INV_EMPTY_CATEGORY_HIDDEN）
トップページと KIDS カテゴリー配下のページ同士に、商品0件の /product-category/kids/ へのリンクが表示されている。確定事項「空カテゴリーは非表示」との不整合。トップページのKIDS COLLECTIONカードが主因とみられる。実サイト側の修正候補。

### 4. 画像・取得エラー
- IMAGE_HTTP_ERROR 16件：全て /brands/ ページ上の画像（ブランドロゴ）が表示されない。実サイト側の不具合候補。
- FETCH_ERROR 14件：https://kaitsuke-shop.local/ への取得失敗（巡回ベースは http）。検査環境起因の可能性が高い。監査で判定してほしい。
- IMAGE_SIZE_FILE_MISSING 4件（MEDIUM）＋画像404 2件：いずれも商品「Vans LX Old Skool 36 Rivets」の画像。縮小サイズ（medium / thumbnail / woocommerce_thumbnail / woocommerce_gallery_thumbnail）のファイル不足と、画像ファイル自体の404。実サイト側の不具合候補（対象はこの1商品に集中）。

## 監査への依頼事項
1. 上記2と4（FETCH_ERROR）について「実不具合／検査側の想定違い／検査環境起因」の判定。
2. 実不具合と判定したものの修正優先順位（公開前必須か、公開後でもよいか）。
3. 検査側の修正が必要な場合は、Claudeへの修正指示の形で返してほしい。

サイト実物・テーマ・商品データへの変更は本メモでは行っていない。

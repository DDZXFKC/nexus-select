# Shoe Palaceへの実HTTP通信テスト結果（2026-11-22 JST）

## 結論
**Shoe Palace公式のShopify商品JSONに対する外部環境からの実HTTP通信テストはPASS。** GitHub Actions runnerから公式URLにアクセスし、HTTP 200、商品ID・SKU・サイズ別Shopify variant ID・在庫真偽・価格セントを実データと照合した。最終試験 run [44934223004](https://github.com/DDZXFKC/nexus-select/actions/runs/44934223004) は **completed/success**。その前の同URL単一バリエーション実HTTPテスト run [44934162649](https://github.com/DDZXFKC/nexus-select/actions/runs/44934162649) もsuccess。

## 実測通信
- 実行：2026-11-21 18:12:26 UTC（2026-11-22 03:12:26 JST）
- 実行主体：GitHub Actions Ubuntu runner。モック、保存HTML、過去CSVのみの検証ではない
- 対象：`https://www.shoepalace.com/products/ugg-1178111-san-zora-ballet-flat-womens-sandals-chestnut.js`
- HTTP応答：**200**
- Content-Type：`text/javascript; charset=utf-8`（本文はJSONとして読み取り成功）
- 応答バイト数：**11,458**
- 商品ID：保存済みSP商品IDと一致
- 商品内variation：**13件**を取得し、Woo SKUとShopify variant IDを全件比較。**13件すべて一致**
- 在庫あり：**4件** / 在庫なし：**9件**
- 最初の照合variant：在庫なし、価格13,500セント（USD 135.00として使うときは独立した店通貨の確認が必要）
- JSON本文SHA-256：`dc6565da328c248aa873f093160cfe95459cf01d1394cfb375fb0115805a04ea`
- 取得方法：正規のHTTPS GET、Accept: application/json、リダイレクト拒否、12秒タイムアウト、最大1,000,000バイト、リトライなし、1回のHTTPで13variation検証。403/429回避やキャプチャ迂回なし

## 変更・保存
- `.github/workflows/sp-live-connectivity-one-shot.yml` — 公式サイトからワンショットで取得、厳密なID/SKU、price/available型検証、応答SHAをログに残す。
- コミット `777e640` に単一バリエーション検証を登録、`ff3fcf0` に同一レスポンスの13variation全件検証を追加。両実行PASS。
- WooCommerce商品、SKU、サイト本体、カート状態、XServer設定、公開状態は変更していない。

## 完了の境界
「**Shoe Palaceへの実際の通信テスト**」のGitHub Actions runner実HTTP接続・商店応答形式・サイズ別variant ID/SKUと在庫/価格の実測テストは完了。ただし、158商品全件に再アクセスしたわけではなく、今回の対象は**1商品13variation**。過去Claude実測158商品1,713件の照合は別途 `f23c996f` の記録。Shoe Palace在庫値は観測時点のもので在庫を保証しない。

**XServer実機PHP `wp_safe_remote_get` からの通信可否、XServerで有効化した買付先照会コード、新UIからの実在庫確認→カート追加、端末表示テストはまだ別工程。** この単体実HTTP試験をXServer受入合格やサイト公開合格と取り違えない。

## 次の残存タスクへの引継ぎ
XServer差分/旧ハンドラーの競合と新UIを確認してから、ログに個人情報を残さず、ステージングで同一1商品に対するPHP `wp_safe_remote_get` を実機検証。その後、在庫ありと品切れの両結果と、別ユーザーが24時間の共有印に妨げられず再チェックできること、400円価格変更・価格差未満・カート許可・キャンセル・直接Woo/Store API拒否をPCとモバイルで検収する。

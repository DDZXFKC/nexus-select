# 在庫確認サーバー側：Claudeレビュー反映結果・XServer反映ゲート（2026-11-21）

## Claudeへの回答（docs/claude-ack-review-2026-11-21.md）

1. **初回ゲストセッション：修正済み（GitHub）**。start内で `WC()->session->set_customer_session_cookie(true)` を呼び、step以降でセッションハッシュを照合。模擬結合テスト合格。ただしXServerシークレットウィンドウでの実測は未実施。
2. **掲載価格表示：ClaudeのUI側修正を採用**。GPT側で重ねて変更しない。
3. **SOLD OUT表示：Claudeの `woocommerce_available_variation` を維持**。GPT側は当該フィルターを追加しない。GPT側の印は `_ahc_inline_oos_until`。
4. **候補ゼロ：`no_candidate`**。stepの早期判定で返す。16件のモックに検証追加。
5. **simple商品：対応**。variation_id=0で許容し、該当商品の在庫と価格を検証。単品も購入許可とカート投入を通す。
6. **`ahc_sc_add_to_cart`：実装**。入力 permit/accept_quote/nonce；Wooカート追加、サーバー側許可チェック、価格保存、5分トークン、同一セッション、使い回し拒否、60分カート価格保持、旧カート全面禁止との接続を実装。
7. **所有境界維持**。GPTは `tools/ahc-stock-inline-endpoints-staging.php` とテストのみ編集。ClaudeのUIファイルは未変更。

## コード・テスト
- `tools/ahc-stock-inline-endpoints-staging.php` （ステージング）
- `qa/php-tests/stockcheck_inline_endpoint_stub_test.php`
- `.github/workflows/stockcheck-inline-php.yml`
- GitHub Actions https://github.com/DDZXFKC/nexus-select/actions/runs/44886410877 ：PHP構文・模擬結合**16件合格**。
- 未接続：`ahc_inline_verified_offers`、`ahc_inline_check_one_offer`、`ahc_inline_recomputed_sale_price` の実データ・実サイトに紐づくアダプター。**価格不明や買付先ゼロは失敗で閉じる。買付可能と誤判定しない。**

## 重要：二重実装衝突
`tools/ahc-stock-inline-cart-gate-staging.php` は独立した別ステージング版で、`wp_ajax_ahc_sc_add_to_cart` にもハンドラを登録する。**両方を同時に有効化すると2重実行・カート重複追加等の重大リスク**。今回の`tools/ahc-stock-inline-endpoints-staging.php`が、start/step/add_to_cart/カート検証を1ファイルでまとめ、Mock 16件検証済み。**一時的な統合候補はこちら**とするが、XServerの現在の実ファイル・Wooバージョン・カスタマイズ確認前の最終採用は未決。別実装は同時に読み込まない。

## XServer反映前の必須条件
1. サーバーの本番稼働中の`ahc-stock-check.php`、ロード順、Woo Store API、PHPバージョン、既存購入導線を差分比較。バックアップ・ロールバックを確保。
2. 実在SKUと買付先URLの照合データ、同一サイズ/カラーの在庫確定、現地最新価格、全費用を含む自社EC販売価格計算を実データと接続。現在のフィルターは未接続であり**実運用不可**。
3. 1つだけのサーバー側エンドポイントファイルを採用し、Claude所有`ahc-stock-check-ui.php`/`js`と同時に適用。
4. PC/スマホ、シークレット初回ゲスト、通常/Store API無許可追加拒否、価格400円・価格確定・注文時価格持続、SOLD OUT 24時間、二重クリック、カート60分/期限切れ等のE2E実測。
5. Basic認証/noindexの維持と非公開状態でのテスト。実測が済むまで公開しない。

## 画像の引継ぎ確認
Claudeの`docs/image-fix-log-2026-11-21.md`：商品21376はStadium Goods PNGを白キャンバスに配置し、PC実画面は確認済み。スマホ幅・iMac画像マスター保存・全件監査は未完了。GPTは画像編集とClaude UIファイルに触れない。

**状態**：GitHubのステージング実装＋模擬テスト完了。XServer反映・実仕入先への接続・実カート・実画像全件確認は未完了。

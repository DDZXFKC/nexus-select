# AFTER HOURS CLUB — SP158実測SKUと原価式の実装・接続完了記録（2026-11-22）

## 対象と実施結果
Claude実測 `f23c996f` の `data/xserver-export/sp158-live-sku-match-2026-11-22.csv` を正本照合証拠として使用。全 **158 Woo親商品、1,713バリエーション PASS**。旧7商品/77行のサンプルだけを使う実装から、全1713件の固定的な識別子証拠を使う実装に拡張した。

GitHubコードとして以下のつなぎ込みを完成：
1. `tools/ahc-stock-sp158-owner-bridge-staging.php` — Woo親product_id/variation_id、親SKU、variation SKU、Shopify商品ID/variant ID、公式URLを**全件検証済みCSV**から厳格に結合。ファイルは1,713行/158親商品以外・重複/不一致/欠損では全件不許可。古い在庫値は使わない。
2. `tools/ahc-stock-sp-live-adapter-staging.php` — カスタマーの照会時にShoe Palace公式 `/products/<handle>.js` を取得。要求バリエーションID/SKUと価格・在庫を再照合。通信不能・429・不一致は確認不能。
3. 同bridgeの `ahc_inline_recomputed_sale_price` — **今回オーナー再確認の計算式**を買付先の**ライブ取得USD価格**に適用。
4. `tools/ahc-stock-inline-endpoints-staging.php` — 一時的な購入許可、WooカートにおけるID/サイズ・価格の保存、再利用防止を担当。既存機能を利用。
5. `tools/ahc-sp158-staging-loader.php` — 必要3モジュールだけをロードするステージング用のガード付きローダー。既定では無効。
6. `tests/test_ahc_sp158_owner_bridge.php` — 実データ1713行の完全性、商品ID/Shopify ID/SKU検証、改ざん/欠損時拒否、価格の境界を検証。
7. `qa/php-tests/stockcheck_sp158_full_chain_stub_test.php` — オフラインでWoo在庫確認開始→実1713行証拠から候補選出→模擬SP Shopify HTTP→正しいライブ価格で原価/販売価格→価格承認→カート追加→トークン使い回し拒否、売切れ・再確認を検証。
8. `.github/workflows/stockcheck-inline-php.yml` — 上記をGitHub Actionsの自動試験に追加。

## 原価および販売価格：オーナー指定・明示的な固定ルール
```
原価（円、丸め前） = 現地商品価格（USD） × 158 × 1.02 + 2,200 + 1,500 + 60
販売価格（税込表示予定の円単位） = 100 × ceil((原価 ÷ 0.785) ÷ 100)
```
四捨五入した表示原価から販売価格を計算せず、丸め前原価を使い、最後に100円切り上げ。
検算：現地価格 USD 100.00 → 25,400円、USD 125.99 → 30,700円。
計算はUSDセントの整数で演算し、浮動小数点誤差を回避。計算式の為替・カード率・固定額・除数は今回のオーナー指定値を使用し、独断変更しない。
**クーポンの自動適用はしない**。別料金/税額が発生するルートでは、この固定式にすべて含まれるかの商用確認が必要。商品・URL・サイズ・SKU・Woo実価格の一括書換えは行わない。

## 在庫と価格の時点
CSVの `available_live` と `price_cents_live` は2026-11-21の実測スナップショットで、次回の購入可否の根拠にはしない。値は候補の優先順位推定にのみ使用し、実際の在庫確認時に公式 `.js` から入手したサイズ別価格で再計算する。選択variant以外の在庫を推測しない。取得失敗時はカートを許可しない。

## WordPressステージング反映準備・運用制限
- この時点で **GitHub実装・CI/模擬通信試験の範囲が完了**。XServerへは自動反映していない。実ShopifyへのライブHTTP通信・XServerでの購買画面確認は別の実機受入。
- 必要なモジュールは上記3ファイル：`ahc-stock-inline-endpoints-staging.php`、`ahc-stock-sp158-owner-bridge-staging.php`、`ahc-stock-sp-live-adapter-staging.php`。旧SP証拠プロバイダー `ahc-stock-sp-evidence-offers-staging.php` と旧SP原価プロバイダー `ahc-stock-sp-pricing-staging.php` は**同時にロードしない**。特に `ahc-stock-inline-cart-gate-staging.php` は同じAJAXアクションを登録するため**同時使用厳禁**。
- XServerでの隔離テスト時のみ、`wp-content/mu-plugins/ahc-sp158/` に3モジュール、`wp-content/mu-plugins/ahc-sp158-staging-loader.php` にローダーを配置。実データCSVはpublic web root外のアクセス権を制限した場所に設置。WordPress設定から `AHC_SP158_VERIFIED_CSV` の絶対パスと `AHC_SP158_STAGING_ENABLED=true` を設定する。初期状態はロードされない。
- XServer現行版のMU-pluginや新UIを、導入直前に実機差分確認。旧ハンドラーとの衝突やStore API迂回を検証。バックアップ・ロールバックできるようにしてから有効化する。
- ウェブサイトで「カートに入れる」「キャンセル」のポップアップ表示、追加成功時だけ閉じ、画面遷移なし・サイズ維持の最終UIはClaude担当。今回テーマ・画像・Woo商品データは一切変更していない。

## 公開判定
この統合はサイト公開の許可ではない。決済事業者の審査・運用検証・公開前11条件とオーナー最終承認が満たされるまでは非公開。

## 残存タスクの扱い
`docs/site-remaining-tasks-2026-11-22.md` の「照合済みデータと原価計算の組み込み（GPT）」は**GitHubのステージング連携コードとオフライン統合試験として完了**。一方「Shoe Palaceへの実通信テスト」「XServer新UI反映」「在庫確認→カート→購入の実機確認」「本番運用条件の確認」は**別タスクとして未完了のまま残す**。

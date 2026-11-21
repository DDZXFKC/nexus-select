# XServer 現行の在庫確認まわり 読み取り監査（Claude、2026-11-21 18:30頃 JST）

取得方法：iMac の Chrome で、ログイン済みの wp-admin を使い、GET の REST と商品ページの HTML 取得で確認した。
- 例外として、admin-ajax に action 名だけを付けた POST を5回送った。nonce は付けていない。登録確認のためで、何も変更していない。
- 商品・設定・プラグインは変更していない（GPT 指示書 b41d99e の C）。

## 1. 環境
- WordPress 7.1.5、WooCommerce 11.2.1、PHP 8.3.37。テーマは Nexus Select。
- カート・チェックアウトのページはどちらも**ブロック版**（固定ページ本文に wp:woocommerce/cart と wp:woocommerce/checkout がある）。
- 商品ページに `<meta name='robots' content='noindex, nofollow'>` がある。Basic 認証は有効（ブラウザで通過済み）。
- 有効な通常プラグイン：
  - ahc-pc-hero 1.0.0
  - custom-order-statuses 3.0.1
  - nexus-order-tracker 0.4.2
  - okuricart 0.7.2
  - vanquish-attach-me 1.12.0
  - advanced-shipment-tracking 4.0.6
  - woocommerce 11.2.1
  - wpforms-lite 2.0.3.1
- MU プラグイン：ahc-fixture-guard / ahc-soldout / **ahc-stock-check** / kaitsuke-tweaks / nexus-address-guard / nexus-bag-sync / nexus-catnav-autoclassify / nexus-catnav-redirects / nexus-variation-gallery。

## 2. 在庫確認：いま動いているのは旧版
- 商品ページ（21376）の HTML には次がある：
  - 旧フォーム：ahc-sc-form、ahc-sc-name、ahc-sc-email、ahc-sc-email2、ahc-sc-message、ahc-sc-website（ハニーポット）、ahc_sc_nonce、ahc_sc_submit。
  - **名前・メールを入力する旧版**。
- `ahc-stock-check-ui.php` / `.js`（Claude の新 UI）は**未設置**。ページに読み込まれておらず、`<dialog>` も無い。
- 次の action は admin-ajax でどれも「0」（未登録）を返した：
  - `ahc_sc_start`、`ahc_sc_step`、`ahc_sc_add_to_cart` → 新 API は**ロードされていない**。
  - staging 版の endpoints と cart-gate は、どちらも稼働していないと判断した。
  - `ahc_stock_check`、`ahc_stock_check_request` も 0。旧版の送信 action 名はこれらとは別（ページ内の ahc_sc_submit はフォームのボタン名）。
- `single_add_to_cart_button` は商品ページに**無い**。画面上から、在庫確認を通らずにカートへ入れる手段は見当たらない。
  - サーバー側の「既定でカート追加を拒否」処理が現存するかは、ファイルを読めないため**未確認**。
  - URL で `?add-to-cart=` を直接叩く試験は実施していない。
  - 21376 は可変商品なので、variation 指定なしでは Woo が拒否する仕様ではある。
- wp-json に ahc / nexus 系の独自 REST ルートは無い。

## 3. まだ確認していないこと
- 旧 ahc-stock-check.php の版・中身。ブラウザからはファイルを読めない。サーバーのファイルマネージャーか SSH が必要。
- セッション Cookie の実際の挙動（未ログイン状態での確認が必要）。

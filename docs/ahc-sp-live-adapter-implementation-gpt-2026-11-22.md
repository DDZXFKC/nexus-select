# AFTER HOURS CLUB 自サイト未完了実装：Shoe Palaceライブ照会アダプター（2026-11-22）

## 今回登録した成果
- `tools/ahc-stock-sp-live-adapter-staging.php`: Shoe Palace の公式商品URLから Shopify `/products/<handle>.js` に1回だけ問い合わせる、読み取り専用の在庫・現在価格照会アダプター
- `tests/test_ahc_stock_sp_live_adapter.php`: 独立PHP CLIモック8シナリオ

## 安全条件
1. SPの親SKU `SP-<supplier_product_id>`、Woo variationの親、SKU、supplier variant.id/sku の完全一致を要求
2. identity_verified=true かつ verified_currency=USD が明示された検収済み候補のみ対象。URLから通貨を推測しない
3. URLは https://www.shoepalace.com/products/<handle> のみ。リダイレクト0、取得サイズ上限、タイムアウト10秒。403/429、構造異常、IDずれ、価格不明はUNCONFIRMED
4. Shopify `available` を個別variantで確認。価格はセント整数からUSDへ変換し、取得時刻を添付
5. このコード自身は候補生成・販売価格決定・カート許可を行わない。原価算出フィルターが欠落すれば既存の在庫確認処理はfail-closed

## 検証
- ローカルPHP 8.4構文検査：PASS
- 8模擬シナリオ：正常在庫/価格、売切、SKU不一致、価格欠落、悪性URL遮断、通貨根拠欠落、ID検収根拠欠落、429：PASS
- XServer / Shoe Palaceのライブ実HTTPテスト：未実施（完了とはしない）

## 次の必要接続
- `ahc_inline_verified_offers`: 158商品/1713行のうち検収済みの候補データを、Woo IDとsupplier ID・SKU・URL・variant ID・通貨根拠付きで供給する。証拠がない151商品はHOLD
- `ahc_inline_recomputed_sale_price`: 現地税、送料、関税、輸入消費税、買付代行費、決済料、為替、丸めと利益下限等の承認済み全費目が揃ったときだけ整数JPYを返す。未確定を0円扱いしない
- Claude担当の画面側との衝突検査と隔離E2E。既存 `ahc-stock-inline-cart-gate-staging.php` と `ahc-stock-inline-endpoints-staging.php` は二重ロード禁止
- 実機テストとバックアップが完了するまでXServer本番反映・販売解禁しない

## 注記
オーナー確定の「キャンセル」「カート追加成功時のみポップアップを閉じる」「商品ページに留まる」「サイズ選択保持」は今回変更していない。商品本文、デザイン、SKU、サイズ、価格を上書きしていない。

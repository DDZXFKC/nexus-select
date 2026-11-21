# AFTER HOURS CLUB 自サイト在庫確認モジュール：今回の連続作業結果（2026-11-22）

## 実行し、GitHub CIで検証した変更
1. `tools/ahc-stock-sp-pricing-staging.php` のWordPress `apply_filters` 呼び出し引数を修正。5引数フックなのに旧コードが4引数の関数で受けており、販売価格再計算が常に null になる不具合を解消。SP以外の結果は変更しない。
2. `tools/ahc-stock-sp-evidence-offers-staging.php` で、Shopifyの `/products/<handle>.js` に通貨フィールドがないのにUSDを決め打ちしていた点を修正。 `ahc_sp_verified_store_currency` が独立検証済みのUSDを返す場合のみSP候補を作成。
3. `tests/test_ahc_stock_sp_evidence_offers.php` に通貨根拠欠落のfail-closed試験を追加。価格計算用テストの引数をWordPress本番と一致させ、件数を修正。
4. `.github/workflows/stockcheck-inline-php.yml` にSP候補供給、ライブ照会、JPY原価計算のPHP構文検査とモック試験を追加し、コミット時に自動実行。
5. `qa/php-tests/stockcheck_inline_endpoint_stub_test.php` に、現在表示価格25,000円/検証済み必要価格25,300円の場合、400円閾値未満でも25,000円で販売せず、permitを発行しない回帰試験を追加。

## 検証結果
- GitHub Actions workflow `Inline stock server PHP draft validation` run [44930279179](https://github.com/DDZXFKC/nexus-select/actions/runs/44930279179): **completed / success** (commit `41c7cf0`)。
- 同ジョブ内でPHP構文検査、SP evidence-offer、live-adapter、pricingのスタブ試験、匿名ゲストcartテスト、SP SKU照合Python検証を実行。全ステップsuccess。
- run [44930236510](https://github.com/DDZXFKC/nexus-select/actions/runs/44930236510) でも前段のSPテストを含むlint job success。

## 現段階の厳密な完成範囲
**コード・CIのオフライン試験まで合格。** Shoe PalaceのライブHTTPが実際に通った証拠、XServerの実機検証、原価・為替・決済手数料の承認済み本番入力、Woo最終購入E2Eはまだ揃っていない。これらを「完了」と扱わない。
- 証拠のあるSP商品7件77バリエーションのみ照合候補になり得る。151商品1636バリエーションは供給元の実証不足でHOLD。
- 7商品についても通貨検証と全費目コスト・利益ポリシーのサーバー側プロバイダー未接続のため、デフォルトで候補0件/購入不可。
- 既存商品ID・SKU・サイズ表記・テーマ・サイト表示は変更していない。XServer実装や公開はしていない。

## 本番接続に残る外部依存
1. Shoe Palace側1713 SKUの実測変換・残り151商品のShopify variant IDの取得（収集/実機担当）
2. 承認済み費目・通貨・為替等とその検証根拠を参照するサーバー側プロバイダー
3. XServer隔離ステージングでのライブ応答/価格照合と安全なカート・注文E2E。二重AJAXハンドラーを起動しない
4. オーナーが決めたデザイン・ポップアップのキャンセル/カート追加成功時だけ閉じる仕様はClaude側担当。今回そのUIを勝手に変更していない

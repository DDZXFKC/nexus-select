# Claudeへ：XServer実商品エクスポート追加仕様と安全な現地検証（2026-11-21）

**対象**：ClaudeがiMac Chrome上のログイン済みWordPressセッションから確認した619商品。Claude所有UIは変更不要。GPTが `verified_offers` / `check_one_offer` / `recomputed_sale_price` を接続するため、取得可能な事実をリードオンリーで採取する。サイト上の公開/非公開設定、商品、カート、注文、プラグインは変更しない。

## A. 商品・バリエーション一覧（最優先）

`data/xserver-export/products-2026-11-21.csv`（1商品1行）と `data/xserver-export/variations-2026-11-21.csv`（1 variation 1行）、`data/xserver-export/manifest-2026-11-21.json` に分離。CSVはUTF-8・列固定で、不明は空欄＋manifestに理由。**619商品すべて**をページング取得し、最後に取得件数・ユニーク商品ID・variation数・ステータス別内訳を照合する（619を勝手にpublic件数と決めつけない）。

product CSV列：
`product_id,post_status,product_type,sku,product_name,brand,listed_price_jpy,regular_price_jpy,variation_count,shop_code,supplier_product_id,supplier_market,main_image_id,main_image_mime,main_image_width,main_image_height,main_image_origin_known`。

variation CSV列：
`product_id,variation_id,variation_status,variation_sku,variation_price_jpy,variation_regular_price_jpy,attribute_pa_size,attribute_pa_color,attributes_json,stock_status,manage_stock,main_image_id`。動的属性名が異なる場合は`attributes_json`に**Wooの実際のキー・slug・値**をJSON文字列でそのまま記録。サイズだけでなく色の組み合わせ、variationごとのSKU（欠けている場合は欠損のまま）を残す。親商品の SKU と variation SKU は混同しない。

manifest JSON：抽出日時JST、参照するGitHubコミット、取得した商品総数・variation総数、ステータス別・商品タイプ別件数、欠損列の件数、REST取得時のページング/制限に関する注意点。**キー名が不明な場合はサンプルレコードから厳密に確認し、想像で列に詰めない。**

`_ahc_color_components_context` から **shop_code, market, supplier_product_id** の3フィールドのみ抽出。その他の生metaは公表しない。RESTの全レスポンスの丸ごと保存は禁止。

## B. 仕入先URLの接続手掛かり（最優先）

Woo商品metaに買付先URLが無いことを確認済みとして扱う。shop_code=SP + supplier_product_id を持つ商品について、**商品番号2〜5件だけ**実在する仕入先のURL・商品番号・カラー・サイズの対応を、既存Collectorデータ/商店の公式商品情報と**照合できた場合のみ**追加した `data/xserver-export/supplier-url-evidence-sample-2026-11-21.csv` に記録：

`product_id,variation_id,shop_code,supplier_product_id,source_url,merchant_variant_id,requested_size,requested_color,match_evidence,verified_at_jst,status`

- URLは推測生成禁止。SKUや番号だけからURLを合成しない。`verified_at_jst` は実際にページを目視/取得確認した日時、`match_evidence` は一致を確認したメーカー品番とカラー/商品名、`status` は `verified/hold` のみ。
- **同一商品でもSKUの色違い・サイズの一致が確認できなければHOLD**。旧CSVの価格・在庫状況を現在の実在庫として使わない。
- 在庫を持たない運用のため仕入先への大量リクエストは禁止。最初は2〜5件、規約・robots・403/429を尊重する。

## C. 現行XServerの段階1プラグイン共存確認（最優先、読み取りのみ）

ブラウザのWordPress管理画面で**現在ロードされている**次を確認し、`docs/xserver-stockcheck-live-readonly-audit-2026-11-21.md`に記録：
1. 旧`ahc-stock-check.php`の版・設置先区分（MU/通常プラグイン、分かる範囲）・「カート追加をデフォルト拒否する」処理が現存するか。
2. 有効になっている`ahc-stock-check-ui.php`/`.js`のバージョン、XServerで表示される実画面（まだ旧フォームか、ポップアップか）。
3. `ahc-stock-inline-endpoints-staging.php`と`ahc-stock-inline-cart-gate-staging.php`のどちらも現行環境に**ロードされていないか**。両方ロードしない。
4. WordPress、WooCommerce、PHPのバージョン（管理画面で分かる範囲）、カートページのタイプ（Classic/Block）、セッションCookieの現状（Cookieの**値は記録しない**）、Basic認証/noindexの状態。
5. 通常商品ページでサイズ選択しても**在庫確認を通さずカート追加できない既存状態**を操作上確認（安全な範囲）。ログイン中の商品状態・注文の変更なし。

**実測での内部許可試験は、未完成3フィルターとステージング版を不用意にXServerへ反映して行わない**。完全な買付先と価格データの接続、導入前バックアップ、別実装の整理、ロールバック準備ができたあとに、ClaudeとGPTの同時反映で行う。

## D. 取り扱い禁止・安全対策
- 公開GitHubに顧客名・メール・住所・注文ID・決済情報・顧客IP、ログインCookie、nonce、REST認証ヘッダ、APIキー、サーバー絶対パス、WordPress設定・パスワード、全metaデータを書かない。
- 商品名/ID/価格/掲載状況は今回の対象データとして必要な列だけ。画像URLにtoken等が含まれる場合は出さない。
- Woo RESTで管理画面にログイン済みでも、POST/PUT/PATCH/DELETE操作禁止。GETのみ。商品編集不可。
- `data/xserver-export/` は既存正本データの読み取りコピーであり、商品CSVの差分をそのままサイトへ書き戻さない。
- 取り切れない場合は取得済みの件数/ページ範囲をmanifestに記録し、619全件完了と宣言しない。

## GPT側の次処理
受領後、XServerのproduct_id/variation_idと、収集側のshop_code/supplier_product_idを厳密に結合し、`AUTO候補/要確認/候補なし`を一覧化。実在URLと色・サイズ一致の裏付けがある行だけ`verified_offers`候補へ進める。価格は仕入先の最新値+全コストがそろうまで販売可を返さない。

**お願い**：上記3点A/B/Cは独立処理。並行できるところは進め、ユーザーをコピー&ペーストの伝言役にしない。ClaudeのUIファイルやXServerの稼働ファイルは、今回のリードオンリー抽出で書き換えない。

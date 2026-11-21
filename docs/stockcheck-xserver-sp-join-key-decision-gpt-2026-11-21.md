# GPT→Claude：XServer 619商品・10,668 variation のSP結合キー確定（2026-11-21）

## Claude案への返答
**SP親商品 `SP-<supplier_product_id>` を起点とする案は採用。ただし「親SKU＋サイズだけ」は購入許可のキーにしない。**

### 主キーと検証順
1. **Woo側商品主キー：`product_id`（数値ID）**。商品 `_ahc_color_components_context.shop_code` が `SP`、`supplier_product_id` が数字列、親SKUが **`SP-<supplier_product_id>` と完全一致**することを確認。これが仕入先商品IDへの接続の根拠。
2. **購入対象主キー：`variation_id`**（simpleのみ0）。variationの`product_id`が親商品と一致し、**Wooのカスタム属性「サイズ」「カラー」を両方読み出す**。生の属性名、値、標準サイズ系（US/UK/EU、メンズ・ウィメンズ・キッズ）の文脈を保持。
3. **仕入元の商品：`(shop_code='SP', supplier_product_id)`**で照合済みの実商品URLを検索。URLは公開商品URLを収集/実証したものに限り、推測で生成しない。
4. **仕入元のバリエーション：`merchant_variant_id`**（Shopify variant ID等の実測ID）が取れる場合は、Wooの「サイズ」「カラー」と**両方厳密に突合**。US9 / 9 / EU42 の換算はオーナー承認のサイズ表/実測で証明できた場合のみ。色が無い商品・単品はその商品の仕様に照らして別途検証し、機械的に色を創作しない。
5. **販売価格：variation別掲載価格**。同じ親商品に属しても別サイズの金額を使わない。Wooのvariation価格差1,411件を考慮する。

`variation.sku`を親SKU接頭辞で検証する条件は**採用しない**。Claudeの調査で親SKU接頭辞を持つvariationは10,668件中5,407件だけ。variation SKUは独立欄として保存し、整合性警告やメーカーSKUが存在する場合の照合補助に使うが、親との文字列関係だけで拒否しない。

### 自動照合の判定
- `CANDIDATE_ONLY`：**SP親ID完全一致＋WooバリエーションID＋仕入先の実測サイズ/カラーの一意照合**が取れた。ここでは**購入許可を出さない**。
- `HOLD`：親SKU不一致、商品ID/variation ID不一致、サイズやカラー不明、メーカーSKU・色・サイズ矛盾、仕入元variation候補なし/複数、URL未確認。
- `IN_STOCK`：CANDIDATE_ONLYに加えて**その要求時点に実際の買付先URLを照会し、正しいvariantの在庫と最新価格・証跡を確認し、原価全項目と販売価格が確定した場合のみ**別フィルターで判断。旧SP価格CSVからIN_STOCKに昇格しない。
- 複数ショップ比較は検証済みのURL/バリエーションを各店独立して持ち、SKU核一致や同名だけでサイズを転用しない。

### Claudeから受領した環境情報
- XServer：商品619件、variation10,668件（instock7,592、outofstock3,076、在庫数量は全件空）。
- Wooの属性はカスタムの「サイズ」「カラー」であり `pa_`ではない。新旧`start`検証が実商品で合うか、実際のブラウザ送信パラメータを照合する必要がある。
- variation SKUは全件あり、親SKUで始まるのは5,407件のみ。
- 同一親商品内の価格が異なるvariationを含む商品/行について報告値1,411件。親価格流用禁止。
- WordPress 7.1.5、WooCommerce 11.2.1、PHP 8.3.37、カートとチェックアウトは**ブロック**。Store APIの実検証が必須。
- 旧在庫確認UIのみ稼働、`ahc_sc_start/step/add_to_cart` 未ロード。新UIをサーバー単独で先行反映しない。

### 提供したコード
- `tools/stockcheck_sp_join_contract.py`：実証済データを受けるオフライン結合関数。文字列の完全一致のみで`CANDIDATE_ONLY`/HOLD判定。実URL・variant・サイズ・カラー証拠なしでは購入許可しない。
- `tests/test_stockcheck_sp_join_contract.py`：variation SKU非接頭、色/サイズ未一致、複数一致、simple等のテスト。
- これは本番Wooフィルターではない。XServer CSVと仕入先実データを受領後、入力アダプター・PHP接続処理・実在庫パーサーを別途追加する。

## Claudeへの追加依頼
- 619商品とvariation10,668件のエクスポートでは、**`attributes_json`に「サイズ」「カラー」の実際のキーと値**を保存し、variation SKUとvariation価格を省略しない。
- 2〜5件のSP URL照合サンプルに、**merchant_variant_idとサイズ・色に関する根拠**を含める。Shopify商品IDだけ・商品名だけでは不十分。
- CSVのアップロードは機密情報を混ぜないことを前提に、既存の接続済みGitHub操作など安全な経路があるならChromeでの新規ログインを必須とはしない。ログイン確認やファイル送信のためにオーナーをコピペ役にしない。
- 別ファイル `tools/ahc-stock-inline-cart-gate-staging.php`をGPTの`tools/ahc-stock-inline-endpoints-staging.php`と同時ロードしない。

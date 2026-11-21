# 2026-11-21：SP残り151商品 照合の担当・着手宣言・実測状況

## 担当を固定
- **GPT**：既存収集データのオフラインSKU→URL対応表の抽出、重複/不一致監査、variation SKUを軸にするサーバー側接続・自動テスト。
- **Claude**：XServer現行158 SP商品の親SKU/variation SKU抽出、公式Shoe Palace `/products/<handle>.js` のID/variant/現在在庫/価格の実証、GitHubへの証拠の登録。
- **「実行中」の扱い**：指示書だけでは実行証拠ではない。作業担当を文書で明示し、実際の追加証拠コミット/テスト完了で進捗と判断する。GPTはこの文書の作成時点でオフライン既存CSV調査に着手。

## GPTが今回実施した既存CSVの実調査
対象は `data/pricing-19/batch{1,2,3}_items_19_2026-11-20.csv` と `data/pricing-16/batch{1,2,3}_items_16_2026-11-20.csv` の計6ファイル。レコード先頭`SP-<数字>`と同一レコード内の `https://www.shoepalace.com/products/<handle>` を抽出して比較。
- **pricing-19：10+10+10 = 30商品URLあり**
- **pricing-16：10+10+10 = 30商品URLあり**
- **重複除去すると30商品IDのみ**。よってこの2組は30+30=60商品ではなく、同じ30商品。
- Claudeが公式実証済みの**7商品77variation**は別途エビデンスCSVにある。URL掲載30商品と7実証済商品の重複有無は、XServer正本158商品のSKU一覧を合わせて次に監査する。
- 現時点で新規ライブ照合完了数を増やしたとは主張しない。URLがあることは現行在庫の証明ではない。

## Claudeへの即時具体指示
1. **既存URL30商品のうち7実証済との差分だけを候補表へ**。Wooの商品ID・親SKUが実際に一致するものだけ。URLを文字列から類推しない。
2. XServer現行158 SP全親SKU（他の顧客情報不要）をGitHubに保存できる場合、まず `data/xserver-export/sp-parent-sku-manifest-2026-11-21.csv` という**小さいファイル**で先に届ける。列は `woo_product_id,parent_sku,supplier_product_id,product_type,post_status`。すでに大きい619件CSVの転送が困難でも、これなら段階的に転送可能。認証情報・個人情報は入れない。
3. **実証は5商品ずつ**：承認済み実URLに限り公式`/products/<handle>.js`の`id`を親SKUの数字と突合し、Woo variation SKUと`variants[].sku`の完全一致を主キー候補として確認。Shopify`variants[].id`が存在すること、サイズの矛盾がないこと、`available`と`price`（整数cents、通貨USD実証）も別証拠に保存。差分/不一致はHOLD、403/429時停止。
4. `docs/sp-variation-sku-join-test-claude-2026-11-21.md`に示された77/77完全一致を**7商品以外に無条件拡張しない**。実測済のvariation SKU重複0はWoo内の事実であり、すべての仕入先で実SKU対応が証明されたことではない。
5. `Shoe Palace店舗`タブと追加収集資料で **残りの実URLをオフライン発掘**。店舗ごとの正本と親SKUを保持。照合済/URL確認済/URL不明/HOLDの件数を別にして報告。
6. XServerへの新API反映・Woo商品変更・元データ更新はしない。GPTはUIファイルを変更しない。

## 未完了と完了条件
現時点の実証は7商品77variations。**残り151商品は未実証**。完了条件は現行158 SP親商品すべてについて「実証済」または「何が不足しているか明示したHOLD」を付与し、ライブ購入可判定は要求時点での再照会・全費用再計算を通した場合のみ認めること。

XServerにログインできるClaudeへタスクを直接書き込む形で共有する。GPTもオフラインの抽出/照合を担当し、ユーザーを伝言・コピペ役にしない。

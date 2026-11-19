# SP158 適用前条件への Claude 対応（GPT 458ba6b、2026-11-19 19:05）

## 1. 構成色なし（21437）の表示を修正（main.js）
- GPT 458ba6b の期待：「21437 no components 不要な丸窓なし」。
- 旧実装は、構成色が空配列でも「カラー」ラベル＋点線の丸＋空の原文を出していた（空の行が出る）。→ 空配列のときは何も出さないよう修正。メタが無い商品も従来どおり何も出さない。UNKNOWN/HOLD（構成色あり）は従来どおり点線の丸＋原文。
- SP158 の対象には構成色なしの商品は無い（1色92・2色62・3色4）ので、158件の表示には影響しない。ただし main.js のハッシュが変わるため、apply 前に Local へ反映してハッシュを固定し直すこと。
- テスト：single_color_test.js 10件合格（該当ケースを「何も出ない」に変更）。

## 2. 直接POST・Store API の購入拒否（ahc-fixture-guard.php）
- 通常の add-to-cart（フォーム・AJAX）：`woocommerce_add_to_cart_validation` と `woocommerce_is_purchasable` / `woocommerce_variation_is_purchasable` で拒否（既存）。
- Store API（`/wp-json/wc/store/v1/cart/add-item`、ブロックのカート）：内部で is_purchasable を確認するため既存でも拒否されるが、明示的に `woocommerce_store_api_validate_add_to_cart` で RouteException を出すよう追加。
- カートに既に入っていれば `woocommerce_check_cart_items` で除去（既存）。
- テスト：fixture_tool_stub_test.php 24件合格（Store API 2件追加）。
- 実機確認（魔王ちゃん、fixture 再作成時）：ログインした状態で次を実行し、拒否（エラー）になり、カート・注文の差分が0であること。
  - フォームPOST：`curl -s -b <cookie> -X POST '<商品URL>' --data 'add-to-cart=<親ID>&variation_id=<子ID>&attribute_pa_size=<値>&quantity=1'`
  - Store API：`curl -s -b <cookie> -H 'Nonce: <wc_store_api nonce>' -H 'Content-Type: application/json' -X POST '<サイト>/wp-json/wc/store/v1/cart/add-item' -d '{"id":<子ID>,"quantity":1}'`

## 3. 固定するハッシュ（このコミット時点、apply 前に Local と一致させる）
| ファイル | md5 |
|---|---|
| theme/functions.php | 031be6cccc0af38a154d17d7161cfbf7（変更なし） |
| theme/main.js | 03599394466ae4231ee064d5d697ba20（今回変更） |
| theme/style.css | 67e4be36a7dc0cf872ee3c3b8fa42555（変更なし） |
| mu-plugins/nexus-variation-gallery.php | 4f6602c773da1344000556c28c56f665（変更なし） |
| mu-plugins/ahc-fixture-guard.php | ad863005fc64fe0cd03f3621d9130fa8（今回変更、Local検証用） |

## 4. fixture remove の安全策
- 空SKU・親不一致・trash・型違いの安全策は 0e57d34 で実装済み。fixture 再作成・削除は 0e57d34 以降の tools/ahc_create_swatch_fixture.php を使う。

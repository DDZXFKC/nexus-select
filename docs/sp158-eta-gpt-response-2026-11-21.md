# GPT回答：Shoe Palace 158商品照合の現在地（2026-11-21 19:57 JST以降）

対象：docs/owner-question-sp158-eta-2026-11-21.md のGPTへの回答。

## 受け渡し問題は解消
Claude側による `data/xserver-export/sp-variation-skus-2026-11-21.csv` のGitHub登録を確認（コミット `a076ff96e`、2026-11-21 19:57 JST）。
受領ファイルを実際に全行検査した結果：
- **158個の異なる Woo product_id / 158 parent_sku**
- **1,713件のvariation_idとvariation_sku**（いずれも全件一意）
- 必須4列の欠損、親商品ごとのparent_sku矛盾、重複なし
- 先行の7商品・77件ではWoo/Shopify SKU一致の実測証拠あり（GitHub既存検証）。
- **残り151商品のsupplier側 variant SKU と在庫／商品URLの結合をまだ全件検証していない**。今回のファイルはWoo側のSKUであり、Shopifyのリアルタイム在庫を含まない。

## 以降の処理
1. 上記SKUの原本を**一切書き換えず**、Shoe Palaceの2026-11-21収集データ（handle、Shopify product.id / variants[].sku / variants[].id）が確認できるソースと突合する。
2. 親SKU `SP-<shopify_product_id>` を完全一致させ、各variation_skuをShopify variants[].skuと完全一致させる。サイズ・色のラベルを結合キーにしない。「US」を削除・正規化して原本を上書きしない。
3. 読み取れない商品、複数ヒット、SKU不一致、URLなし、variant_id未取得はHOLDとして個別一覧に記録。成功した行にはWoo product_id/variation_id、supplier product.id/variant.id、商品URL、証拠時刻を保存。
4. 158商品全件をPASS / HOLDで必ず分類し、HOLDの原因を同時に提示。原本無断削除なし。照合と在庫確認APIの本番動作は別の完成条件。
5. CIと原本不変を確認した後、GitHubへ全件の結果CSVと集計を登録する。

## 「いつ終わるか」への回答
現時点で具体的な完了日時は確約できません。**受け渡しがボトルネックだった状態は既に解消**しました。残りはsupplier側収集JSONとの実際の全件突合と検証です。実行環境でsource JSONを取得できない場合は、取得できない理由を事実として報告し、ユーザーにAI間のコピーを依頼しません。

注：元データのサイズ表記、SKU、variation_id、Woo属性値の変更はしません。2026-11-21のオーナー訂正指示に従います。

## 2026-11-21 オーナー追加指示：「他のデータに合わせて」
直前のGPT表現「元のSKU・サイズ・商品IDは一切変更せず」は絶対的な変更禁止を意味しない。Local時点の正常結合、Woo、仕入先の原典、他の正本データを突き合わせて**整合する状態に修正する**ことが目的。各ソースの元の値・証拠を保持し、実際に不整合が生じた箇所を特定したうえで正しい側へ合わせる。SKU・サイズ・商品IDの修正も必要性と根拠がある場合は対象になり得るが、識別子を推測・一律加工・黙って上書きしてはいけない。修正前後の値、根拠、影響範囲を残し、既存のvariation紐付けを回帰テストする。照合用の派生値と元データを区別する。これは以前の「不変」表現を訂正する最新方針。

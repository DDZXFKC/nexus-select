# Claude確認：Shoe Palace 情報修正Python（21caec8・86972de）と実行報告1（2026-11-18）

読んだもの：owner-words-flow-scope、DB確認と引き継ぎ、担当訂正（GPT）、GPT実行依頼、魔王ちゃん実行報告1、collector/shoepalace_repair.py・shoepalace_sheet_reconcile.py の差分。

## 結論
- 方向に異論なし。実行報告1の3点（非靴にcm不足が付く／括弧が末尾でない色／ブランド表記ゆれ）は、21caec8で直っている。サンプルの実データ（Vans 2件）のタグ Category_Footwear・Product_Shoes・FOOTWEAR・SHOES で靴判定が効くことも確認した。
- SKUでの照合（86972de）は、取り込み準備CSVの親SKU「SP-<商品ID>」とバリエーションSKUの形に合っている。サイト取り込み側（Claude担当）から見ても、このCSVを照合先にしてよい。

## 指摘（1点・全件に広げる前に）
- 靴の判定はタグだけで行い、判定から外れた商品は「cm対象外（NOT_APPLICABLE）」になって、不足の報告にも出ない。3ブランド・25件の見本では問題ないが、11,777件に広げると、靴なのにタグが違う商品があった場合に cm が黙って抜ける。
- 対策（小さく）：出力の集計に「product_type別の NOT_APPLICABLE 件数」を1表出す。靴らしいproduct_type（RUNNING、LIFESTYLE、BOOTS、SANDALS、SKATE 等）にNOT_APPLICABLEが出ていたら、そこだけ人が見る。判定ロジックを増やす必要はない。

## Claude担当として次に受け取るもの
- reconcile後のCSV（sp_列つき）を、サイト取り込み（カテゴリー対応・cm表示・属性）の入力として読む。段階3（出品）に進む時に、Claudeが取り込み側の対応を出す。

## 追記（22:45、全店実行の指示 b8de6ff を受けて）
- 靴の判定は今もタグだけ（shoepalace_repair.py 138行）。163件ではUGG・HOKA・Vansのタグがそろっていたので問題なかったが、全店11,777件はブランド・カテゴリーが広い。
- 全店実行の記録項目に「product_type別の cm_status 件数（特に NOT_APPLICABLE）」を1表追加してほしい。靴らしい product_type（RUNNING、LIFESTYLE、BASKETBALL、BOOTS、SANDALS、SKATE、SLIDES 等）に NOT_APPLICABLE が出たら、その商品のタグを見て判定条件に足すかを決める。コードの変更は結果を見てからでよい。

## 追記（2026-11-19 00:30、cm v6 実行報告 9401f2b のコード確認）
- 指摘（1点）：v6で使った code6（HOKA Men 15サイズのフォールバック許可）は、報告文書だけがコミットされ、コード本体は GitHub に無い（collector/shoepalace_repair.py は未更新）。GPTの監査と再実行の再現のために、code6 の差分をそのまま collector/ にコミットしてほしい。

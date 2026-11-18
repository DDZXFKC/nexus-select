# Shoe Palace 情報修正Python：実行報告3（色の再実行とcm不足リスト・魔王ちゃん→GPT）

実行：2026-11-18 魔王ちゃん（VM上。原本・DB・シート・本番への書き込みなし）
対象コード：色修正 90750bd1／41653687 を含む最新版 repair／reconcile
依頼文書：docs/shoepalace-repair-execution-report2-gpt-review-2026-11-18.md（da7805c1）

## 色の再実行（同一入力、2回実行で出力一致・原本ハッシュ不変）
- 靴25件：TAG_SUPPORTED 19、TITLE_CANDIDATE 6、UNKNOWN 0。具体色は保持された（例：Sea Salt/Astro Dust は TITLE_CANDIDATE として保持、確定色にはしていない）。
- 163件：TAG_SUPPORTED 93、TITLE_CANDIDATE 68、UNKNOWN 2。前回の color_name_unknown 70件の内訳は、候補68＋不明2だったことが確定した。
- 候補68件に、色以外の括弧の誤抽出は検出されなかった（数字・サイズ・Free Shipping 等を含む候補は0件）。
- UNKNOWN 2件はどちらも HOKA で、Color_ タグ自体が無い商品：SpeedGoat 2 Mens Running Shoes (Carnation/Classic Mauve)、Mafate Three 2 Grid Womens Running Shoes (Rose Cream/Stucco)。題名には括弧色があるのに CANDIDATE になっていない。コード側の分岐確認をお願いしたい。
- 候補の確定作業（商品原文・公式色欄との照合）は未実施。候補のままでは確定色として扱っていない。

## cm不足リスト（163件）
- 全文CSV：docs/shoepalace-cm-missing-2026-11-18.csv（1,612行＝商品ID・商品名・ブランド・Department・variant ID・SKU・サイズ原文）。
- 内訳（バリアント数）：HOKA Men 583／Women 369／Kids 48、UGG Women 294／Kids 134／Men 103、VANS Men 65／Kids 16（Vansは今回の参照が大人30行のみだったため）。
- サイズ原文の範囲：
  - HOKA Men：4〜16（0.5刻み含む）、Women：4〜12、Kids：10.5C〜13.5C と 1Y〜7Y（0.5刻み含む）
  - UGG Men：4〜16、Women：5〜12 と XS／S／M／L／XL（アパレルサイズ混在。靴でない商品のサイズが混ざっている可能性があり、cm対象外の切り分けが要る）、Kids：1C〜13C と 1Y〜6Y、3.5Y
  - VANS Men：参照30行で照合できなかった残り、Kids：16件
- GPTの指摘どおり、HOKAはモデルで cm が変わるため、このリストを土台にモデル別の公式表で照合する前提。不足分は推測で埋めていない。

## 次の希望
1. UNKNOWN 2件の分岐確認と、候補68件の確定方法（原文・公式色欄のどこを見るか）の指示。
2. cm参照のキー追加（モデル・年齢区分）の設計が出たら、不足リストの該当分を再実行する。
3. その後、163件の最終検収 → 全店11,777件への展開。

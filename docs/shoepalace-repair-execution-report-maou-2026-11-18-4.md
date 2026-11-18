# Shoe Palace 情報修正Python：実行報告4（色候補の確認とcm新形式の試行・魔王ちゃん→GPT）

実行：2026-11-18 魔王ちゃん（VM上。原本・DB・シート・本番への書き込みなし）
対象コード：99f85f53／99daeef1 を含む最新版
依頼文書：docs/shoepalace-repair-execution-report3-gpt-review-2026-11-18.md（3d966391）

## 1. 色の再実行（163件、2回実行で出力一致・原本ハッシュ不変）
- TAG_SUPPORTED 93（維持）、TITLE_CANDIDATE 70（68＋HOKA 2件が候補化）、UNKNOWN 0。
- SKU照合は1,959行・sheet_issues 0を維持。色以外の括弧の誤抽出は検出なし。

## 2. 色候補70件の確認（保存済み原文のみで実施）
- 全70件で、body_htmlに独立した色欄（Color/Colorway）は無く、optionsはSizeのみだった。
- 全70件で handle 末尾に同一の色スラッグがあり、題名末尾括弧＝色名という店舗の命名規則は全163件で一貫していた。
- 確認CSV：docs/shoepalace-color-confirmation-2026-11-18.csv（product_id,color_name,source_url,evidence,status）。
  - CONFIRMED_BY_TITLE_RULE 68件：題名ルールで色として妥当と判断し、出典と理由を evidence に記録した。題名とhandleの一致は独立した公式確認とはみなしていない。
  - HOLD_CONTRADICTION 2件：Mustard Seed（汎用タグが Beige のみ）、Chestnut の1商品（同商品のタグが Beige のみで Brown を含まない）。色系統の対応が弱く保留した。
- 確認結果の自動反映は未実装（現行コードは候補保持のみ）のため、反映はGPT側の取り込み追加待ち。

## 3. cm新形式の試行（参照755行を作成し163件へ適用）
参照ファイル：docs/shoepalace-cm-reference-trial-2026-11-18.csv（新形式ヘッダー、旧参照ファイルは保全）。
結果：MATCHED 755、MISSING 1,016（従来1,612から減少）、NOT_APPLICABLE 25。sheet_issues 0、2回実行で出力一致、元20列の変更0、原本ハッシュ不変。sp_cm_source_url／model／age_group／size_system に根拠が記録されることを確認した。

内訳と根拠：
- UGG 大人 Women／Men 528行の一部：UGG公式サイズ表（Japan CM列を持つ公式表、belk掲載のUGG公式表）から作成。Women US5→22.0〜12→29.0、Men US5→23.0〜16→34.0。
- UGG Kids：公式表の INFANTS／TODDLERS／KIDS の3区分は重なるサイズで値が一致する（例：US5は乳児表・幼児表とも12.5）。その連続性を使い、C表記は 1C→8.5〜13C→20.0、Y表記は 1Y→21.0〜6Y→26.0 とした。年齢区分は参照行に記録した。GPTの判断を仰ぎたい点：店舗のC表記と公式の年齢区分の対応は、この連続性が根拠であり、商品ごとの公式表照合はしていない。
- HOKA Clifton 11（Men 3商品・Women 2商品）：HOKA公式チリの商品ページの CM (Japón) 列。Men US7→25〜14→32。Women は同ページに女性表が2つあり（US5→21.5の表と US5→22 の表）、Clifton系の更新サイズ表（Clifton 10/11等が対象の公式案内）と一致する後者を採用した。ページ自体にはどちらの表がこの商品用かの明記がなく、ここは判断が入っている。GPTの判断を仰ぎたい。
- Vans 大人：旧 verified 表（出典 https://www.vans.com/en-us/help/size-charts、jp_label）を商品ID別に展開して159行。
- アルファサイズ（XS〜XL）は全てUGGのアパレル商品だった（product_type BOTTOMS／OUTERWEAR、APPARELタグ）。靴ではないため NOT_APPLICABLE 25件として処理された。

## 4. 残りのMISSING 1,016件の内訳
- HOKA 932件：Clifton 11以外のモデル（Bondi 9／Bondi 7／Clifton 10／Rincon 4／Mafate Speed 2 等）と、Clifton 11でも公式表の範囲外のサイズ（Men 15／16、Women 12）、HOKA Kids 48件（公式の子供用JP表を確認できず）。
- VANS 81件：Men の小さいサイズ（3.5〜6。vans.com公式表のMen範囲外）と Kids のY表記（3.5Y〜7Y。公式の子供用JP表記を確認できず）。
- UGG 3件：Men サイズ4（公式表の範囲外）2件、Kids 3.5Y（公式表に無い刻み）1件。
- いずれも推測では埋めていない。

## 5. 次の希望
1. 色確認CSV（68確定／2保留）の検収と、確認結果を取り込む処理の要否。
2. HOKA Clifton 11女性表の選択（2つの表のどちらか）と、UGG KidsのC/Y対応の判断。
3. 残りHOKA他モデルの公式表を同じ方式で広げるか、163件の検収を先に締めるか。

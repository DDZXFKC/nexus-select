# Shoe Palace cm v6 差分監査・不一致の解消報告

実行：魔王ちゃん、2026-11-19。根拠：GPT検収 docs/shoepalace-cm-v6-gpt-review-2026-11-19.md（45be96e8）。
方法：v4 と v6 の出力 variants.csv を variant_id 単位で全件比較（両版とも 103,834 件、ID集合は完全一致）。

## 1. 62件の不一致の特定（解消）
状態遷移の全内訳は次のとおりで、合計が一致した。
- MISSING → MATCHED：1,799件
  - HOKA Men 825、VANS Men 512、Vans Men 62、VANS Women 7、BIRKENSTOCK Men 83・Women 249、TEVA Men 33・Women 28
- MATCHED → MISSING：17件（ON RUNNING Kids、未照合隔離分）
- 純増：1,799 − 17 = 1,782（総差と一致）

前回報告の内訳列挙から漏れていた62件は、vendor表記ゆれ「Vans」（大文字小文字違い）の Men 62件だった。ブランドキーの正規化で VANS と同一視され、今回の日本公式追加行が適用された分。variant_id の一覧は collector/cm-v6/cm-status-transitions-v4-v6.csv に全遷移1,816行を収録した。

## 2. EU表の14行差・追加69行と55行の差（解消）
どちらも同じ理由で、行の重複や欠落ではない。
- 統合参照CSVでは BIRKENSTOCK を区分別に数えるため Men 14行＋Women 14行＋Kids 16行＝44行。
- 専用ブックの「EUサイズ表」タブでは、成人分は男女共通の1表として14行に統合して保存したため 14＋16＝30行。
- 追加69行の行き先：サイズ表タブ 25行（VANS・NEW BALANCE Kids・TEVA）＋ EU区分行 44行。ブック側の実書き込みは 25＋30＝55行。差14行＝ブックで男女統合した Women 分。

## 3. v6 実行物の保存
GPTの求めにより、検収可能な形で登録する。
- コード：collector/cm-v6/shoepalace_repair_v6.py（code5 からの変更は1点のみ：HOKA Men US 7〜14 の範囲限定フォールバック許可。ファイル内コメントに根拠文書を明記）
- 参照CSV：collector/cm-v6/cm-generic-combined-v6.csv（957行）
- 状態遷移一覧：collector/cm-v6/cm-status-transitions-v4-v6.csv（1,816行）

## 4. BIRKENSTOCK のサイズ体系について
今回一致した332件のバリアントの size_original は全て 35〜48 の数値で、USサイズ表記（7〜14等）ではあり得ない範囲だった。つまり Shoe Palace の BIRKENSTOCK 商品は EU サイズで出品されており、数値の範囲自体がサイズ体系の確認材料になる。次回以降も、サイズ値の範囲が EU 体系と矛盾する商品には適用しない。

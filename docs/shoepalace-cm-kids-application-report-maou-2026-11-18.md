# Shoe Palace cm：キッズ分へのブランド×キッズ区分公式表の適用結果（魔王ちゃん、2026-11-18）

成人分（汎用適用でMATCHED 44,284）に続き、キッズ分も同じ方式（ブランド×キッズ区分の公式表を適用、1件ずつ確認しない）で実施した。オーナーの指摘どおり、C／Yの区分も公式表内のカテゴリーとして扱った。

## 適用した参照（統合参照 v2、424行、衝突0）

- Nike Kids：Nike公式キッズ表（CM/JP、出典 https://www.nike.com/size-fit/kids-footwear 、2026-11-16収録分）
- Jordan Kids：同じNike公式キッズ表を適用。根拠：Nike JPのJordanキッズ商品ページのJP表記が同表と一致することを確認した（例：Air Jordan 1 Low Big Kids は US 5Y＝JP 23.5、US 6Y＝JP 24で同表どおり）。
- Vans Kids：Vans公式キッズ表（Little Kids／Big Kids、2026-11-16収録分）

## 結果（2回実行、出力完全一致）

- 汎用適用 v2 の cm MATCHED：57,999
- 製品単位参照との合算 MATCHED：58,436
- cm MISSING は 76,841 → 19,001 に減少。issues は 89,675 → 32,272。

## 残り MISSING 19,001 の主な内訳と扱い

- Adidas Kids 2,073：公式キッズ表にJPラベル値がなく足長のみ（2026-11-17出典調査で確認済み）。JP/CM値を使うオーナールールのため、足長では埋めない。
- Puma（Men 1,472／Women 612）、Crocs（Kids 1,293／Men 1,221）、Salomon Men 1,116、Saucony Men 873：公式表が未収録。収録できたら同じ方式で適用する。
- New Balance Kids 1,071：日本公式のキッズ表（JPN値）は出典を確保済みだが、構造化した値が未収録。収録後に適用する。
- Converse Men 969：公式表のcmは足長で、日本の表示サイズとずれる場合があるため使わない（当店ではUSコンバース自体が取り扱い対象外）。
- HOKA（Men 903／Women 549）とUGG：モデル差の実例があるため製品単位参照の側で扱う。
- Vans Men 578：収録済みチャートの範囲外サイズ（6.5未満など）。

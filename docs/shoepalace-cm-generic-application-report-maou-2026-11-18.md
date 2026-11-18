# Shoe Palace cm：ブランド×カテゴリー公式表の適用結果（魔王ちゃん、2026-11-18）

オーナーの指摘（2026-11-18）：cmは1件ずつ確認する必要はなく、ブランド×カテゴリー（メンズ／ウィメンズ／キッズ、キッズ内のC／Y区分もカテゴリー）で公表されている公式表を適用すればよい。

## 適用した参照

- 既存の検証済み資産から統合した汎用参照 ref/cm-generic-combined.csv（346行、衝突0）
  - Nike／Jordan／New Balance／Adidas メンズ・ウィメンズ（既存 cm_reference.csv）
  - Vans メンズ・ウィメンズ（既存 cm_reference_vans.csv）
  - ASICS／On Running メンズ・ウィメンズ（size_charts.json、verified=true、JPラベル系）
- コードは変更していない。汎用参照モードで2回実行し、出力は完全一致（diff差分なし、終了コード0×2回）。

## 結果

- 汎用適用のみ：cm MATCHED 44,284（適用前は製品単位参照のみで596）
- 製品単位参照（596件側）との合算：MATCHED 44,721（重なり159、汎用のみ44,125、製品単位のみ437）
- issues は 89,675 → 45,987 に減少
- 残り MISSING 32,716。主な内訳：Jordan Kids 8,763、Nike Kids 4,431、Adidas Kids 2,073、Puma Men 1,472、Crocs Kids 1,293、Crocs Men 1,221、Salomon Men 1,116、New Balance Kids 1,071、Converse Men 969、HOKA Men 903、Saucony Men 873、Vans Kids 636

## 次の適用対象

- キッズ：C／Y等の区分も公式表内のカテゴリーとして、ブランド×キッズ区分の公式表を同じ方式で適用する（Nikeキッズは公式表にCM/JP列があることを2026-11-17出典調査で確認済み）。
- 未収録ブランド（Puma、Crocs、Salomon、Saucony等）：公式表を収録してから同じ方式で適用する。
- HOKA／UGGはモデル差の実例があるため製品単位参照を維持し、今回の合算でも製品単位のみで437件がMATCHEDしている。

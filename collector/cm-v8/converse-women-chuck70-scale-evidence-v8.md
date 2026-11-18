# CONVERSE Women Chuck 70 - size scale determination (v8-3, 2026-11-19)

対象2商品（Shoe Palace, department=Women）:
- 7508278083790 Chuck 70 HI Womens (Black/Beige), style A12350C
- 7550076420302 Chuck 70 Roses (title says Mens, department tag Women), style A10637C

## 判定: 両商品とも Shoe Palace のサイズ選択肢は US Men（ユニセックス）体系

根拠:
1. 両商品のサイズ選択肢は 3, 3.5, ..., 13 で完全に同一。US Women 体系の Chuck 70 は
   5 から始まり 15 まであり得るため、3〜4.5 の存在と上限 13 は Men 体系と一致する。
2. A12350C: Converse公式カナダの同品番ページはバリアントを "Men's 3 / Women's 5"
   の併記で販売（ユニセックス）。BSTN も同品番を Sizing Standard: Men / Unisex と明記。
3. A10637C: Converse公式フィリピンの Chuck 70 は "unisex product that follows
   Men's Sizing" と明記。AFEW は同品番を Gender: Unisex、US 3 起点の表で掲載。
   Converse南アフリカ公式の同品番ページの表も US MEN'S 3 = US WOMEN'S 5 の併記。
4. 比較対象の Men 商品 A07901C（7288323408078、v7で適用済み）は 4〜13 の同体系。

## 適用（GPT v7検収の規則: US Men なら実箱確認済み 3.5/4/4.5 のみ）
- 実箱確認済み JP ラベル値: US Men 3.5=22.5, 4=23, 4.5=23.5（Chuck 70 Hi 166318C の箱）
- 2商品 × 3サイズ = 6 バリアントを scoped 参照で適用。それ以外のサイズは実箱根拠が
  ないため MISSING のまま（公式 LENGTH は足長であり JP ラベル値ではないため使わない）。

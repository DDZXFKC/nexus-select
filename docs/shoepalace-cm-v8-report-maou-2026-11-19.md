# Shoe Palace cm v8 実行報告（魔王ちゃん → GPT検収依頼）

対象: GPT v7検収・v8実行指示（コミット 9c360412）の手順0〜3を実施。
v7出力は保全し、v8は別出力（out-v8-a / out-v8-b）で2回実行、出力完全一致
（variants.csv md5: f856644ce74f9c76f4b3f9caf6ebb823）。

## 結果（全103,834バリアント、variant_id集合はv7と完全一致・重複なし）

| 項目 | v7（合算値） | v8 | 増減 |
|---|---|---|---|
| MATCHED | 68,767 | 69,741 | +974 |
| MISSING | 8,670 | 7,696 | −974 |
| NOT_APPLICABLE | 26,387 | 26,387 | 0 |
| SIZE_SYSTEM_REVIEW | 10 | 10 | 0 |

- 状態遷移: MISSING→MATCHED 977件、MATCHED→MISSING 3件（隔離分）。
全遷移は `collector/cm-v8/cm-status-transitions-v7-v8.csv`（980行）に保存。
- 根拠別MATCHED: 汎用参照 68,430件 / 商品単位（scoped）1,311件。
MATCHED全件に cm_source_url と cm_size_system が出力へ記録された（欠落0件）。
- 在庫ありMISSING: 1,785件。

## 手順0（誤適用防止）

### 0a. BIRKENSTOCK 332件のEU確認 → 全件確認済み、scoped化
- 対象53商品すべてについて、raw原文の品番タグ（SKU_/STYLE_、5〜7桁）が
Birkenstock公式の Item no. と一致し、サイズ選択肢がEU範囲の整数のみである
ことを商品単位で確認した。公式ページ（例: 品番1029651）は同品番をEUサイズ
主表記で掲載している。
- 証拠: `collector/cm-v8/birkenstock-eu-evidence-v8.csv`（53商品分）。
- v8では汎用参照からBIRKENSTOCK全行を外し、商品単位参照
`cm-scoped-birkenstock-eu-v8.csv`（332行）でのみ適用。332件すべて
reference_type=scoped でMATCHED（値の変更なし）。
- なお同ブランドのキッズ商品1点（US表記）とソックス2点は元々NOT_APPLICABLEで、
今回も対象外。

### 0b. UGG Kids 224件の年齢区分確認 → 221件整合、3件を隔離
- 43商品のタイトル上の年齢区分（Grade School / Infant Toddler / Toddler）と
サイズ接尾辞（C/Y）を、公式PDFの区分（TODDLERS / LITTLE KIDS / BIG KIDS）と
全件照合した。証拠: `collector/cm-v8/ugg-kids-age-evidence-v8.csv`。
- 隔離3件（variant_id 41707750162638 / 42228915372238 / 42843176403150）:
サイズ構成が 1C・2C・4C のみの乳児向け3商品（Fluff Yeah Slides Infant Toddler、
Bixbee Infant Booties、Tasman Slipper Infant Toddler）の 4C。
この構成は公式PDFの INFANTS 複合サイズ（0/1、02/03、04/05）に対応する疑いが
あり、4C は TODDLERS の 11.5 ではなく INFANTS 04/05 の 12.5 の可能性がある。
個別根拠が取れるまでMISSINGへ戻した（`ugg-kids-quarantine-v8.csv`）。

### 0c. 汎用+商品単位の同時適用と出典の出力保存（code8）
- 修正Python v8（`collector/cm-v8/shoepalace_repair_v8.py`）:
- 汎用参照と商品単位参照を1回の実行で同時適用（scoped優先）。
複数のscopedファイルを統合読み込み可能にした。
- 汎用参照に source_url / size_system 列を追加
（`cm-generic-combined-v8.csv`、884行。全行に出典URLと出典メモあり）。
汎用ヒットでも cm_source_url / cm_size_system が出力に残る。
- 出力に cm_reference_type（scoped / generic）を追加。
- 隔離リスト（variant_id指定）で一致を強制的に止める仕組みを追加。
- 本実行の前に、この仕組みだけを先行検証した（汎用v8＋Converse/Birkenstock
scoped＋隔離のみ）: 結果は MATCHED 68,764（= v7合算 −隔離3）、遷移は
隔離3件とConverse scoped 2件のみ、3回実行で出力ファイル完全一致。
※先行検証の初回だけ、実行時統計の issues 表示が 21,733 と出たが、出力
ファイル自体は3回とも同一（issues 21,507行）で、表示側の混線と判断した。

## 手順1. HOKA Women 549件 → 286件を商品単位で適用
- GPT支給のモデル別表（gpt-model-exceptions.csv、公式チリ出典）を、
対象モデル・世代が一致する商品にだけ商品単位参照で適用した
（`cm-scoped-hoka-women-v8.csv`、22商品・286バリアント）。
- 表A（US5=21.5系）: Clifton 10 / 11、Rincon 5
- 表B（US5=22系）: Rincon 4、Bondi 9、Transport 2
- 判断の明示: 表Bの対象名は「Transport」で、店の商品は「Transport 2」。
旧世代ではなく現行世代のため適用したが、検収で確認してほしい。
- 残り263件は適用外: 旧モデル（Clifton 9系、Bondi 7、SpeedGoat 6、Kawana 2、
Mafate系、Clifton UTL、Bondi Mary Jane）と、表の範囲外サイズ（US12など、
外挿なし）。

## 手順2. UGG大人 685件 → 公式表を直接確認し商品単位で適用
- 集計: 対象75商品（Women 57 / Men 18）、全て靴（BOOTS / SANDALS / LIFESTYLE）。
サイズ原文は通常のUS数値のみ（EEE等の幅表記は店データに無し）。
- 公式表は UGG公式の Product-SizeChart（all-gender footwear）の
Japan (CM) 列を直接読み取り、48行を確定した
（`ugg-adults-official-chart-v8.csv`、出典URL付き）。
- GPT支給の旧84行は、この公式Japan列と Men 14 以降で食い違う
（例: Men 14 は旧行 32 だが公式Japan列は 31.5。Men 15: 33 vs 32、
16: 34 vs 32.5、17: 35 vs 33、18: 36 vs 33.5）。
そのため旧行は使わず、公式表そのものから商品単位参照を生成した
（`cm-scoped-ugg-adults-v8.csv`、685行）。Women 482件・Men 203件がMATCHED。
- 同一公式表が男女共通であることは公式ページ上で確認済み。汎用参照への
UGG大人追加はせず（コードの汎用拒否は維持）、商品単位のみで適用した。
汎用化してよいかは検収で判断してほしい。

## 手順3. CONVERSE Women Chuck 70 の2商品 → Men体系と確定し6件適用
- 対象: 7508278083790（A12350C）、7550076420302（A10637C、タイトルは Mens 表記）。
- 判定: 両商品ともサイズ選択肢は US Men（ユニセックス）体系。
根拠の詳細は `converse-women-chuck70-scale-evidence-v8.md`:
選択肢が 3〜13 で同一（Women体系なら 5〜15）、Converse公式（カナダ／
フィリピン／南アフリカ）が同品番・同モデルを Men's/Women's 併記または
"follows Men's Sizing" で販売していること、等。
- GPT規則どおり、実箱確認済みの Men 値（3.5=22.5、4=23、4.5=23.5）のみ
2商品×3サイズ=6件を適用（scoped参照は合計8行 = 既存Men商品2行 + 今回6行）。
他サイズは実箱根拠がないためMISSINGのまま。

## 回帰確認（fd11fee8の指定項目）
- HOKA Men: 範囲内（US7〜14）はMATCHED維持、範囲外120件はMISSINGのまま。
- UGG: 汎用参照のUGG行はKidsのみ。大人・Kidsとも適用はscoped/許可範囲のみ。
- EU: 確認済み商品のみscoped適用。未確認の同数値への一般化なし。
- CONVERSE: Chuck 70以外（All Star等）は全てMISSINGのまま
（Men 967 / Women 175 / Kids 208）。
- 非靴: NOT_APPLICABLE 26,387件不変。重複IDなし。原本（raw）への書き込みなし。
- product_type × cm_status の内訳表を本報告末尾に付けた（Claude要請 a538ce02）。

## 残りMISSING 7,696件の内訳（主なもの）
| 区分 | 件数 | 扱い |
|---|---|---|
| ADIDAS Kids | 2,073 | GPT指示で保留（JPラベル資料待ち） |
| CONVERSE Men | 967 | 実箱・公式JP資料が取れた分だけ |
| REEBOK Men | 348 | 手順4の対象 |
| HOKA Women | 263 | 旧モデル・範囲外（資料待ち） |
| VANS Kids | 221 | 手順4の対象 |
| CHAMPION Kids | 216 | 公式キッズ表なし（資料待ち） |
| ANTA Men | 212 | 公式JPラベル資料なし |
| VEJA Women | 209 | 手順4の対象 |
| CONVERSE Kids | 208 | 資料待ち |
| NEWBALANCE Kids | 197 | 日本公式表に無いサイズのみ残存 |
| ASICS Kids | 184 | 足長のみ（資料待ち） |
| RALPH LAUREN Men | 150 | 公式対応表未確認 |
| ADIDAS Men | 128 | 表に無いサイズ |
| HOKA Men | 120 | GPT承認範囲外（US7〜14以外） |

## GPTへの確認事項
1. 手順1の Transport 2 を表B「Transport」に含めた判断でよいか。
2. 手順2の UGG大人: 商品単位のままでよいか、汎用参照への追加（コード変更）を
許可するか。
3. 専用ブック「ブランドサイズ表」のサイズ表タブで、
UGG Kids に重複キーが16件あり、うち7件は cm が競合している
（例: 11C = 17.5（旧GPT行） vs 18（PDF採用行）、5C = 12.5 vs 12）。
旧GPT行84件（出典「UGG公式（ugg.com サイジング情報）」）には、
手順2で判明した Men 14 以降の誤りも含まれる。
旧行の扱い（別タブへ退避して現行タブを確定値だけにする等）を指示してほしい。
今回はブックへは一切書き込んでいない。
4. 次は手順4（REEBOK / VEJA / VANS / NEWBALANCE等の集計と少量根拠で多く
解消できる順）に進んでよいか。

## 保全
- 原本raw・DB・本番・商品シート・価格への書き込みなし。v7出力は不変更。
- 本番投入・価格反映はしていない。

## Claude指摘（98991160）への実測回答
- 靴判定がタグのみのため、靴なのに NOT_APPLICABLE へ黙って落ちる商品がないか、
  v8出力で実測した。product_type が靴らしい区分（LIFESTYLE / BASKETBALL /
  RUNNING / SANDALS / SKATE / BOOTS 等）の NOT_APPLICABLE 商品について、
  タイトルに靴を表す語（shoe / sneaker / boot / sandal 等）を含むものを抽出した
  結果は8件のみで、全件が帽子・シャツ・ショーツ（店名「Shoe Palace」の "Shoe" や
  "Sneaker Patch" という柄名による誤検出）だった。実際の靴の取りこぼしは
  検出されなかった。全 product_type でも同様で、検出647件の大半は HATS の
  店名由来だった。
- code6 のGitHub未登録という追記指摘（2026-11-19 00:30）については、
  コミット 452a5e36 で code6 を登録済み。code7 は c58fb671、code8 は本登録に含む。

## 付録: product_type × cm_status（v8）
| product_type | MATCHED | MISSING | NOT_APPLICABLE | SIZE_SYSTEM_REVIEW |
|---|---|---|---|---|
| BASKETBALL | 22,294 | 822 | 10 | 0 |
| RUNNING | 23,164 | 1,464 | 29 | 0 |
| LIFESTYLE | 10,163 | 4,517 | 3,460 | 10 |
| TRUE RETRO | 6,415 | 8 | 0 | 0 |
| SANDALS | 4,607 | 364 | 6 | 0 |
| SKATE | 2,303 | 373 | 16 | 0 |
| BOOTS | 686 | 148 | 0 | 0 |
| TRAINING | 109 | 0 | 0 | 0 |
| その他（衣類・バッグ・帽子等） | 0 | 0 | 22,866 | 0 |

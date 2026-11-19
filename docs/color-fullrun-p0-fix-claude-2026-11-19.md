# 色分解生成PythonのP0修正（Claude、2026-11-19）

担当：Claude（GPT検収 caafbc5／b5c5027、魔王ちゃん確認 09:30）。
コード：collector/color_fullrun.py。テスト：collector/test_color_fullrun.py（期待値assert 33件、全件合格）。
旧スクリプト docs/color-fullrun-generate-2026-11-19.py は変更せず残す（履歴）。

## 1. 使い方（どちらもオフライン。シートへの書き込みはしない）
- recompute：シートの2タブの書き出し（CSV、またはシート取得JSON＝先頭行が見出し）から、派生列だけを新ルールで再計算する。魔王ちゃんの dry-run（55a4d82）と商品単位で突き合わせる用。
  ```
  python3 collector/color_fullrun.py recompute --master <カラーマスター.csv|json> --products <商品カラー.csv|json> --output <新しい出力フォルダ>
  ```
  出力：product_color_recomputed.csv（全列＋派生列）、changes.csv（商品・列・前→後）、integrity_issues.csv（参照の不整合）、summary.json（状態別・旧→新の遷移件数、2回実行一致のハッシュ）。
- generate：シートに無い商品だけの候補を作る（新しい店・追加分用）。
  ```
  python3 collector/color_fullrun.py generate --master <現行の全カラーマスター> --sheet-products <現行の商品カラー> --v8-products <products.csv> --raw-dir <raw/YYYYMMDD_HHMMSS> --output <新しい出力フォルダ>
  ```

## 2. 丸窓ステータス（案B）
先頭 min(3, n) 色だけで判定、強い順に：
- HOLD：colorway_status=HOLD_CONTRADICTION／表示枠の色IDが空・マスターに無い・トークン不一致・他ブランド（他商品）の色を参照／表示枠の色の hex_status=CONFLICT
- UNKNOWN：0色／表示枠に有効な#RRGGBBが無い／表示枠が Multi・Multicolor 等の特殊トークン（HEXが入っていても）
- DRAFT：表示枠すべて有効HEX、1つ以上が APPROVED_APPROX でない
- CONFIRMED：表示枠すべて有効HEXかつ APPROVED_APPROX
- 色系統（family_status）は条件にしない。色コード不明の枠を飛ばして4色目を繰り上げない。重複色はそのまま。
- 4色目以降の参照不整合は丸窓には影響させず、integrity_issues.csv に必ず出す（書き込み前の整合ゲート）。

## 3. GPT指摘への対応
| 指摘 | 対応 |
|---|---|
| 既存トークンを scope 無視でスキップ（Phantom問題の再発） | 照合は「その商品のPRODUCT行→そのブランドのBRAND行→COMMON行」。他ブランドのBRAND行は使わない（JORDANのPhantomはNIKEの行を借りない）。 |
| PRODUCT scope未対応 | 対応。 |
| ブランド表記ゆれ | 照合時に NFKC・小文字・空白除去で正規化（adidas／ADIDAS 等）。 |
| 既存scope重複がdictで隠れる／assertが最適化で消える | マスター読み込み時に、ID形式（C-数字）・ID重複・scopeキー重複を例外で止める（assert不使用）。 |
| 再実行で全IDが振り直される | 既存IDは変更しない。新トークンだけ、現行全マスターの最大ID＋1から採番。古い13行から再生成しない（--master に現行全マスターを渡す）。 |
| 新トークンのscope | オーナー決定（965d6d3、全ブランド共通）に従い、新規は常にCOMMON。既存のBRAND行（Phantom等）は移行確認まで残し、そのブランドだけに使う。 |
| 件数がトークン単位（重複色で水増し） | 解決した color_id ごとに distinct 商品数・在庫あり distinct 商品数を出力（color_id_distinct_counts.csv）。 |
| search_families にDRAFTが混ざる | 確定（family CONFIRMED）と候補を別列に分離：search_families_json／search_families_candidates_json。 |
| SOLE_FAMILY の単一主色断定 | 全構成色に系統が付いて、かつ1系統の時だけ主色にする。 |
| TITLE_CANDIDATE の一律確定 | c4aac99c の条件（末尾括弧＝候補、既知suffix「Free Shipping」「Limit n」だけ許可、handle 末尾が候補のスラッグに境界一致、数量・サイズ等の非色を除外、Color_タグと系統が矛盾しない）を満たす時だけ CONFIRMED_BY_TITLE_RULE。満たさなければ TITLE_CANDIDATE のまま。 |
| raw欠落・重複・ID不一致を黙って通す | すべて例外で停止。 |
| 取得日時 | raw のフォルダ名（YYYYMMDD_HHMMSS）から取る。名前が違う時は --observed-at 必須。 |
| 手動確定の保護 | recompute は派生列（丸窓HEX・丸窓状態・検索系統）だけを再計算。ID・色名原文・構成色・colorway_status 等はシートの値をそのまま使い、作り直さない。 |
| negative_tests が件数抽出だけ | 期待値assertのテスト33件に置き換え（単色／2・3色／4色以上／重複色／空ID／他ブランド参照／HEX CONFLICT／Multiが表示枠・4色目／色名なし／未知HEX／状態の優先順位／列保護／ID採番の安定／raw欠落・ID不一致／タイトル規則 等）。 |

## 4. 魔王ちゃんへのお願い
1. 現行シートの2タブ（バックアップ済みのもの）を CSV か JSON で用意し、recompute を実行。
2. 結果の swatch_status を、魔王ちゃんの dry-run（4217／2857／4700／3）と商品ID単位で突き合わせ、違う商品があれば changes.csv・integrity_issues.csv と一緒にGitHubへ。違いが出た場合はどちらが正しいかをClaudeが確認する。
3. 承認10色の反映・Multi空欄化は、この突き合わせが一致してから（b5c5027 の反映順序どおり）。

## 5. 修正2（GPT監査 8b166ed／99ab4f9 への対応、2026-11-19）
| 指摘 | 対応 |
|---|---|
| 1. Multi かつ HEX CONFLICT が UNKNOWN になる | 同じ枠では HEX CONFLICT を先に見る（HOLD優先）。テスト追加。 |
| 2. generate が PRODUCT 行を見ていない | 構成色の照合・タイトル判定とも、その商品のキー（shop|market|商品ID|single）を渡して PRODUCT→BRAND→COMMON の順に照合。同名3行のテスト追加。（移行期間だけの動き。共通IDへの統合後は COMMON だけになる） |
| 3. raw の重複ID | 契約を明示：同じIDが「全く同じ内容」で2回出る（ページの重なり）は許容して件数を summary の raw_identical_duplicates に記録。内容が違えば停止。IDが空・欠落も停止。テスト追加。 |
| 4. swatch_reason の上書き | 出力専用の診断列 diag_swatch_reason に変更。シートの既存列（swatch_reason 等）は書き換えず、changes.csv にも出さない。テスト追加。 |
| 5. SP/US 固定・主色の確定扱い | generate は --shop-code / --market を必須にした（既定値なし）。対応するのは1商品ID=1色（single）の店だけと明記。主色は1系統に揃った時だけ付け、全構成色の family_status が CONFIRMED の時だけ main_family_status=CONFIRMED、それ以外は DRAFT。 |
| 追加：active 検査 | マスター行の active が TRUE でない色を参照していたら HOLD（INACTIVE_MASTER_ROW）。 |
| 追加：component_count・原文の整合 | colorway_original を「/」で分けた並びと構成色の並びが違う、または component_count が違う商品は HOLD にし、integrity_issues.csv に出す。 |
| 追加：候補familyの CONFLICT 分離 | 検索用の系統を「確定／候補／矛盾」の3列に分けた（search_families_conflict_json を追加）。 |

- テストは 33→43件、全件合格。
- 注意：search_families_conflict_json は新しい列なので、recompute の changes.csv に全商品分の「空→値」が出る。シートに列を追加して書き込むかは GPT の判断で、現行シートには無条件に書き戻さない（8b166ed の指示どおり）。
- Museへ：テスト再実行と、現行バックアップでの recompute 回帰比較（swatch_status は前回の書き込み結果 6,407／667／4,700／3 と一致する想定。違えば理由を記録）。

## 6. 共通化dry-run（b85ba18）への対応（Claude、2026-11-19 10:00）
- 問題：統合後の旧行（C-2662/2663/2664）は非アクティブで残る。旧コードは非アクティブ行も検索対象にしていたため、generate で NEW BALANCE 等の新商品の「Phantom」が非アクティブのBRAND行に割り当てられ、HOLD（INACTIVE_MASTER_ROW）になっていた。また非アクティブ行のscopeもCOMMONへ変えると重複キーで停止していた。
- 修正：非アクティブ行は by_id には残す（旧参照は引き続き INACTIVE_MASTER_ROW で検出）が、検索（lookup）と重複キー検査からは外す。アクティブ行同士の重複は従来どおり停止。
- テスト：4件追加、計47件すべて成功。recompute の結果は、非アクティブ行に重複キーが無い現行シートでは変わらない。

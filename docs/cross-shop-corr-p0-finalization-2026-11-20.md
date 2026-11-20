# 横断corr P0確定記録（2026-11-20）

位置づけ：GLM検収記録 `docs/cross-shop-corr-review-glm-2026-11-20.md`（コミット b2f986b7）の後続記録。魔王ちゃんによるP0検証・P1検証と、GLMのパリティゲート裁定を受けて、P0の確定をここに宣言する。

根拠文書：
- GLM裁定（パリティゲート解釈・source_id統一先）：2026-11-20 GLM回答（検証側保管：glm_parity_gate_20261120）
- P0検証レポート：魔王ちゃん検証（テスト36/36、実データパリティ differing=0、erratum適用確認）
- P1検証レポート：魔王ちゃん検証（テスト39/39、候補レポート全60件カバー）

## 1. P0確定の宣言

- GLM裁定により、パリティ基準は解釈(a)＝**商品単位の意味パリティ**で充足する。**P0は確定とする。**
- ゲート（アダプタ内蔵の参照パリティゲート）のキー方式差異は、受理判定ではなく機械の修理事項として切り分け、P0には含めず §6.1 の後続必須タスクとする。
- **source_id は interface v1 の長さ区切り安定IDに統一する。** 検証用アダプタの素の商品IDは「参照形式」として位置づけ、ゲート側の正規化経由でのみ比較対象とする。
- **「全行の source_id が manifest で商品IDへ一意に読み替えられること」を出荷不変条件に昇格させる。**

## 2. GLM裁定の要旨

- 基準「検証用アダプタとの出力パリティ（差分空）」が保護すべき性質は、相関ロジックの判定結果が両実装で一致すること。今回の内訳は differing=0（SP・FLとも）、manifest読み替え後の全フィールド差分ゼロ、バケット計数まで完全一致であり、基準が守ろうとしているものは成立している。
- source_id は行のアドレス表現であって相関意味論の一部ではない。本番側の方式は interface v1 の規定に従った側であり、表現差は仕様適合の帰結である。
- 統一先を interface v1 の長さ区切り安定IDとする理由：interface契約に既に規定され本番側は適合済みであること。横断corrは複数ショップ横断が前提で、素の商品IDのID空間はショップ内でのみ一意であり、現在の非交差は保証ではなく偶然であること。長さ区切りは値に区切り文字が混入しても一意にパースでき、決定的に再生成可能であること。人間可読性の弱点は manifest で補完する。

## 3. 解釈の明文化（受理条件①）

GLM裁定の受理条件1点目として、以下の解釈を本記録に明記する（GLMが次回レビューで否認できる形で置く）：

> パリティは商品単位の意味パリティとし、source_id は manifest 経由で正規化して比較する。本解釈は source_id の表現差に限定し、他フィールドの不一致免除には適用しない

## 4. 受理条件への対応状況

### ① 解釈の明文化
本記録 §3 に収録済み。

### ② 読み替え突合手順の固定化
突合は検証資産 `~/workspace/cross-shop/verify-p0/` に再実行可能な形で固定されている。手順は次のとおり：

1. `verify-p0/build_interface.py`：実CSVから interface-v1 CSV（431行＝SP 163＋FL 268）を構築する。マッピングは phase2 で確立した検証用アダプタ（`verify-corr/build_inputs.py`）と同一（SP：スクレイプ元CSVの `STYLE_` タグを style/color に分割、販売可能リストにあれば sellable=1、原価は `round(USD×158×1.02＋3,760)`。FL：fl_margin の HOKA/UGG/Vans 268件、原価は cost_jpy）。
2. 本番アダプタ `tools/cross_shop_corr_adapter.py`（CLI）：interface-v1 から corr 入力（SP 163／FL 268）と manifest を出力する。実行時に全431行の復元照合を行い roundtrip=PASS。
3. corr 本体 `tools/cross_shop_corr.py`（CLI）：処遇・採用を出力する。
4. `verify-p0/compare_parity.py`：manifest 経由で本番側 source_id を商品IDへ読み替え、前回基準（`verify-corr/run/corr_out.csv`・`adoption_out.csv`）と全件突合する。

使用 manifest の特定：`verify-p0/run/manifest.json`、SHA-256 = `93f949af55ff90753ce74da3211bf2425641e8fdce3ac46bf7677a3f475910e5`

### ③ エビデンス（P0検証レポートの数値）
- テスト：**36件中36件合格・不合格0件**（従来契約テスト20＋P0新規7＋既存identityスイート9。検証環境に pytest が未導入のため unittest で実行）
- roundtrip：**PASS**（アダプタが全431行について manifest からの復元＝原行列を照合）
- 処遇パリティ：268件・**differing=0**（status／sp_style／sp_color／rule／matched_key／candidate_count／tags／hold_reason_codes／evidence_tier／notes／対応SP商品）
- 採用パリティ：268件・**differing=0**
- アダプタ出力 vs 検証用アダプタ出力（商品単位で brand／style／color／sellable／name／原価4項目）：SP 163＋FL 268・**differing=0**
- バケット計数：AUTO 28（法則27＋手動1）、採用 SELECTED 28＝SP 25／FL 3（手動ペアを除くと SP 24／FL 3 で参考値と一致）、HOLD_NO_COLOR 33、HOLD_LEGACY_NUMERIC 27、NO_MATCH 180
- Nike再確認：K1衝突 0件（`{}`）、NO_MATCH 1,879／HOLD_UNVERIFIED_FORMAT 672／AUTO 0（前回監査と同一）
- コーパス特定：interface-v1、SP 163＋FL 268
- erratum：仕様本編の3箇所に過不足なく適用済み（コミット 14c232c7）。42110519＋HOKA 13件群の LEGACY_NUMERIC ロックは契約テストに追加・合格済み
- 中核ツール `tools/cross_shop_corr.py` と従来契約テストは前回検証時のコピーとバイト単位で完全一致（無変更）

## 5. P1検証結果の要旨

- テスト：**39件中39件合格・不合格0件**（identity 9＋契約20＋P0 7＋P1 name_aid 3）。P1追加後も従来分に回帰なし。GPT証拠文書の「39/39 PASS」主張と一致。
- 候補レポート（`tools/cross_shop_name_aid.py` の実データ実行）：対象は **ちょうど60件** ＝ HOLD_NO_COLOR 33件（HOKA 25／UGG 8）＋ HOLD_LEGACY_NUMERIC 27件（HOKA 13／UGG 3／Vans 11）。欠落0・余分0。全1,695行が suggestion_only（human_review_required=1／match_status=UNVERIFIED_CANDIDATE）で、**自動採用・自動登録はなし**（実行時JSON：auto_or_manual_mapping_written=false）。候補の名前裏付けは実在のSP商品に基づくことをサンプル突合で確認済み。
- 実行ログ面：P0証拠文書（`docs/cross-shop-corr-p0-evidence-gpt-2026-11-20.md`）と workflow Run **44700665141**（head_sha c2032a51、status=completed、**conclusion=success**、GitHub APIで独立確認済み）で充足。
- GPT証拠文書が「未実施（ゲートOPEN）」とするアダプタ実コーパスパリティは、魔王ちゃんのP0検証で実施済み（differing=0）であり、GLM裁定（§1〜§3）により**実質クローズ**とする。
- **P1はGLM確定スコープ（候補提示レポート生成のみ／自動採用禁止／登録は手動シード経由のみ／対象はNO_COLOR・LEGACY両キュー）の範囲で完了。**

## 6. GPTへの後続タスク

### 6.1 ゲート比較キーの manifest 正規化（必須・GLM合格条件つき）
方針はゲートの比較キー正規化（両方式→manifestで商品IDへ読み替え）。検証用アダプタ側を interface v1 形式に出し直す代替案は、基準値の再生成と再検証を伴うため非推奨（GLM）。

合格条件：
- 正規化は manifest 参照または長さ区切り形式の決定的パーサに限る。曖昧一致・ヒューリスティック禁止。
- 正規化不能な source_id（パース失敗、manifestで0件または複数件ヒット）は黙って除外せず、該当IDを列挙して FAIL。
- 正規化後のキーがコーパス内で一意であること（多対一に潰れないこと）を検証し、潰れた場合は差分として報告。
- missing／extra／differing の3分類は正規化後も維持し、適用した正規化方式を出力に明示。PASS条件は **differing=0 かつ missing=extra=0**。
- 現行コーパスで、修正後ゲートの結果が今回の読み替え突合（PASS・同計数）と完全一致すること。
- 相関ロジック本体への変更はゼロ（diffレビューで確認）。
- テスト：正規化器の単体（正常系・不正ID・衝突）＋両形式フィクスチャによるゲートE2E。

### 6.2 name_aid 候補の絞り込み
- 現状は候補が多く（1件あたり中央値27件・最大57件）、汎用トークン（WHITE・BLACK・BONDI 等）の断片一致で弱い候補が大量に混ざる。単独数字がトークン化されないためモデル世代を区別できない（例：Bondi 7 の候補上位に Bondi 9 製品群）。
- オーナーの一回限りの目視確認に回す前に、`style_suffix_hint` 等による絞り込み・順位付けの改善が必要。強い信号である style_suffix_hint=1 は現状14行のみで、発火箇所の精度は高い。

### 6.3 P2 ADV_NAME_NOTE の精緻化（未着手）
- Nike追補の正規化（NFKC・ハイフン種・ケース）を流用し、コンテンツトークン重複閾値で発火させる。raw比較は診断フィールドとして残す。採用判断に無関係のためブロッカーではない（検収記録の差し戻しP2どおり）。

### 6.4 関連する残件（記録）
- NO_COLOR 33件の個別監査（末尾英字＝幅記号 B/D/EE 等の点検、model+color裏付けペアの有無確認）：GLM条件付き第二フェーズ。name_aid はこの監査を代替しない。文法拡張の承認は監査結果を受けたGLMの再判断事項。
- raw→interface-v1 変換器の生産コード化：現行の納品は interface-v1→corr入力のアダプタであり、実CSV→interface-v1 の変換は生産コードとしては未提供（P0検証では検証側ビルダーが橋渡し）。FLのローカルデータには商品URL列がなく、interface の source_url を実データで埋めるには収集側の補完が要る。
- HOLD_NOT_SELLABLE の実データ経路：非販売可能を含む全コーパスの入手時に再検証する（繰延条件どおり）。

## 7. 再検収・再判断のトリガー（検収記録から継続）

- AUTO／Stage3出力を変える改変を行う場合のみ再検収。
- GLMの再判断が必要なのは：文法拡張の承認時、設計確定時、AUTO／Stage3出力を変える改変時、全コーパス入手時。
- §6.1 のゲート正規化は合格条件を満たす限りGLMの追加判断なしで実行可能。

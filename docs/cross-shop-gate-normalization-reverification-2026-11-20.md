# ゲート正規化 修正の再検証レポート — 2026-11-20

## 結論：**合格**

前回不合格（`gate-normalization-verification-2026-11-20.md`、GitHub登録 `a1a6c4e0`）の差し戻し3点は**全て充足**された。修正済みゲートは実コーパスで SP・FL とも全項目0のPASSとなり、前回の本番結果（処遇・採用パリティ、Stage3出力）とも完全一致する。name-aid絞り込みとP2診断も、自動採用なし・本体無変更の設計どおり納品されている。残る留意点は2件あるが、いずれも合格条件の範囲外である（末尾の注記参照）。

## 対象

- リポジトリ：DDZXFKC/nexus-select、ブランチ integration/grok-review
- 検証時点の最新HEAD：`a1a6c4e0`（前回検証レポートの登録コミット。その直下がGPTの修正群）
- GPTの修正コミット群（全て実在を確認）：
  - `1b8c6129`：FL 4要素再構成の修正（本丸）
  - `15481b31`：CI（workflow へのテスト登録）
  - `88d138cf`／`4aeef16d`：name-aid絞り込み（ツール＋テスト）
  - `65a97eae`／`147f647a`：P2診断（ツール＋テスト）
  - `48c6fcd4`：証拠文書 `docs/cross-shop-corr-post-p0-followup-gpt-2026-11-20.md`
- 合格条件の正本：`docs/cross-shop-corr-p0-finalization-2026-11-20.md` §6.1 および前回検証レポートの差し戻し3点

## 差し戻し3点の判定

### ① FL再構成の4要素化 — ✅ 充足

- アダプタ（`tools/cross_shop_corr_adapter.py`）の前回検証時点からの差分は **`_manifest_product_keys()` の1箇所のみ**（13,402 → 13,503 bytes）。
- 修正内容：FL の再構成が `(shop, product) + (corr_code,) + ("",)` の4要素になった。生成側 `adapt()` の規則は `key = (shop, product, code, color)`（SP は corr_style＋corr_color、FL は corr_code＋color=""）であり、再構成側と規則が一致した。
- 前回FAILの実例（商品 0011999）でいうと、再構成が実際の source_id `2:FL7:00119997:00119990:` と一致するようになった（実コーパスE2Eで全268件確認済み、下記③）。
- 注記：「生成と再構成を同一の定義から取る」形については、共通ヘルパーへの一本化ではなく、生成側の4要素スキーマを再構成側が shop 分岐で再現する実装である。規則の一致という本質要件は満たされ、フィクスチャE2Eと実コーパスE2Eの両方で担保されているため合格とするが、将来どちらか一方のスキーマを変える場合は両側の同時変更が必要な点は残る。

### ② workflow へのテスト登録 — ✅ 充足

- `.github/workflows/corr-p0.yml`（最新HEAD時点）の**トリガーパスと実行ステップの両方**に `tests/test_cross_shop_parity_manifest.py` が含まれている（ステップ名「Manifest source ID normalization gate (§6.1)」）。
- あわせて name-aid絞り込み（`test_cross_shop_name_aid_refine.py`）とP2診断（`test_cross_shop_name_note_diagnostic.py`）のテストおよび各ツールもパス・ステップに登録されている。
- GPT証拠文書によれば、初回ラン `44710047870` で当該テストが1件失敗し、`1b8c6129` の修正後に再実行ラン `44710122921` が成功（55件PASS）したとの記録がある。ラン自体の直接確認は読み取り専用ツールの範囲外のため未実施だが、下記③のとおり同一の55件をローカルで再実行し全合格を再現している。

### ③ 全テスト＋実コーパスE2E — ✅ 充足

**全テスト（ローカル再実行、unittest discover、全7ファイル）**：

| スイート | 件数 | 結果 |
|---|---|---|
| offer契約（identity） | 9 | 全合格 |
| corr契約 | 20 | 全合格 |
| P0ガード・アダプタ | 7 | 全合格 |
| name_aid（旧） | 3 | 全合格 |
| parity manifest（§6.1） | 8 | 全合格（前回不合格だった FL サブテスト `test_semantic_parity_with_raw_reference_product_id_SP_FL` も合格） |
| name_aid_refine | 4 | 全合格 |
| name_note_diagnostic | 4 | 全合格 |
| **合計** | **55** | **全件合格** |

前回の再検証範囲（47件）を包含し、回帰なし。

**実コーパスE2E（修正済みCLI、前回と同一のピン留め資産で実行）**：
- 入力：`verify-p0/run/interface_real.csv`（431行＝SP 163＋FL 268）、manifest SHA-256 = `93f949af55ff90753ce74da3211bf2425641e8fdce3ac46bf7677a3f475910e5`（確定記録と一致）
- 参照：検証用アダプタ出力 `verify-corr/run/sp_input_cost.csv`（163件）／`fl_input_cost.csv`（268件）

| 対象 | pass | missing | extra | differing | invalid |
|---|---|---|---|---|---|
| SP（163件） | **true** | 0 | 0 | 0 | 0 |
| FL（268件） | **true** | 0 | 0 | 0 | 0 |

- 終了コード0、往復（roundtrip）もPASS。適用方式は両方とも `MANIFEST_SHOP_PRODUCT_V1`。
- 生成された本番出力 `sp_out.csv`／`fl_out.csv` は前回の本番出力（`sp_prod.csv`／`fl_prod.csv`）と**バイト単位で完全一致**。新manifest の entries 431件も旧manifestと完全一致（ファイルSHAの差は parity 記録フィールドの有無のみ：旧は `NOT_CHECKED`、新は今回のPASS結果を記録）。
- 従来の読み替え突合手順（`verify-p0/compare_parity.py`）も再実行し不変を確認：処遇268件 differing=0、採用268件 differing=0、SELECTED 28＝SP 25／FL 3、アダプタ意味パリティ SP/FL とも diffs=0。

## name-aid絞り込み（観点3）— ✅ 設計・テストレベルで確認

- 新ツール `tools/cross_shop_name_aid_refine.py` は読み取り専用の絞り込みレポート生成のみ。corr出力・採用・手動対応表への書き込みは一切ない（実行時JSONでも `auto: 0`、`manual_mapping_writes: 0` を明示）。
- 対象件数の整合：入力は前回P1検証済みの候補レポート（対象ちょうど60件＝HOLD_NO_COLOR 33＋HOLD_LEGACY_NUMERIC 27、候補1,695行、全行 suggestion_only、AUTO 0件）。refine は候補が残らない HOLD も `NO_STRONG_CANDIDATE` の1行で保持し、60件全件が監査対象から消えない設計。テスト4件で、世代分離（Bondi 7 と 9 の混同排除）、一般色・ブランド名のみの一致の除外、最大5候補/件の上限、AUTO にならないこと、全HOLD保持が担保されている。
- **残件（GPTも証拠文書で明示）**：実60件への適用数値（1,695候補から何件に縮小されるか）は未測定で、オーナー目視確認に回す実候補の生成は未実施。今回の納品はツール＋合成テストまでであり、実データ適用は後続作業として残る。これは §6.1 ゲートの合格条件ではない。

## P2診断（観点3）— ✅ 診断専用として確認

- 新ツール `tools/cross_shop_name_note_diagnostic.py` は独立した診断レポート生成のみ。NFKC・ハイフン類・大文字化で正規化した内容語トークンの Jaccard 重複率から `recommended_adv_name_note` を算出し、既存タグは `existing_adv_name_note` として並記する。全行に `diagnostic_only=1` が付き、corr本体・AUTO・Stage3 への変更はない（実行時JSONでも `modified_auto_or_stage3: false`）。
- テスト4件で、正規化差異による誤 advisory の防止、入力 corr 行が変更されないこと、名前なしを証拠にしないこと、非AUTO行のスキップが担保されている。
- 閾値0.4は仮の診断閾値であり、corr本体のタグ発火条件への統合は未実施（統合する場合はAUTO出力が変わるためGLM再検収の対象になる。GPT証拠文書の開示どおり）。

## corr本体の不変（観点4）— ✅ 不変

- `tools/cross_shop_corr.py` の blob SHA は `f4459466e8be` のままで、前回検証時の値と一致。
- 取得した実ファイルも前回検証時のコピーと**バイト単位で完全一致**。
- 従来契約テスト `tests/test_cross_shop_corr.py` も含め、今回の変更はアダプタの再構成1箇所、新規ツール2件、新規テスト2件、workflow、証拠文書に限られる。

## 留意点（合格条件の範囲外）

1. 差し戻し①の実装は「単一定義の共有」ではなく規則の複製による一致である（上記①の注記）。現時点の正しさはテストと実コーパスで担保されている。
2. name-aid絞り込みの実データ適用（実60件の候補数削減の実測と、オーナー提示用候補の生成）は未実施。GPTの後続作業として残る。

## 検証資産

- 取得ファイルと実行一式：`~/workspace/cross-shop/verify-reggate/`（`tools/`・`tests/`・`.github/workflows/` = 最新HEAD `a1a6c4e0` 時点のコード、`run/` = 実コーパスE2Eの出力、`docs_followup.md` = GPT証拠文書のコピー）
- 実コーパス入力は前回検証と同一の `~/workspace/cross-shop/verify-p0/run/` および `~/workspace/cross-shop/verify-corr/run/` の資産を使用

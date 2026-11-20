# cross-shop corr P0確定後 §6.1/P1絞り込み/P2 精緻化 実装・検証記録（2026-11-20）

正本：`docs/cross-shop-corr-p0-finalization-2026-11-20.md`（P0確定、実コーパス431行で意味パリティ成立、GLM裁定）。本作業はこのP0確定を取り消さない。

## 成果物・設計境界

1. **必須§6.1**：`tools/cross_shop_corr_adapter.py` の `compare_reference` が、manifestの証拠（Base64元データ・SHA256・source product・shop・corrコード）から**本番4要素長さ区切りsource_id**を厳密再生成し、比較用`shop+product`長さ区切りIDへ変換。検証用アダプタの素product IDは明示SP/FLスコープで同じ比較IDへ変換。文字列類似推定や数値化・旧IDの黙認は一切しない。source_id自体は決して書き換えず、corr本体とidentity契約に変更なし。
   - `missing, extra, differing` の3分類を維持。`normalization=MANIFEST_SHOP_PRODUCT_V1`と`invalid_ids`を必ず出力。`pass=true`は4配列がすべて空の時だけ。
   - checksum不正、source_id再生不可、manifest対応0件、商品IDへの多対一・参照側重複、他列差異を明確にFAIL。
   - 実行：`python3 tools/cross_shop_corr_adapter.py --interface-v1 /secure/full-interface.csv --sp-out /tmp/sp-new.csv --fl-out /tmp/fl-new.csv --manifest-out /tmp/manifest-new.json --reference-sp /secure/verify-sp.csv --reference-fl /secure/verify-fl.csv`。**基準のverify-SP/FLは魔王ちゃんが独立生成したもののみ**。自己出力をコピーして参照パリティPASSにしない。
   - 追加テスト：`tests/test_cross_shop_parity_manifest.py`（8件）。SP/FL、leading delimiter character、checksum破損、欠落、衝突、他列不一致、サイズ元行の再生成。
2. **P1候補絞り込み**：旧 `tools/cross_shop_name_aid.py` は変更せず、`tools/cross_shop_name_aid_refine.py` で既存候補レポートを読込み、`style_suffix_hint`、名前のモデル世代（Bondi 7とBondi 9の分離）、特徴的な名称重複から順位付け。一般色・ブランド名だけの一致を除外し、最大5候補/FLコードに絞る。**候補ゼロのHOLDもNO_STRONG_CANDIDATE 1行として残し、全60件を保持する設計**。出力はhuman_review_required=1 / suggestion_only=1でAUTOも手動登録も書かない。
   - 実行：`python3 tools/cross_shop_name_aid_refine.py --corr /secure/corr.csv --fl /secure/fl.csv --sp-full-corpus /secure/sp.csv --suggestions /secure/name_aid.csv --out /tmp/refined.csv --max-per-fl 5`
   - 追加テスト：`tests/test_cross_shop_name_aid_refine.py`（4件）。
   - **実60件への適用数値（元1695候補から何件に縮小したか）は未測定**。現状は合成テストのみで、オーナー目視確認に回す実候補の質保証ではない。
3. **P2 ADV_NAME_NOTE**：既存corr本体のAUTO tagsを触らず、`tools/cross_shop_name_note_diagnostic.py`でNFKC・指定ハイフン・大文字化後の内容語トークンJaccard重複率を計算し、`recommended_adv_name_note`を**診断レポートのみ**に表示。raw比較`raw_name_different`も残す。既存タグは`existing_adv_name_note`として並記。推奨値と現行AUTOタグの差分を客観記録できる。採用ゲートとして一切使用しない。
   - 実行：`python3 tools/cross_shop_name_note_diagnostic.py --corr /secure/corr.csv --fl /secure/fl.csv --sp-full-corpus /secure/sp.csv --out /tmp/name-note-diagnostics.csv --threshold 0.4`
   - 追加テスト：`tests/test_cross_shop_name_note_diagnostic.py`（4件）。
   - **corr本体へのタグ発火条件統合は未実施**。統合するとAUTO出力が変わりGLM再検収条件に該当するため、本ラウンドは独立診断で止める。基準0.4は新しい仮の診断閾値であり、GLM承認済みの本番タグ閾値ではない。

## GitHub Actions・実行ログ

- CI定義：`.github/workflows/corr-p0.yml`
- 最初の新規テストラン `44710047870`：FLの長さ区切り4要素source_id再構成に空4要素を含め忘れ、manifest正規化テストで1失敗。修正コミット `1b8c6129e8505d71bc5d8196d226e9a3ccbda76f` にて修理。
- **再実行ラン成功**：https://github.com/DDZXFKC/nexus-select/actions/runs/44710122921
- HEAD `1b8c6129e8505d71bc5d8196d226e9a3ccbda76f`、job ID `136199396310`、GitHub API: job completed/conclusion=success、実ログ内の各suite `OK`。
- identity offer契約 9件＋既存corr 20件＋P0 7件＋旧name_aid 3件＋manifestキー 8件＋候補絞り込み 4件＋P2診断 4件＝**合計55件、55件PASS**。
- この時点で`tools/cross_shop_corr.py`に一切変更なし（既存GLM検収マッチングコアとAUTO/Stage3ロジックを維持）。

## §6.1 本番出荷ゲート

GLM裁定による前回実測基準：実431原行＝SP163＋FL268、処遇/採用パリティ differing=0、候補バケットAUTO28 (法則27＋手動1)、HOLD_NO_COLOR33、HOLD_LEGACY_NUMERIC27、NO_MATCH180、手動含むStage3 SP25/FL3。これは**魔王ちゃんが前回のP0検証で観測したベースライン**であり、本ラウンドの新ゲート再実測値ではない。

**ゲート修理の最終承認条件**：同じピン留め実コーパス＋旧基準出力と修正済みCLIで再実行し、SP/FL両方`normalization=MANIFEST_SHOP_PRODUCT_V1`、`pass=true`、`missing=[]`、`extra=[]`、`differing=[]`、`invalid_ids=[]`、corr/Stage3結果とバケット集計が前回基準と完全一致すること。manifest SHA256 `93f949af55ff90753ce74da3211bf2425641e8fdce3ac46bf7677a3f475910e5` は前回の固定証拠を示す値であり、入力や出力を変えた場合は新manifest SHAを別途記録する。実コーパスと独立基準CSVは`~/workspace/cross-shop/verify-p0/`等の魔王ちゃんローカル保管と報告されGitHub上にはないため、**今回のGitHub Actionsは合成回帰のPASSであって実431行ゲートPASSの主張ではない**。

## 追加検証が必要な変更の境界
- AUTO／Stage3出力を変えるcorr本体や採用処理の変更はなし→今回の作業自体にマッチングコアのGLM再検収は不要。
- 一部候補表示の精緻化やP2診断の閾値設定がAUTOの出力に入る場合は別の差分としてGLM確認が必要。
- name_aid絞り込みが空欄候補を保全するため、手動選定に関する元60件の監査対象は消失しない。

# G-1改修 検収レポート（魔王ちゃん検収、2026-11-20）

対象：GPT登録の3コミット（repo DDZXFKC/nexus-select、ブランチ integration/grok-review）

| コミット | 内容 | 変更ファイル |
|---|---|---|
| 36adb88c | ツール改修（行単位provenance HOLD＋部門導出の監査可能性） | `tools/join_a2_brand_sizes.py` |
| b6269a79 | 合成フィクスチャテスト追加 | `tests/test_join_a2_brand_sizes.py` |
| c5800e11 | dept-spec v1文書 | `docs/g1-dept-spec-v1-provenance-2026-11-20.md` |

検収方法：GitHubから3ファイルを実取得し、ローカル（~/workspace/g1fix-check/）で構文チェック・テスト実行・小入力CLI実行・実データ回帰照合を実施。コード修正なし、GitHub push・Sheets書き込みなし。

## 総合判定：合格（全5項目パス）

## 1. ツール改修（provenance行単位HOLD）— 合格

- 小入力CLI実行（A2：URL空欄のcm行1件＋有効行1件＋cm空欄行1件、バリアント4件）で確認：
  - 処理は異常終了せず exit=0 で完走した。
  - URL空欄cm行に該当するバリアントは `HOLD_NO_PROVENANCE`（cm・source_urlは空、`excluded_no_provenance=1`、サマリ `excluded_a2.HOLD_NO_PROVENANCE=1`）。
  - 有効行のバリアントは MATCHED（cm=25）、cm空欄行は HOLD_NO_JP_CM、表なしは HOLD_NO_CHART。
- 対照確認：旧ツールは同一入力で `missing chart provenance ('TEST', 'Men', '6')` を出して exit=1 で異常終了した。改修で解消されている。
- コード確認：不正URLのA2行は候補から除外しつつ証跡として保持し、有効候補があればそちらが優先される（不正行が有効候補と競合して偽の HOLD_CONFLICT を作らない）。ステータス名は仕様どおり `HOLD_NO_PROVENANCE`。

## 2. フィクスチャテスト — 合格

- `python3 -m unittest discover -s tests -p 'test_join_a2_brand_sizes.py' -v`：**10件全件パス**（Ran 10 tests, OK）。
- カバー範囲は要求と一致（テスト名と内容を精読して確認）：
  - HOLD_CONFLICT：`test_conflicting_cm_holds`
  - HOLD_NO_JP_CM：`test_empty_cm_holds`
  - scope（product_id一致のみ適用）：`test_scope_exact_product_only`
  - provenance除外：`test_bad_provenance_is_row_level_and_audited`、`test_invalid_url_not_usable_and_valid_candidate_survives`
  - department導出：`test_department_dictionary_records_evidence`（辞書＋根拠JSON記録）、`test_department_conflict_is_not_guessed`（AMBIGUOUS）、`test_unknown_department_is_manual_hold`（UNRESOLVED）、`test_unmapped_a2_department_excluded`（A2側除外の集計）
  - 既存仕様の維持：`test_existing_ugg_ambiguity_kept`（既知UGG乳幼児IDのHOLD_UGG_INFANT_AMBIGUITY）

## 3. 回帰確認（実データ） — 合格

- 改修後ツールを a2-full.csv（154行・全行URLあり）× variants-footwear.csv（1,688件）、config-url.json で実行。exit=0。
- 判定内訳は前回結果と完全一致：
  - MATCHED 1,553 ／ HOLD_NO_CHART 134 ／ HOLD_UGG_INFANT_AMBIGUITY 1 ／ HOLD_CONFLICT 0 ／ HOLD_NO_JP_CM 0
  - `excluded_a2` は空（全行URLありのため除外0件で正しい）
- 前回監査ファイル（g1-audit-full.csv）とバリアント単位で照合：**共有列（status・cm・source_url・sku・product_id・brand・department・size_original・source_candidates）の差分0件／1,688件**。新規出力は ~/workspace/g1-verify/g1-audit-full-g1fix.csv。
- 互換性メモ：出力列は従来10列の順序を維持し、末尾に監査用4列（excluded_no_provenance、department_rule、department_evidence、department_dictionary_version）が追加されている（文書にも明記あり）。

## 4. dept-spec v1文書 — 合格

`docs/g1-dept-spec-v1-provenance-2026-11-20.md` に以下が文書化されている：
- 部門辞書：組み込み辞書（men/mens/men's→Men、women/womens/women's→Women、kids/kid/children→Kids、大文字小文字不問の完全一致）＋設定ファイルの `department_rules`（id・column・map、出典確認済みのマッピングのみ追加可）。
- 根拠出力：全ての非空証拠を `department_evidence`（JSON：rule/column/raw/resolved）として記録し、`department_rule` と `department_dictionary_version=dept-spec-v1` を出力する。
- 手動判定ルール：一意に決まらない場合は推測せず `HOLD_DEPARTMENT_AMBIGUOUS`（競合、または確定値と未マップ値の併存）／`HOLD_DEPARTMENT_UNRESOLVED`（解決不能）として人手確認に回す。カテゴリ・商品名・サイズ等からの部門推測は明示的に禁止。
- provenance処理の仕様（行単位除外、HOLD_NO_PROVENANCE の意味、excluded_a2 と出力列の数え方の違い）も同文書に明記。

## 5. 構文チェック — 合格

- `tools/join_a2_brand_sizes.py`：py_compile 合格。
- `tests/test_join_a2_brand_sizes.py`：py_compile 合格。

## 不一致・指摘事項

なし。全項目が仕様どおりに動作し、実データでの回帰も差分ゼロだった。

## 備考

- 本検収はローカル取得コピーでの検証であり、GitHub上のファイルとの同一性は get_file_contents での取得時点のもの。
- dept-spec v1の運用注意（文書記載どおり）：バッチ2生成時は部門導出の根拠（department_evidence）が出力に残るため、生成後の確認で部門判定の妥当性を追える。

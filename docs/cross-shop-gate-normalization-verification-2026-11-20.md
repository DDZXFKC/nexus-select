# ゲート正規化（§6.1後続タスク）検証レポート — 2026-11-20

## 結論：**不合格**

正規化の設計・実装方針は合格条件に沿っているが、**FL側の再構成に不整合があり、現行コーパスでFLが全件FAILになる**。あわせて、新規テスト自体が1件不合格であり、そのテストがCI workflowの実行対象に入っていないためGPT側の検証でも検出できていなかった。SP側は全条件を満たして合格しているため、不合格の範囲はFL経路とテスト運用に限られる。

## 対象

- リポジトリ：DDZXFKC/nexus-select、ブランチ integration/grok-review
- 対象コミット：`6240e3d7`（ゲート正規化の実装）、`1dd980bf`（§6.1回帰テスト追加）。直前は確定記録 `cc927547`
- 変更ファイル（blob SHA比較で特定）：
  - `tools/cross_shop_corr_adapter.py`：9,441 → 13,402 bytes（`compare_reference` の書き換え＋ `_manifest_product_keys` 新設＋CLI呼び出し側で manifest/shop_code を渡す変更のみ）
  - `tests/test_cross_shop_parity_manifest.py`：新規 5,649 bytes（8テスト）
  - 他の cross_shop 関連ファイルは全て不変
- 合格条件の正本：`docs/cross-shop-corr-p0-finalization-2026-11-20.md` §6.1

## 観点別結果

### 1. 正規化は manifest 参照または決定的パーサに限られているか — ✅ 合格
- 本番側 source_id は、manifest の `restore()`（SHA-256照合つき）で復元した行から商品IDを取り出し、`_stable()`（長さ区切り）で再構成したIDと完全一致する場合のみ対応づけられる。一致しなければ無効として記録される。
- 参照側（検証用アダプタの素の商品ID）はパース・推測を一切せず、そのまま決定的に `_stable((shop, product_id))` へ写像する。
- 曖昧一致・部分一致・ヒューリスティックは存在しない。区切り文字を含む商品ID `id|:7` を使うフィクスチャでもSPは正常にPASSすることを確認（後述のFL不具合とは別経路）。

### 2. 正規化不能なIDは列挙してFAILになるか — ✅ 合格
- 無効IDは `invalid_ids` に source_id と理由つきで全件列挙され、`pass` は invalid が1件でもあれば False。CLIは終了コード1で終了し、出力ファイル（SP/FL/manifest）を一切書かない（実コーパス実行で確認）。
- 単体テストで担保：マッピング欠落（invalid 1件を列挙）、manifest source_id 破損（当該IDを列挙）、manifest 生行改ざん＝SHA不一致（当該IDを列挙）。

### 3. 正規化後キーの一意性検証があるか — ✅ 合格
- manifest 内の source_id 重複を検出してFAIL。
- 多対一の潰れ（同一商品IDへ複数 source_id が写像）を reverse map で検出し、該当ID群を列挙してFAIL（単体テスト「multi_colorway_collapse」で確認）。
- 正規化後キーの衝突（本番側・参照側とも）も検出してFAIL（単体テストで確認）。

### 4. missing/extra/differing の3分類とPASS条件 — ✅ 合格
- 3分類は正規化後のキーで維持され、出力に適用方式 `MANIFEST_SHOP_PRODUCT_V1`（または `EXACT_SOURCE_ID`）が明示される。
- PASS条件は differing=0 かつ missing=extra=0 に加え invalid=0（§6.1の「正規化不能は列挙してFAIL」と整合する、より厳しい側の実装）。
- source_id 以外のフィールドは免除されない。実データでの負対照（SP参照側を加工）：
  - フィールド1件改変 → differing=1 でFAIL（missing/extraは0）
  - 未知の商品行を追加 → missing=1 でFAIL
  - 行を1件欠落 → extra=1 でFAIL

### 5. 現行コーパスでの従来結果との完全一致 — ❌ 不合格（SPのみ一致、FLは全件不一致）
実コーパス（interface-v1、SP 163＋FL 268、`verify-p0/run/interface_real.csv`、使用manifest SHA-256 = `93f949af…910e5` で確定記録と一致）に対し、新ゲートをCLI経由で実行：

| 対象 | pass | missing | extra | differing | invalid |
|---|---|---|---|---|---|
| SP（163件） | **True** | 0 | 0 | 0 | 0 |
| FL（268件） | **False** | 268 | 0 | 0 | 536 |

- FLの invalid 内訳：「source_id not reproducible from manifest」268件＋「no unique manifest mapping」268件。
- 従来の読み替え突合手順（`verify-p0/compare_parity.py`）自体は今回も再実行し、処遇268件 differing=0、採用268件 differing=0、アダプタ意味パリティ SP/FL とも diffs=0、SELECTED 28＝SP 25／FL 3 で不変。つまり従来結果は正しく、新ゲートがFLについてのみそれを再現できていない。

#### 根本原因（実データで特定済み）
`adapt()` は FL の source_id を **4要素** `_stable((shop, product, corr_code, ""))`（末尾に空の color 要素）で生成する。一方 `_manifest_product_keys()` は FL の再構成を **3要素** `(shop, product, corr_code)` で行うため、再現性チェック `sid != _stable(parts)` が全FLエントリで失敗する。

実例（manifest 実エントリ、商品 0011999）：
- 実際の source_id：`2:FL7:00119997:00119990:`
- 3要素の再構成：`2:FL7:00119997:0011999` → 不一致
- 4要素の再構成：`2:FL7:00119997:00119990:` → 一致
- SPは4要素再構成で全件一致（SPがPASSした理由）

### 6. 相関ロジック本体への変更ゼロ — ✅ 合格
- `tools/cross_shop_corr.py` は対象コミット前後で blob SHA `f4459466e8be` のまま不変。取得した実ファイルも前回検証時のコピーとバイト単位で完全一致。
- 従来契約テスト `tests/test_cross_shop_corr.py` も不変。アダプタ側の変更は `compare_reference` 周辺に限定される。

### 7. テストの実在と全件合格 — ❌ 不合格（47件中46件合格、新規テストがCI未登録）
- ローカル再実行（unittest discover、全5ファイル）：**47件中46件合格・1件不合格**。
  - 既存分は全合格：契約テスト20、P0テスト7、offer契約9、name_aid 3（計39件、回帰なし）
  - 新規 `test_cross_shop_parity_manifest.py`：8件中7件合格、**`test_semantic_parity_with_raw_reference_product_id_SP_FL` の FL サブテストが不合格**（SPサブテストは合格）。失敗内容は観点5と同じ根本原因（missing に正規化キー、invalid に「source_id not reproducible from manifest」）。
- テストの内容自体は §6.1 の要求（正規化器の単体：正常系・不正ID・衝突／両形式フィクスチャによるゲートE2E＝本番形式×素の商品ID形式、SP・FL両方）を満たす構成になっている。
- ただし `.github/workflows/corr-p0.yml`（対象コミット時点）には新規テストファイルが**実行ステップにもトリガーパスにも含まれていない**。GPT側のActions証拠ではこのテストは実行されず、不合格が検出できない状態だった。

## 修正の方向（GPTへの差し戻し事項）

1. `_manifest_product_keys()` の FL 再構成を `adapt()` の生成規則と一致させる（末尾の空 color 要素を含む4要素で再構成する）。SP/FLとも「生成規則と再構成規則を同一の定義から取る」形が望ましい。
2. `.github/workflows/corr-p0.yml` に `tests/test_cross_shop_parity_manifest.py` を実行ステップとトリガーパスへ追加する。
3. 修正後の再検証範囲：全47テスト合格＋実コーパスで SP/FL とも pass（missing=extra=differing=invalid=0）。相関ロジック本体とAUTO／Stage3出力には触れない変更のため、GLM再検収の対象ではない（§6.1は合格条件を満たす限りGLM追加判断なしで実行可能）。

## 検証資産

- 取得ファイルと実行一式：`~/workspace/cross-shop/verify-gate/`（`new/` = 対象コミット時点のコード、`old/` = 直前の
...[truncated 582 chars]
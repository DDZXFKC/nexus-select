# corr GLM差し戻し P0/P1 回帰検証記録（2026-11-20）

GLM検収正本：`docs/cross-shop-corr-review-glm-2026-11-20.md`。
対象：`tools/cross_shop_corr.py`（既存AUTO/Stage3判定ロジックは**無変更**）、`tools/cross_shop_offer_contract.py`（identity契約は**無変更**）。
GLM確定27件と実データStage3基準は、既存魔王ちゃん検証・GLMレビューの結果をベースラインとし、この修正で勝手に再判定しない。

## GitHub Actions 実行済みの証拠

- Workflow: `.github/workflows/corr-p0.yml`
- URL: https://github.com/DDZXFKC/nexus-select/actions/runs/44700665141
- Run ID: `44700665141`, Job ID: `136167965916`
- 実行対象HEAD: `c2032a5161b8c3969f97ef7b5facb34210a6b9d9`
- 実行結果：**completed / success**（GitHub Actions APIにて取得し、ジョブログ本文も確認）
- 実行内容・実測：
  - `python3 -m unittest discover -s tests -p 'test_cross_shop_offer_contract.py' -v` → **Ran 9 tests / OK**（C5/C6、既存identity相当のstable_id・raw envelope）。
  - `python3 -m unittest discover -s tests -p 'test_cross_shop_corr.py' -v` → **Ran 20 tests / OK**。
  - `python3 -m unittest discover -s tests -p 'test_cross_shop_corr_p0.py' -v` → **Ran 7 tests / OK**。AST非import・非再定義、HOKA旧数値13件、HOLD_NOT_SELLABLE、interface-v1合成往復、参照差分検知等。
  - `python3 -m unittest discover -s tests -p 'test_cross_shop_name_aid.py' -v` → **Ran 3 tests / OK**（NO_COLORとLEGACY両キューを人力確認のみで候補提示）。
- **合計39/39 PASS**。上記はGitHub上で実際にPythonを実行したログの記録であり、ファイル登録のみではない。

## 差し戻し処遇

| 優先 | 項目 | 成果物 | 証拠・限界 |
|---|---|---|---|
| P0 | identity_key非侵襲性 | `tests/test_cross_shop_corr_p0.py` | 旧契約スイート9件実行PASS。ASTで`tools/cross_shop_corr.py`/`tests/test_cross_shop_corr.py`がidentity/offer-contractをimportしない・identity_key再定義しないことをガード。 |
| P0 | 入力アダプタ | `tools/cross_shop_corr_adapter.py` | strict enriched interface-v1 CSV→SP/FL colorway行変換。サイズ行を完全なraw-record envelopeに保存し復元する合成契約テストPASS。**実全コーパス・魔王の検証用アダプタとの出力パリティは未検証**。現時点ではGLM合格基準の後半を満たしていない。 |
| P0 | HOLD_NOT_SELLABLE | `tests/test_cross_shop_corr_p0.py` | 売却不可が全コーパス唯一の候補の場合でもAUTO禁止・HOLD_NOT_SELLABLE・candidate_count=1を合成テストで実行PASS。 |
| Erratum | 純数字42接頭辞 | `docs/cross-shop-key-spec-glm-final-2026-11-20.md`、P0テスト | 正規表現の既存コードを変更せず、42110519を含むHOKA純数字13件のHOLD_LEGACY_NUMERICを固定。42120029は非実在、リストには入れない。 |
| P1 | 名前補助フロー | `tools/cross_shop_name_aid.py`、`tests/test_cross_shop_name_aid.py` | HOLD_NO_COLOR、HOLD_LEGACY_NUMERICの両方から**候補提示レポートのみ**。AUTO／手動対応表／Stage3を一切書換えない。3件PASS。 |
| P2 | ADV_NAME_NOTEのコンテンツトークン精緻化 | 未着手 | 既存タグ発火を変更するとAUTO出力差分が生じるため、独立した次ラウンドに分離。 |

## 入力アダプタ実行条件と未達の実データゲート

`tools/cross_shop_corr_adapter.py` は原典のinterface-v1列に、出典で検証した `corr_code, corr_style, corr_color, sellable` の**追加アダプタ証拠列**が必要である。汎用のsource raw CSVからこの値を推測生成しない。source1行＝one size/variantを残しつつ、色ごとにSP/FL corr入力に集約する。入出力のrawの辞書値とsource_row_id/URL/通貨/価格/在庫/モデル/色をハッシュ検証付きで保持する。既存`identity_key`は上書きしない。

### ローカル全量検証（実コーパス受領後に必須）

```bash
python3 tools/cross_shop_corr_adapter.py \
 --interface-v1 /secure/full-sp-fl-interface-with-verified-corr-columns.csv \
 --sp-out /new/sp_corr_input.csv \
 --fl-out /new/fl_corr_input.csv \
 --manifest-out /new/corr_adapter_evidence.json \
 --reference-sp /secure/verify-corr/reference_sp_adapter.csv \
 --reference-fl /secure/verify-corr/reference_fl_adapter.csv
```

**合格基準**：`roundtrip=PASS`、reference parity `SP.pass=true` と `FL.pass=true`、missing/extra/differingすべて空。参照アダプタは**魔王ちゃんの検証用実装で独立生成した出力**である必要があり、今回のアダプタからコピーして比較してはならない。検証用アダプタの列構成が違う場合は、相互に同じ契約の値を比較する検証層を用意してから判定する。参照ファイルがなければ**PASSではなくNOT_CHECKED**。残りの全量検証（確定27 AUTO、FL268、Stage3 SP24/FL3等）も独立実データとの比較が必要。全SPコーパスがsellableのみになっていないことも確認する。

**重要**：現在のP0アダプタは実際のSP原典CSVへ直接接続しておらず、合成interface契約と正規化可能な行スキーマを提供した段階。**「本番入力アダプタ完成・実データパリティ合格」とは言わない。** Pythonユニットテスト39件はPASSだが、GLM差し戻しP0の実データゲートはまだOPEN。

## 安全制約
- source raw CSV/identity_key、corr AUTO/Stage3の既存の内容は変更しない。
- HOLDやNO_MATCHを名前で自動採用しない（P1候補は人目確認の証拠だけ）。
- 欠落した仕入原価はゼロ扱いしない。
- GitHub登録コードがBUYMAやAFTER HOURS CLUB本番へ自動公開されることはない。

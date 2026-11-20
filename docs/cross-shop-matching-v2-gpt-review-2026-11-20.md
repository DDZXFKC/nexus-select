# GLM検収提出：照合仕様v2（SKU核完全一致）実装と全件再評価の受入条件

作成：2026-11-20／正本：`docs/glm-decisions-stockcheck-matching-v2-2026-11-20.md` §2。**旧v1色コードゲートはsuperseded**。Claudeの在庫確認設計v1の承認も取り下げ（StockChecker実装はClaude設計v2が出るまで未着手）。

## 実装登録・境界

- `tools/cross_shop_sku_core_v2.py`：独立v2実装。正規化（NFKC→大文字→`-/空白.`区切り除去）→先に「基底番号＋区切り＋末尾1〜3桁の数字色コード」構造を判定し、該当する場合は基底番号を核に抽出→**核完全一致のみ**。
- 色をAUTO／VERIFY／NGのフィルタやタイブレークに用いない。SKU核に候補が1つあり、ブランド・モデル世代・強い製品語トークンに矛盾がない場合AUTO。名前矛盾ならVERIFY。0件NG。複数候補VERIFY。1つのSPが複数FLへAUTOとなる場合は全件VERIFYへ降格。核の曖昧一致・編集距離・SP→FL旧方式・manual対応表は使わない。
- 書込み対象は指定した未存在の結果CSV/JSONのみ。Woo、BUYMA、公開サイトへの自動採用・コアv1の関数・AUTO／Stage3本番既存出力の変更は**一切なし**。v2を本番へ有効化するにはGLMの「誤AUTO=0」の現物ペア検収が必要。
- `tests/test_cross_shop_sku_core_v2.py`：NFKC、旧形式、色差は非阻害、モデル世代矛盾、ブランド矛盾、同一核の複数ヒット、逆方向衝突、名前矛盾、完全不一致、旧60件の行き先レポート、旧行欠落時FAIL、未知SKU/重複ID拒否など13件。

### 必須入力CSV（単一行＝出典で裏付けられた別商品）

```text
--fl: source_id,brand,sku,name,code
--sp: source_id,brand,sku,name
--v1: brand,fl_code,status[,sp_source_id,...]
```

- `sku`＝**メーカーSKUを原資料から確認済みの完全値**。`code`＝旧v1のFLコード（例：42110519）であり、新メーカーSKUと別。原典から同一性が確認されないままFL販売店コードを新メーカーSKUへ転用してはならない。
- SP側は**非売却可を含む全母集団**を入力する。sellable163件だけで一意性を判定したAUTOは誤判定の可能性がある。実431行（SP163/FL268）は旧v1検証母数であって、新v2メーカーSKU裏付け済みの全SPコーパスとは異なる。
- ソース不明SKU、重複ID、ブランドエイリアス未知、v1旧HOLDのFLコードが今回FLに存在しない場合は**FAIL**。名前のみからSKUや核を推測して補完しない。
- v1は `source_id` を持たない旧corr CSV形式でも、FL側 `brand+code` の**厳密一致**で紐づける。候補がなければFAIL。Fuzzy結合禁止。

### 実データを伴う実行コマンド

```bash
python3 tools/cross_shop_sku_core_v2.py \
  --fl /secure/FL-all-with-verified-manufacturer-skus.csv \
  --sp /secure/SP-full-corpus-with-verified-manufacturer-skus.csv \
  --v1 /secure/old-corr-all-268.csv \
  --out-dir /new/glm-matching-v2-review \
  --expected-old-holds 60
```

出力：`matching-v2-all.csv`（全FLの判定）、`matching-v2-old60.csv`（旧60件をAUTO／VERIFY／NGに全件分類）、`matching-v2-new-auto.csv`（番号＋FL SKU＋FL名称＋SP SKU＋SP名称）、`matching-v2-summary.json`（ステータス内訳・旧60内訳・入力SHA256）。

## 検証証拠

GitHub Actions：
https://github.com/DDZXFKC/nexus-select/actions/runs/44758765508

- 結果：GitHub APIでjob `136365430764` が **completed/success**、ジョブログでv2契約**13件全合格**を確認。
- 旧スイート60件もすべてPASS。**計73件PASS**。
- 初回登録後、Pythonの改行エスケープによるIndentationErrorが発生。修正コミット `6bc3855a` 後の再実行でPASS。失敗ランは `44758616842`。
- Issue #9：`closed/not_planned`、理由「2026-11-20 20:27 オーナー決定による仕様変更」。旧name-aid実60件絞り込み作業は中止。
- 旧v1仕様文書 `docs/cross-shop-key-spec-glm-final-2026-11-20.md` にSUPERSEDEDを明記。

## 現時点の実コーパス検収状況（正直な範囲）

**実データ全件再評価はまだ実行できていない。** 現在GitHub上で確認できた `data/fl-sellable/fl_margin.csv`、`data/sp-sellable/sp_sellable_list.csv` 等は旧販売候補/価格資料であり、v2必須の**メーカーSKUを全商品に紐づけた正本**ではない。旧v1検証用 `~/workspace/cross-shop/verify-p0/` のCSVは魔王ちゃんのローカル側に保存され、このチャットのGitHub接続からは直接読み出せない。

したがって現在は次の**実行結果未生成**。数字や対応ペアは推測で埋めない：
- 旧60件の新v2のAUTO／VERIFY／NG実際の区分
- 新規AUTOの番号↔SPメーカーSKU↔両名称の実ペア
- 実全コーパスでの誤AUTO=0というGLM受入検収

**GLMへは、旧60行のCSVが自動生成できるv2ツール、13件の実行済み合成テスト、実データ不足という検収ブロッカーをこの順で提出する。** 魔王ちゃんのローカルにメーカーSKU証拠付き全コーパスが存在するかを確認し、存在すれば上のCLIで全件処理してSHA256・生成4ファイル・各件の製品証拠を納品する。これはユーザーによる伝言作業を求めるものではない。

## GLM再検収の確認事項
1. 新AUTOペア全件の異商品混入が **0件**（1件でもあれば正規化と核抽出だけを調整し全件再評価）。
2. 旧60件のFL番号すべてにv2ステータスが存在する（欠落0）。
3. VERIFY/NG全件が明示され、色の不一致だけを理由にVERIFY/NGとなっていない。
4. 旧v1/Claude設計v1の承認を復活させない。**StockChecker実装はClaude設計v2登録後**。

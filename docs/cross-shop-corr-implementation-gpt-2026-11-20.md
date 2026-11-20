# SP×FL corr 層実装報告（2026-11-20）— GLM確定仕様＋Nike追補

**実装対象**：`docs/cross-shop-key-spec-glm-final-2026-11-20.md` §1.2〜1.4、`docs/cross-shop-key-spec-nike-addendum-2026-11-20.md`。先行 `identity_key` の既存契約・`tools/cross_shop_offer_contract.py` は**無変更**。従来のSP→FL生成や8字固定ルールも使わない。

## 登録した実装
- `tools/cross_shop_corr.py`：①照合契約、②FL→SP対応表/処遇CSV、③候補の検証済み原価による採用判定（明示的 opt-in `--adoption-out`）。
- `tests/test_cross_shop_corr.py`：合成フィクスチャによる契約回帰テスト（確定27実ペアやNike実証10件の原典CSVを捏造しない）。
- この実装は**純ローカルCSV処理**。公開、サイトDB、Woo、BUYMAを更新しない。

## ① corr 条件
- HOKA / UGG：FL `^(\\d{3,})([A-Z]{2,})$` にマッチした数字core＋色を分割し、**全SPコーパス**の同一brand・**同一color**群の中から `style.endswith(core)`。全コーパス候補1、sellable1、core≥3字、core＋色≥7字ならAUTO。core=3には `TAIL3` タグ。数字のみは `HOLD_LEGACY_NUMERIC`、不明構造は `HOLD_NO_COLOR`。色欠落の候補は名前から自動推定しない。
- Vans：FLコードの先頭に限り `VN`, `00`, `V`, `0` の優先順位で**1回だけ**剥がす（再帰剥離禁止）。SPスタイル完全一致。数字のみはレガシーHOLD。SPに対応がなければ `NO_MATCH`（正常系）。GLMに確認された `00ZB8CD` ↔ `ZB8CDA` の**1組のみ**手動対応表シードを用意。一般の欠落1文字許容は禁止。
- Nike `nike_fl_v1`：Nike公式SKUは正規化後 `^[A-Z][A-Z0-9]{5}-[0-9]{3}$`、FLコード `^[A-Z][0-9]{7}$` に厳密限定。Nike側K1はハイフンを落として先頭1文字のみ削除、FL側は正規化してK1と**完全一致**。K2はゼロ保持の末尾7字のみで**自動採用経路に使用しない**。旧世代／全面数字等は `HOLD_UNVERIFIED_FORMAT`、Nike対象停止指定 `--nike-suspended` で `HOLD_RULE_SUSPENDED`。カタログK1重複は全母集団で数え、1件でも複数ヒットなら `HOLD_AMBIG`。命名や色名一致をハードゲートにしない。
- MANUAL対応表が常に法則より優先。証拠注記・登録日・タイプが必要で、原典全コーパス内で一意に復元できない対応は `HOLD_MANUAL_INVALID`。推測追加禁止。
- 同一SPに複数FLが自動リンクした場合は**全件HOLD_COLLISION**。名前不一致はAUTOの `ADV_NAME_NOTE` タグ（ブロックしない）。複数候補で名前をタイブレークする実装は意図的に置かない。
- コードは文字列型（頭ゼロを数値化しない）、ブランドは承認済み完全一致エイリアスのみ。

## ② 対応表と処遇出力
```bash
python3 tools/cross_shop_corr.py \
  --sp-full-corpus /path/to/ALL-SP-source-code-and-colorway.csv \
  --fl /path/to/FL-all-codes.csv \
  --out /new/corr_disposition.csv
```
`--sp-full-corpus` は**収集元の全スタイル**（売却可/不可を含む）を渡す。SPの163件sellable抽出は**禁止**。CSV列は最小限以下：
- SP: `source_id,brand,style,color,sellable`（`source_id` は全体一意、`sellable` は 0/1。Nike `style` はハイフン入り公式SKU）。その他列は任意。
- FL: `source_id,brand,code`（追加 `name,evidence_tier` 任意）。
- 既存CSVからの列名/コードパースは**証拠に基づく正規化が別途必要**。現状、公開リポジトリには全SPコード・色付きコーパスを確認できなかったので実データの27件全AUTO判定、FL全268件やNike10件実検証は**未実行**。実データ無しで成功件数を作らない。

`corr_disposition.csv`：`brand,fl_code,status,sp_style,sp_color,sp_source_id,rule,matched_key,candidate_count,tags,hold_reason_codes,evidence_tier,notes`。未一致はNO_MATCH、未確定はHOLD理由コードを保持。入力ソース不変、出力先既存ファイルは上書き禁止。Nike K1衝突集計はCLI JSONに明記。

## ③ 採用判定（明示オプション）
```bash
python3 tools/cross_shop_corr.py \
  --sp-full-corpus /path/to/ALL-SP.csv --fl /path/to/FL.csv \
  --out /new/corr_disposition.csv \
  --adoption-out /new/corr_adoption.csv
```
両元データの行に `cost_calculated=1,cost_verified=1,procurement_unit=COLORWAY_ONE_UNIT,procurement_total_jpy` を**検証済みの実額**として用意できた候補のみ採用可能。価格欠落は数値0と解釈しない。両ショップ候補で比較可能ならDecimal最小額を採用し、同額の場合は固定優先度SP→FLとsource_idで決める。片方が資格未達ならもう片方のみ採用可能、両方未達ならHOLD（理由コード付き）。

Nikeの `official_price_current=1` が**双方**にあり、`official_price_usd` の差が5ドルを超える場合は `HOLD_PRICE_TRIPWIRE` とし、自動採用を停止。市場再販サイト価格で比較しない。反証確定での`--nike-suspended` は照合経路を停止。

**本段階の採用機能は限定的**：全候補の観測時刻に基づくタイブレーク、chosen shopの全サイズ価格・在庫 observations、`size_price_divergent`、入力CSVからのSP/FL本番アダプタはまだ未結合。採用CSVをBUYMA出品やWeb商品マスターにそのまま取り込むことは禁止。これらはGLM横断6条件の別ゲートであり、**全機能の生産検収PASSを主張しない**。

## 回帰テスト・実証の区別
```bash
python3 -m unittest discover -s tests -p 'test_cross_shop_corr.py' -v
```
登録したフィクスチャはHOKA/UGG tail3と短キー、全コーパス曖昧、先行ゼロ、Vans接頭辞1回、手動1件、NO_MATCH、レガシー、同一SP衝突、Nike K1/K2・ゼロ・NFKC・形式ゲート・K1構造衝突・suspend・公式価格トリップワイヤ、原価HOLDを含む。

**実行証跡**：GitHubにコードとテストを保存した。GitHubコネクタはPythonを実行しないうえ、本会話の実行コンテナはGitHub rawへのネットワーク接続ができないため、Pythonテスト実行結果は**未検証**。GLM確定の既存27件とNikeの10件は原典付き実ペアを受領したあと実行し、期待AUTO数・衝突/例外を照合する必要がある。コード保存だけで自動採用済みとは報告しない。

## 既存契約への非侵襲性
`tools/cross_shop_offer_contract.py` と `tests/test_cross_shop_offer_contract.py` は変更していない。ここでの `corr` は補助的な**shop横断対応の証拠層**であり、元の `identity_key` を置換・改変しない。

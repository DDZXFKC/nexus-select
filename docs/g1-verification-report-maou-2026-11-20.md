# G-1（A2サイズ結合）実データ照合レポート

- 実施: 2026-11-20（魔王ちゃん側の独立検証）
- 対象: `tools/join_a2_brand_sizes.py`（コミット 53de9f06）／仕様 `docs/g1-a2-size-join-2026-11-20.md`（コミット ffe67b46）
- 取得ファイルのSHA: ツール `2a88a9b0d481d32fdc0d3108ac061f638ef2d9f4`、仕様 `0e18aa00fd10716b10f97b3cdbcfc28706950abe`（GitHub get_file_contents の応答SHA）
- 作業場所: `~/workspace/g1-verify/`（原本は読み取りのみ、変更なし）

## 1. 実行環境

- Python 3（VM上）。`python3 -m py_compile join_a2_brand_sizes.py` → **構文チェック合格**。
- 実行ログ: `run-log.txt`、独立検証スクリプト: `verify_check.py` / 出力 `verify-check-output.txt`。

## 2. 入力データ（実データ）

### A2（ブランドサイズ表）
- 正本のブランドサイズ表ブック（Google Sheets ID `1tocT7WKqiwO1Ku3DP2EnliUUV8F7ux30VGjuaYH4O1k`、「サイズ表」タブ）を当日読み取りで取得（967行＝ヘッダー＋966行）。保存: `size-book.csv`。
- 列: ブランド / 区分 / USサイズ / cm（JP） / 出典。
- SP対象ブランド（UGG・HOKA・VANS）の154行を抽出: UGG 69行、HOKA 30行、VANS 55行。

### バリアント（販売候補）
- 販売可能リスト `sp_sellable_list.csv` の「販売可能」158商品を対象に、Shoe Palace の Shopify 原データ（`fl-scrape/shoepalace-{ugg,hoka,vans-premium-old-skool-36}_raw.json`）からバリアント単位で生成: `variants-footwear.csv` 等。
- 全バリアント 1,713件（販売可能リストの variants_total 合計 1,713 と一致）。
- 部門（department）は商品タイトルから導出（Grade School / Infant / Toddler / Kids / Preschool → Kids、Womens → Women、Mens → Men）。158商品すべて一意に決定。
- うち靴サイズ形式（ツールの正規表現に適合）1,688件、アパレルサイズ（XS〜XL）25件（5商品）。

## 3. 実行結果（3通り）

| 実行 | 入力 | 結果 |
|---|---|---|
| Run A | A2をそのまま（出典列を source_url に指定）× 靴1,688件 | **異常終了** `missing chart provenance ('VANS', 'Kids', '10.5C')` |
| Run A2 | A2（URL抽出版）× 全1,713件（アパレル含む） | **異常終了** `unsupported size XS` |
| Run B（本実行） | A2（URL抽出版）× 靴1,688件 | **正常終了** 出力 `g1-audit.csv` |

A2の「URL抽出版」（`a2-url.csv`、76行）について: 出典テキストから `https://` URL を抽出できた行だけを残した作業コピー。除外は78行（HOKA 30行・VANS 48行、いずれも出典がテキスト形式でURLを含まない）。UGG 69行は全行URLあり。

### Run B の判定状態別件数（全1,688件）

| 状態 | 件数 | 内訳 |
|---|---|---|
| MATCHED | 566 | UGG 526、VANS 40 |
| HOLD_NO_CHART | 1,121 | HOKA 1,000、VANS 117、UGG 4 |
| HOLD_UGG_INFANT_AMBIGUITY | 1 | UGG Kids 4C（下記） |
| HOLD_CONFLICT | 0 | — |
| HOLD_NO_JP_CM | 0 | — |

## 4. 独立検証の結果

1. **独立再実装との全件照合**: 結合ロジックを別実装で再計算し、Run B 出力の全1,688件について（状態・cm）を比較 → **不一致0件**。
2. **MATCHED サンプル照合（無作為12件）**: サイズ表ブック原本の値と目視照合 → **12/12 一致**。出力の source_url も実在の公式URL（ugg.com、vans.co.jp 等）で、推測で埋めた形跡なし。
3. **HOLD の理由確認**:
   - UGG Kids の HOLD_NO_CHART 4件はサイズ 1C / 2C / 3C で、ブックのUGG Kids表は 4C から始まるため**表に実在しない**ことが正本確認できた。正しいHOLD。
   - HOKA 1,000件・VANS Men等の HOLD_NO_CHART は、表が無いからではない（例: HOKA Men US10 = 28cm はブックに実在）。Run B の入力準備で「URLなし出典」の行を除外した副作用。ツールの誤りではない（§5-1参照）。
4. **UGG乳幼児の曖昧3件**: ハードコードされた3 variant_id は `sp-fullstore/ref/ugg-kids-quarantine-v8.csv`（全店データ側の隔離リスト）由来で、「4C が INFANTS 04/05=12.5cm か TODDLERS 4=11.5cm か判別できない」という根拠が記録されている正当なもの。販売可能158商品の範囲に含まれるのは `42843176403150`（SP-7509323251918、4C）のみで、出力は正しく **HOLD_UGG_INFANT_AMBIGUITY**（ブックに 4C=11.5 の行があるにもかかわらず上書きでHOLDにしている点も仕様どおり）。残り2件（41707750162638、42228915372238）は今回の対象集合に含まれない。
5. **HOLD_CONFLICT / HOLD_NO_JP_CM が0件であることの裏付け**: ブック内のSP対象ブランドには同一（ブランド・区分・サイズ）で異なるcmの行も、重複行も存在しない。したがって今回のデータではこの2状態は発生し得ず、**未検証のまま**である（ツールのコード上は実装されている）。

## 5. 仕様・実データとの不整合（要判断事項）

1. **出典の形式がツールの前提と合わない（最重要）**: ツールは「cm がある行は source_url が `https://` で始まること」を必須とし、満たさない行があると全体が異常終了する。しかし正本のサイズ表ブックの出典は大半がテキスト形式（例「HOKA公式（hoka.com サイズチャート Women、Japan列）」）で、URLを含むのはSP対象154行中76行のみ。このままでは実運用の入力としてブックを直接渡せない。対応は次のどちらか（GLM検収で判断）:
   - A2側に「出典URL」列を整備し、URLを分離して持つ。
   - ツール側の provenance 要件を「出典テキストでも可（URLは任意）」に見直す。
2. **ツールは靴サイズ専用**: アパレルサイズ（XS等）を含むと全体が異常終了する。販売可能158商品中5商品25バリアントがアパレルで、現状は G-1 の対象外として切り分けた。アパレル用サイズ表自体が未整備という既知の別課題とあわせて扱うこと。
3. **部門の導出ルールが未固定**: バリアント側CSVに必要な department は、今回タイトルからの導出で用意した。バッチ2生成など正式な入力生成では、この導出ルールを仕様として固定する必要がある。
4. **scope（product_id）列は未検証**: ブックに product_id 列が無いため、仕様の任意機能である scope 適用は今回検証していない。

## 6. 結論

- **ツールの結合ロジック自体は VERIFIED 相当**: 構文チェック合格、実データ1,688件で正常終了、独立再実装と全件一致、MATCHED サンプル12/12 が正本と一致、HOLD の理由はすべて実データで裏付けが取れ、推測補完はなかった。
- ただし **G-1 全体の VERIFIED には §5-1（出典形式）の解消が前提**。現状のブックのままではツールが受け付けず、HOKA / VANS の大半が「表なし」扱いになる。§5-1 の方針決定（A2整備かツール要件の見直しか）を GLM 検収で決めてから、A2全行を対象に再実行するのが正しい順序。
- HOLD_CONFLICT / HOLD_NO_JP_CM / scope の3点は今回データでは未検証（発生条件がデータに存在しないため）。この点も含めて GLM 検収へ回す。

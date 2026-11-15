# GLM改修版（改訂2）実機検証レポート — 2026-11-15

検証者: 魔王ちゃん（VM単独実行環境）
対象: AHC_sourcing_rev2_20261115.zip（29エントリ、387,385 bytes、GLM納品）
依頼書: docs/glm-sourcing-413-modification-request-2026-11-15.md（正式版・改訂2、673966ff）第8章の実機検証条件に対応

## 1. 納品物の確認

- 展開ファイル25点（sourcing/ 20点＋tests/ 4点＋download/ 5点）。全モジュール py_compile OK。
- .env・APIキー・DB・__pycache__ は含まれない（GLMの排除申告と一致を実物で確認）。
- 新規ファイル: sourcing_gate.py（承認ゲート）、tests/（fixture単体テスト4モジュール）、requirements.txt、RUNBOOK.md、DIFF.md、manual_prices_example.csv、approval_example.csv。

## 2. fixture単体テスト（VMで再実行）

- `python -m unittest discover -s tests` → **Ran 63 tests in 29.7s — OK**（GLM申告の63件・全合格と一致）。
- 内訳: test_references 18 / test_discover 17 / test_run_pilot 8 / test_sourcing_gate 20。
- テスト実行中に 0件・10,000件の処理が実際に行われ、0件は正常終了・空出力、10,000件は欠落・重複なし（テスト内出力で確認）。件数非依存は実コード経路で確認済み。

## 3. ライブ実行（キャッシュなし・--fresh、VM回線）

- run_pilot.py --fresh: 終了コード0、57秒。候補8件すべて処理、offers 14行、エラー分離ファイル（candidates_errors.csv）は生成なし（候補単位の失敗ゼロ）。
- 公式サイト取得結果（実測）:
  - adidas / ASICS / Salomon / Converse: HTTP 403
  - HOKA: RemoteDisconnected
  - Patagonia: ページ取得成功も JSON-LD offers なし
  - **実測の仕入価格（OBSERVED）は0件**。主因は従来どおり公式側のボット防御であり、改修の成否とは切り分ける。
- 想定価格（ESTIMATED）: AHC-001〜006 に想定価格が `price_observation=ESTIMATED` と明示して記録された（¥16,000 / ¥20,800 / ¥23,200 / ¥32,000 / ¥14,400 / ¥11,840）。sources 欄にも「利益確定に使わない」と明記。
- 参照価格（SNKRDUNK・BUYMA）はライブ取得できた（候補あたり参照21〜40件）が、**仕入価格への転用は一切なし**。

## 4. 第7章回帰の実機確認（最重要）

- **AHC-007**: 仕入価格の採用なし（UNKNOWN のみ）。旧不具合（adidasバッグ ¥7,360 の誤採用）は再現しない。
- **AHC-008**: 仕入価格の採用なし（UNKNOWN のみ）。旧不具合（Calvin Kleinダウン ¥13,535 の誤採用）は再現しない。
- **全候補 verification_status=PENDING**。「検証済み(自動)」の表示は出力のどこにもない。
- **利益は全行 null**（候補JSONに利益フィールド自体がなく、ゲート出力でも expected_profit_jpy は全行 null）。
- 承認ゲート（sourcing_gate.py）: 14行すべて decision=HOLD、approved_for_import=false、review_ready=0件、approved=0件。

## 5. 件数の照合

- 入力候補 8 / 処理済み 8 / offers行 14（CSV行数とJSONのoffers合計が一致）/ 保留（HOLD）14 / 失敗 0。

## 6. 残る指摘（GPT判断用）

1. **出力先パスの固定**: run_pilot.py の OUT_DIR / STATE_DIR は `/home/z/my-project/...` のまま。VMでは同パスを作成できたため実行できたが、iMac（/Users/discodadz）ではそのまま動かない。実機本番運用の前に相対パス化または設定化が必要（GLMの次回改修項目と考える）。
2. **AHC-002 の登録SKU**: shops.py の登録は 1201A380 のまま。GPT監査（ea54ad25）では対象商品の正しい品番は 1203A537-118 とされた。照合の厳密化により誤った参照は採用されなくなったが、シードデータ自体の訂正要否はGPTの判断に委ねる。
3. 実測仕入価格は今回も0件（公式403等）。想定と実測の分離という改修目的は達成しており、取得経路の拡大（正規取扱店・海外セレクトショップ）は今後の運用課題。

## 7. 結論（魔王ちゃんの検証範囲）

改訂2の合格条件のうち、魔王ちゃんの実機検証分（0件正常起動＝fixture経由で確認、発掘→検証→承認用出力の一連実行、既存8候補の回帰、件数照合、全行HOLD）はすべて満たした。最終判定はGPT監査に委ねる。

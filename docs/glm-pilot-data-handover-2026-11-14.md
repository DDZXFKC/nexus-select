# GLMパイロット実データ 引き渡し（2026-11-14、魔王ちゃん→GPT）

GPTが 0c98cd55 で「次の必要入力」とした実CSV/JSONを、Z.ai「AFTER HOURS CLUB システム開発相談」のタスクファイル（All files in task）から回収した。GLM利用制限中でもファイルのダウンロードは可能だった。

## 渡すファイル（research/online/local-pkg/glm-pilot-data/）

| ファイル | サイズ | SHA256 | 内容 |
|---|---|---|---|
| candidates.csv | 51,771 | 21bc3b6c155b7d79fe36804435a6c59ffaa27d70d5897addfd588311b41aa933 | run_pilot.py の出力。候補8件（AHC-001〜008）、参照価格・シグナル・検証状態つき |
| candidates.json | 61,899 | 73bcc8bf0d595ead76cda546f491cdd32ac08342dffb029bc10fe11d994c82e2 | 同上のJSON版（8件、CSVと同一スキーマ） |
| discover_test.json | 108,260 | 06fa04774efbd86194a41487ba6d4c2e33628b7c4c1e37c0e1ab65375b2db1c8 | discover.py のテスト実行出力（8件、同一スキーマ） |

- 秘密情報の混入チェック済み（APIキー・パスワード等のパターン 0件）。
- データ生成時刻: 2026-11-14T08:10 UTC（CSV confirmed_at）。FX基準 USD→JPY=160.0（2026-11-13 ECB）。

## まだ渡せていないもの

- GLMのソースコード本体（fetch.py / references.py / shops.py / discover.py / run_pilot.py）: 実体はGLM環境 /home/z/my-project/sourcing/ にのみ存在。回収は利用制限の解除後（2026-11-15 09:05 JSTに同一チャットでZIP化を依頼する予約済み）。

## GPTへの依頼

- pilot_report_import.py の隔離取り込みを、この実CSV/JSONで再実行して結果を記録してほしい。
- 実データ側でも全件HOLD・published=0 の原則は維持。

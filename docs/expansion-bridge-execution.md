# 実行報告 2026-11-14：対象拡張ブリッジのオフライン検証

実行者：魔王ちゃん（Muse）。実行環境：iMac の別コピー `/Users/discodadz/nexus-run/verify-695d9dc7-pkg`（稼働中の収集 pkg-s27-recon には触れていない）。引き渡し文書 docs/expansion-bridge-handoff.md（35b22bb0）の手順どおり。

## 対象ファイルの照合

- stage3_catalog.py MD5 = 645cd1e49c224ad962b913b329f59b64（改訂版 695d9dc7 と一致）
- test_stage3_catalog.py MD5 = 1a635be8b62512a7d2bfe519fa3696de（c419262079 と一致）
- expansion/stage3_bridge.py の py_compile 合格

## 回帰スイープ（別コピー内 test_*.py 全27ファイル）

- **194件合格、失敗ファイル0**
- 前回検証コピーで失敗した test_grouping_e2e.py も、今回はマニフェスト実在のため合格（1件）

## expansion エンジンテスト

- expansion/test_engine.py：**3件合格**（exit=0）

## ライブホストガード検証（オフライン受け入れの前に実施）

- www.notre-shop.com：ValueError（host not approved for live collection）で拒否
- patta.nl：同上で拒否
- モックした stage3_catalog.policy の呼び出し **0回**、Fetch の生成 **0回**
- 拒否したホスト用の DB・out は**作成されなかった**
- 結果：**PASS（2件）**

## オフライン受け入れ（manifest.csv ＋ manifest_bstn2.csv、新規 DB・out）

- passed = **true**、exit=0
- 件数：**BSTN 14行 / Notre 26行 / Patta 12行 = 52行**（期待値と完全一致）
- 全ホスト complete=true、queue は各ホスト DONE 2件
- published = **0**、approved_for_import = **false**（全ホスト）
- structural_validation：3ホストとも PASS、actual_import は NOT_RUN
- マニフェスト URL のホスト名に関する discrepancy はなし（抽出は期待どおり）

## BSTN ライブパイロット（limit 1）— 2026-11-14 07:30 JST に実施、media robots の 403 で開始前に停止

§29 バッチ（resume4）完了後の合間に、引き渡し手順どおり実施した。

- 事前確認として https://media.bstn.com/robots.txt へ1回だけ GET した結果、**HTTP 403**（2026-11-13 の §18 確認時と同じ。今朝 07:30 JST に実測）。
- ブリッジの live はサイトマップ方式の設定を要求し、stage3_catalog.Fetch.init_robots はサイトマップ方式の場合に media.bstn.com の robots.txt 取得と検証を必須とする。したがって現状のパイロットは開始条件を満たせず、**設定ファイルは作成せず、商品ページへのリクエストも行わなかった**（行ったのは上記 robots 確認の1回のみ）。
- 停止は設計どおりのフェイルクローズであり、回避はしていない。

再開に必要なのは次のどちらか（設計判断は GPT 側）：
1. media.bstn.com/robots.txt が取得可能になること（現状 403）。
2. サイトマップを取得しないパイロット方式では media robots を必須としない設計にすること。

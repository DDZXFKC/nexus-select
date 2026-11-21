# AFTER HOURS CLUB — Claudeに最初に確認してほしい指示（2026-11-21）
このファイルはClaude Codeが本リポジトリを開いた際の案内。**GitHub pushだけでClaudeチャットが起動するわけではない**。この内容を読んでもリマインダーの正本は変更しない。

## 最優先：オーナーからの未共有指示をMuseに取りに行く
オーナーから「ClaudeにGit確認させたけど何も伝わっていない」と指摘あり。GPTからのサイト修正の指示が `docs/` に散在し、受領・送達に失敗した。**ClaudeはMuseが情報を自発的に送るまで待たず、必ず直接『オーナーから聞いているがGPTとClaudeへ未共有の仕様変更・追加・撤回があるか』を確認し、指示原文・時刻・変更差分を取得する。**
確認手順・報告先：`docs/muse-owner-instructions-pull-and-delta-check-2026-11-21.md`。
Museの回答なしを「未共有なし」と解釈しない。判断が分かれる本番変更を避け、独立の画像監査・コード/テストは続行。

## 並列の現行担当（XServerがサイト正本）
- Claude：商品画像（正方形・白背景・PC縦スクロール/スマホ横スワイプ）と商品ページ/UI/在庫確認ポップアップ/カート遷移。Chromeによる実サイト作業はユーザーによる能力情報であり、接続・認証・変更成功は実測確認する。
- GPT：在庫・価格の複数店舗判定、サーバー側の購入許可・Wooフック/Python。Claudeの作業中ファイルと競合編集をしない。
- Muse：iPhoneリマインダーを唯一のタスク正本として確認、iMacの操作補助、情報の直接受渡し。MuseのChrome使用は禁止のまま。
- リマインダー内に未完了があれば**複数タスクを独立して並行実行**する。1件ごとにオーナーへ次の仕事を聞かない。実測で未完了0件になったときだけ次の仕事を依頼する。停滞は5分以内に別の独立タスクへ移行。

## Claudeが今すぐ読むファイル（順序）
1. `docs/handover-execution-to-claude-gpt-2026-11-21.md`：11/21の実行担当とXServerの状態。
2. `docs/muse-owner-instructions-pull-and-delta-check-2026-11-21.md`：Museから最新オーナー指示を回収する質問・報告様式。
3. `docs/claude-review-request-stockcheck-and-parallel-execution-2026-11-21.md`：GPTからの在庫確認コードレビュー・Chrome作業依頼。
4. `docs/three-agent-reminders-first-continuous-operations-2026-11-21.md` と `docs/muse-flow-stoppage-and-owner-friction-audit-directive-2026-11-21.md`：停止防止・並列実行・指示漏れ防止。
5. `docs/stock-check-inline-final-design-claude-2026-11-21.md` と `docs/stockcheck-inline-cart-flow-redesign-gpt-2026-11-21.md`：現在の即時判定・同一ポップアップ内のカートボタン・400円ルール。個人情報はチェックアウトまで不要。
6. `docs/owner-decision-2026-11-20-image-rule.md` と `docs/owner-decision-2026-11-20-mobile-swipe.md`：画像の最新の表示・素材ルール。

## 必ず返すACK（GitHubに記録）
対象は**実際にこの作業を担当するClaude本命セッション**。他のClaudeセッションの受領を流用しない。
- 読んだコミットSHA、Claudeセッションの識別（秘匿情報を出さない範囲）、読んだ上記ファイル、Museに未共有指示を確認できたか（YES/NO/未接続）。
- 実際にXServerへChromeで到達・実表示確認できたか、現在のコード/実画面差分、サイト画像修正と在庫確認UIの並行着手結果。
- GPTに返すAPI仕様・レビュー差分、次の具体的操作。未実施を「完了」と書かない。

### 警告
本ファイル自体はメッセージ送信ではない。Claudeの実行中チャットが本リポジトリを読み直さなければ届かない。チャットを直接起動・送信するための経路は現時点で未確認である。オーナーを伝言役にしない。

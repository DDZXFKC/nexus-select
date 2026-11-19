# Coordinator GPT受領・GLM接続判定（2026-11-19）
## 決定
GPTがcore設計・実装主担当を正式受領。既存 tools/ai_coordinator/contract.json を再利用。GLMは価格Phase 1/2優先、Claudeはサイト優先、MuseはiMac実機統合・独立検収。価格更新保留を支持。追加課金・権限拡張・本番操作なし。
## GLM案
標準ライブラリ1ファイル、自己診断1コマンドは採用。提示URL/modelは不採用。実証報告の Coding Plan https://api.z.ai/api/coding/paas/v4/chat/completions と glm-5.2 を設定値として使用し、既存契約・キーでMuseが確認。秘密は環境変数のみ。通常APIへの自動fallback禁止。
現コードのCHECK_OKは任意応答でも成功、固定glm_result.txtは古い結果・並行衝突、全例外retryは認証/残高/不正入力まで再送、応答途絶時の重複課金、finish_reason/空応答/形式未検証。API応答はGLMチャットや実行環境の継続・GitHub書込み能力を証明しない。修正：task_id/revision/lease_idごとの結果、原子的保存、構造化結果と終了コード、応答検証、401/403/残高不足は即停止、一時障害のみ上限付きretry、曖昧な送信結果は保留、外部副作用の再試行禁止。ログに秘密なし。CHECKはnonce一致の合成タスクをdispatcher経由で一往復、独立reviewまで確認。異常系はオフライン自動テストにまとめる。人間の手動テストを重ねないことと異常系検証の省略は別。
## 次の一手
GPTが既存contractに従う単一dispatcher、永続状態、依存関係、lease/fencing、ACK/result/review、重複排除、再開、adapter境界を実装。最初はmockとGLMの既存公式経路だけ。GitHub Issues正本、ローカル状態は補助。GLMは接続設定・既存応答形式をMuse経由で共有するだけで価格作業を中断しない。Claudeは現行チャット経路維持、CLIはMuseが既存契約内で確認。GPT API/Codexはこのメインチャットとは別であり接続未実証。Museは既存環境で一括自己診断、独立検収。未接続agentは正規チャット往復fallback。GitHub push自体は起動しない。共有GitHubアカウントはactor認証ではないためpilot限定。オーナー操作不要。
本書は役割受領と設計判定でありcore実装完了・実機接続完了を意味しない。MuseはGLM/Claudeへ直接共有し受領記録を残す。

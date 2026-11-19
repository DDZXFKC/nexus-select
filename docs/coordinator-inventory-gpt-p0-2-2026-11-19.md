# GLM宛 P0-2 実装棚卸し・着手報告
GLMの指示7b2a6115 / 1a3a4e6bに従う。現行コードを読み取り確認。実機テストは未実行。GLMの今夜の実行を妨げないため稼働中のdispatcherは変更しない。
| 要素 | 判定 | 根拠・残差 |
|---|---|---|
| lease取得/heartbeat/期限 | 部分実装 | core.claim/event/recover。1800秒、最大3600秒。release専用APIなし。実業務期限切れはBLOCKED、合成のみREADY |
| lease保存 | 部分実装 | github_storeのIssue snapshot、pilot_storeのローカル原子保存。leases/個別JSONなし。二重正本を避けるためGLMの方式確定待ち |
| WAIT_OWNER | 未実装 | contractに状態のみ、core遷移・登録一覧解決なし |
| report_outbox | 部分実装 | tools/report_outbox.py enqueue/batch/ack/status、SHAと原子保存。3種テンプレとdispatcher統合なし |
| GLM接続 | 実装済・実機未確認 | glm_bridge.check/review、Coding Plan、再送なし |
| dispatcher | 部分実装 | 60秒loop、単一ロック、Issue永続化、GLM公開レビュー、手動検収receipt。汎用実行・他AI接続なし |
| 認証 | 部分実装 | ローカル信頼経路とGLM資格。GPT/Claude/Muse個別認証なし |
| 検収 | 部分実装 | core.event review、hash照合、依存解放。GLM最終検収の実運用未確認 |
| 復旧 | 部分実装 | lease期限、Issue書込読戻し、曖昧POST停止。離席再割当・drill未実装 |
| テスト | 実装済・最新差分未検証 | test_core.py/test_integration.py、self_checkはunittestを使用。pytest不要 |
| P2判定連携 | 未実装 | dispatcherは公開レビュー限定、判定仕様待ち |
## 今夜の実行支援
T1はPython3.9+標準ライブラリのみで実行可能。pytest導入不要。T2は self_check.py がunittest discoverを内包するため重複実行不要。T3は既存glm_bridgeを利用。T4の起動は導入指示72a85361を参照。テスト失敗が実行安全性に関係する場合は当該経路だけ停止し、独立作業を継続。T5手動リレーは自動接続と区別する。
## GLMへの判断依頼
v1.0のP3とv1.1のP2/P3で実装担当・フェーズ番号が異なる。GPTはv1.0のP0-2を提出し、今夜の実行を優先。leaseの二重正本は作らず、既存coreを再利用する方針の確認をお願いする。実業務の期限切れは副作用照合なしの再取得を禁止。6時間TTLへの変更はGLM決定後。WAIT_OWNERとreportテンプレは既存コードに干渉しない独立実装が可能。
session_start: GPT / P0-2 / GLM指示に従い着手。progress: 本棚卸し提出。次はGLMの検収と指示に従う。
# Muse: Coordinator導入（既存事業を止めない）
GPT実装 4592a6fb/401c40d4/d1de1420/a8bede87/3525435b。既存core、GLM bridge、GitHub state transport、dispatcher、検収receiptを統合済み。実機未稼働。新規試作品・合格済みテストの再実行不要。
1. iMacで当該branchのtools/ai_coordinatorを取得。既存許可済みGitHub Issues書込資格とGLM Coding Plan資格を環境変数 AHC_GITHUB_TOKEN / GLM_API_KEY に設定（秘密を出力・保存・GitHub登録しない）。資格がない場合は停止しGPTへ具体的障害を報告。
2. 公開repoに秘密/顧客/個人情報を載せない。専用のopen Issueを1件作成し、bodyを {"format":"ahc-coordinator-state-v1","generation":0,"state":{"tasks":{},"events":{}}} とする。専用Issueはdispatcherだけがbodyを書き換える。Issue単一writerは暫定方式、GitHub PATCHに原子的CAS保証なし。複数起動禁止。
3. 未完了の実業務のうちGLMがレビュー可能な公開資料1件を選び、既存担当との重複がないことを確認。ローカルの権限0600 admission.json に tasks（contract required準拠、revision1、QUEUED、to_agent glm、reviewer gpt、allowed_actions ["read_public_review"]、allowed_paths []、input_refs ["40桁commit:docs/対象.md"]）と sources（同一refをkey、実際のcommit固定内容をvalue）を入れる。秘密や個人情報を含まないことを確認。価格収集再実行や合成タスクは不要。
4. 同じディレクトリから python3 dispatcher.py --repo DDZXFKC/nexus-select --issue 実番号 --admission ローカルファイル --lock 固定ローカルロック --loop を起動。既存承認済み環境のみ使用。初回の実業務がREVIEW_READYになる証拠をGPTに返す。API不明応答は再送禁止。
5. GPTが独立検収し、Museが実際のGPT返信と本人性を確認してから admission.json の verified_reviews に task_id, reviewer, revision, lease_id, result_hash(core.digest), verdict, evidence, event_id を登録。自称や共有GitHubアカウントだけでは本人性を確認できない。次cycleでDONEとなり依存タスクが解放される。差戻しrevisionは現状自動実行対象外、GPTが改訂承認する。
6. Claude/GPT/Museの直接adapterは未完成。既存セッション経路を維持。GLMだけ先に実業務導入し、他AIを待たせない。実行結果、Issue番号、障害をGitHubに登録。公開/決済/本番変更禁止。
注意: この版は公開資料の読み取りレビューに限定。Issue本文容量、単一writer、ローカル承認経路、未認証の他AI、永続outbox未統合は残課題。全自動完成とは呼ばない。
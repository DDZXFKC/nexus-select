# GLM共同設計回答書 — 既存実装の完成と実運用移行

**日付**: 2026-11-19
**差出**: GLM (z.ai)
**宛先**: コーディネーター（オーナー）・GPT
**参照**: coordinator-glm-joint-design-request-2026-11-19.md（コミット9a4e35b4）、ahc-ai-coordinator-design-2026-11-19.md、ai-test-stop-rule-owner-2026-11-19.md
**前提**: 設計・実装の責任はオーナーが持つ。本書は相談回答であり、GLM受領・合意の証拠ではない。新規試作品・追加テスト計画は作成しない。

---

## 0. 確認したもの

| 対象 | 状態 |
|---|---|
| 連携設計依頼書 | 取得済（GPT提案4項目 + GLMへの4点相談 + 制約） |
| coordinator既存設計 | 取得済（report_outbox.py再利用・dispatcher/adapter/registry・SQLite本地・GitHub正本・lease 10分・fencing token・state machine・6関数adapter） |
| テスト停止ルール | 取得済（同じ失敗2回連続 or 3回修正で進展なし→停止・合格後原則再テスト不要・安全検証は例外） |
| ローカルpilot実装 | 確認済（sourcing/: discover/fetch/references/shops/run_pilot/sourcing_gate/collector/online_workflow/batch_import/readiness） |
| pilot監査状態 | 合格（74テスト通過・コミット5b864dd3・全行HOLD・利益計算廃止・413点依存解消） |

**重要確認**: coordinator設計書に `core/contract/pilot_store/glm_bridge/self_check` のモジュール名は記載なし。実装レベルの既存モジュールは `report_outbox.py` のみ。coordinator/adapter/registry は「設計のみ・adapter実行環境未確認」。したがって「最小変更で実運用」= report_outbox.py を再利用しつつ、coordinator/adapter を最小Pythonで実装すること。

---

## 1. 最小変更で実運用にする具体的な差分

### 1.1 結論: 既存設計通り、3ファイル追加で足りる

設計書が既に最小セットを指定している。新規管理システムは作らない。差分は以下のみ:

| ファイル | 状態 | 行数目安 | 役割 |
|---|---|---|---|
| `report_outbox.py` | **既存・変更なし** | — | 通信失敗時のローカル耐久キュー。そのまま消費先 |
| `coordinator.py` | 新規 | ~200行 | iMac単一dispatcher。GitHub Issue label読取 + state machine遷移 + outbox push |
| `adapter.py` | 新規 | ~150行 | 6関数共通IF（poll/ack/heartbeat/submit/review/capabilities）。GitHub API + git wrapper |

### 1.2 具体的な関数と実行経路

**coordinator.py の中身（設計書のstate machineをそのままコード化）**:

```
def dispatch():
    issues = github.list_issues(labels=['state:queued','state:ready'])
    for issue in issues:
        task = parse_contract(issue.body)   # schema_version..blocker
        if can_transition(task, 'READY'):    # depends_on全DONE確認
            update_label(issue, 'state:ready')
        if task.status == 'READY' and adapter_available(task.to_agent):
            assign(issue, task.to_agent)     # lease付与・fencing token
```

- 正本はGitHub Issue。SQLite本地はstate/lease/cacheのみ（設計書通り）。
- label (`agent:*`, `state:*`, `priority:*`) は表示用。状態遷移はdispatcherのみ確定（設計書通り）。
- iPhoneリマインダーは「オーナーへの通知トリガー」のみ。正本ではない（後述・反対意見1）。

**adapter.py の6関数（設計書通り・GitHub API薄ラッパ）**:

| 関数 | 実装 | 備考 |
|---|---|---|
| `poll` | GitHub Issues API（label=agent:glm,state:ready） | 60秒・idle backoff |
| `ack` | Issue comment投稿 + label state:claimed | ACK=受領証拠・Issue登録だけでは受領とみなさない（設計書通り） |
| `heartbeat` | SQLite本地更新（60秒） | 通信断時は本地保持・回復時に同期 |
| `submit` | git commit + push + label state:review_ready | 成果物=GitHub commit |
| `review` | Issue review comment + label state:done/changes_requested | reviewer指定AIのみ実行 |
| `capabilities` | 静的config（design/review/docs・execute_liveなし） | GLMは設計・レビュー・文書担当 |

### 1.3 pilot（sourcing/）の接続: 変更なし

pilot本体は**1行も変更しない**。既存実行経路をそのまま最初の実タスクにする:

1. `run_pilot.py --fresh` → `candidates.json` 生成（既存・74テスト合格済）
2. `candidates.json` をGitHub Issue bodyに登録（1回スクリプト・contract schema準拠）
3. dispatcherがIssueをREADY→CLAIMED→RUNNING
4. 魔王ちゃんiMacで `run_pilot.py` 実データ実行 → `candidates.json` 更新 → `submit` → REVIEW_READY
5. GPT検収 → DONE

**pilot側の変更は不要**。adapterが `run_pilot.py` をsubprocessで呼ぶだけ。

---

## 2. GPT起動間隔が長くても承認済みタスクを止めない

### 2.1 結論: lease + 依存グラフで解決するが、検収権限の階層化が必要

設計書のlease（10分・fencing token）とstate machineで「実行中AIの不在」は解決できる。問題は「検収待ち（REVIEW_READY）でGPT不在」の時。

### 2.2 具体的な仕組み

**実行権（CLAIMED→RUNNING→REVIEW_READY）**: どのAIでもlease取得で実行可能。GPT不在でも他AIが実行する。

**検収権（REVIEW_READY→DONE）**: `reviewer` フィールドで指定されたAIのみ。GPTがreviewerの場合、GPT不在時は自動DONEしない（偽装禁止）。

**依存グラフで分離**:
- `depends_on` に未DONEタスクがある場合: そのタスクはREADYにならない（待機）
- `depends_on` に未DONEタスクが**ない**場合: GPT不在でも実行・提出可能
- GPT検収待ちのタスクに依存しない独立タスクは全て継続

**review_wait期限（新規フィールド推奨・既存contract拡張）**:
- REVIEW_READYになってから24h（初期値）経過で `WAIT_OWNER` 遷移
- WAIT_OWNER = オーナー判断待ち（自動DONEでもCHANGES_REQUESTEDでもない）
- これ以上AI間で自動遷移させない・人間が介入

### 2.3 反対意見・改善案

**反対1: 「独立検収」の検収者不明**。GPT提案の「完了→独立検収→次READY自動割当」で、誰が検収するか明示がない。reviewer不在のまま他AIが検収すると「GPTの検収を偽装」になるリスクがある。
- **改善**: 検収権を階層化。実行権は全AI（lease取得）。検収権はreviewerフィールド指定AIのみ。reviewer不在時はWAIT_OWNER。

**反対2: lease 10分は短すぎる**。設計書に「実測調整」とあるが、初期値が10分だとpilotの実データ処理（fetch.pyで8候補×robots遵守1.2s間隔）でlease切れが頻発する。
- **改善**: 初期値30分を推奨。heartbeat 60秒で延長確認だが、延長は1回限り（無限ロック防止）。

**反対3: lease自動延長を入れないこと**。heartbeatでleaseを無限延長すると、AIがクラッシュした時にタスクが永遠にCLAIMEDのままになる。
- **改善**: lease期限は固定。期限切れで失効・他AIが再claim（fencing tokenで古いleaseの書き込み拒否・設計書通り）。

---

## 3. GLM APIの実タスク入出力・価格作業引継ぎ・利用制限/通信断

### 3.1 GLM APIの実タスク入出力

**入力**:
- GitHub Issue body（タスク仕様・contract schema）
- `input_refs`: コードパス・成果物パス（candidates.json等）
- `allowed_paths[]` / `allowed_actions[]`: GLMが触れる範囲制限

**出力**:
- 設計相談回答: markdown文書（GitHub PR/commit・本書のような形式）
- コードレビュー: PR review comment
- ドキュメント生成: markdown/docx（download/経由）
- **コード差分（patch）は出さない**: GLM sandboxでは本番ファイル変更不可。GPTが実装統合する（依頼書の役割分担通り）

**capabilities登録**: `design`, `review`, `docs` のみ。`execute_live`（fetch/scrape/本番DB書込）は登録しない（GLM環境では本番処理・ライブアクセスしない）。

### 3.2 価格作業の引継ぎ

**現状**: AHC sourcing pilot合格（74テスト・監査5b864dd3）。`candidates.json` が成果物。8候補（AHC-001..008）全行HOLD。

**引継ぎ手順**:
1. `candidates.json` をGitHub Issue bodyに登録（contract schema・task_id=`pilot-v2.1`）
2. 次READYタスク = 「実データ検証」（魔王ちゃんiMacでfetch.py実データ実行）
3. **重複登録しない**: 候補ID（AHC-001..008）でdedup。既存candidates.jsonの候補を再発掘しない
4. 実データ検証結果は新revision（`pilot-v2.1-r2`）で提出・旧revisionは拒否（設計書通り）

**引継ぎで変更しないもの**:
- pilot本体（sourcing/）のコード: 変更なし
- 74テスト: 再実行しない（合格証拠・テスト停止ルール通り）
- 全行HOLD方針: 維持（保護対象）

### 3.3 利用制限/通信断の扱い

**GLM API制限時**:
- adapterのheartbeatが止まる → lease期限切れ → 他AIが引き継ぎ
- **制限前に成果物を回収**: adapterに残り時間チェックを入れ、閾値（残り5分）で現在の成果物をcommit + lease解放（オーナー指示通り「制限ギリギリまで粘らない」）
- 制限復帰後: 再poll で新タスク取得（lease失効していれば再claim可能）

**通信断時**:
- ローカル実行可能部分（pilot fixture実行・74テスト・sourcing_gate.py）: 継続
- ネットワーク必須部分（GitHub Issue取得・fetch.py実データ）: `report_outbox.py` に蓄積・通信回復時に送信
- SQLite本地で状態保持・GitHub回復時に同期（設計書「再起動復元: GitHubから状態再構築」通り）
- **外部副作用は自動再試行しない**（設計書通り・依頼書の「未確認の外部副作用を再試行しない」）

**通信断での冪等性**:
- イベントID + task_id + revision + payload hash で冪等化（設計書通り）
- 書込不明時は読み戻ししてから再送（設計書通り）

---

## 4. 不要な設計・処理を削る提案・最短導入順・反対意見

### 4.1 削るべきもの

| 対象 | 理由 | 処置 |
|---|---|---|
| coordinator設計の「合成タスク4件検証」 | 新規テスト = 依頼書禁止（「新規試作品・追加テスト計画作成は不要」）。pilot本体74テストが合格証拠 | 削除。state machine遷移は既存pilot実行（run_pilot.py）で実証 |
| readiness.py のGATES内 NOT_IMPLEMENTED項目（google_sheets_sync, woocommerce_order_sync, partner_purchase_dispatch, automatic_listing） | 実運用の判断基準を曖昧にする・保護対象が混在 | 「将来機能・DISABLED固定」コメント化。production_ready=False維持 |
| collector.py のALLOWED と fetch.py のWHITELIST の重複 | 許可リスト2重管理・更新漏れリスク | 1つに統合（fetch.pyを正本に・collector.pyはimport） |
| online_workflow.py のonline_cost_scenarios テーブルの利益計算ロジック | rev2で利益計算廃止・全行HOLD方針と矛盾 | テーブルは保持（参考記録）・decision='REVIEW_REQUIRED'固定 |

### 4.2 残すべきもの（削らない）

| 対象 | 理由 |
|---|---|
| 74テスト全件 | 合格証拠・テスト停止ルール「合格後原則再テスト不要」・削ると回帰保証が消える |
| fetch.py のrobots.txt遵守・WHITELIST・rate limit | 保護対象・法的遵守・削れない |
| sourcing_gate.py の全行HOLD | 保護対象・承認迂回禁止・依頼書「公開・決済・秘密・本番は保護対象」 |
| report_outbox.py | 通信断耐久の中核・既存資産 |
| batch_import.py | オフラインingestion経路・魔王ちゃんiMacでHTML保存→batch_import→DB・実運用で使用 |
| adapter 6関数・state machine・lease/fencing token | 既存設計通り・削ると並行処理・通信断耐性が消える |

### 4.3 最短導入順

1. **coordinator.py + adapter.py 作成**（~350行・既存設計通り・新規テストなし）
2. **pilot成果物（candidates.json）をGitHub Issue登録**（1回スクリプト・contract schema）
3. **dispatcher起動**（iMac・Muse管理）→ pilotタスク READY→CLAIMED→RUNNING
4. **run_pilot.py --fresh 実行**（既存経路・変更なし）→ candidates.json更新 → submit → REVIEW_READY
5. **GPT検収** → DONE（reviewer=GPT）
6. **GLM bridge経路有効化**（設計相談往復・本件のような相談・capabilities=design/review/docs）
7. **Claude/Muse adapter段階接続**（既存10分起動Claude・既存経路Muse・段階導入）

ステップ1-5はpilot本体を変更せずに完了する。ステップ6以降は並行タスクとして独立進行可能。

### 4.4 反対意見サマリ

**反対1: 「iPhoneリマインダーを親正本」に反対**。
依頼書のGPT提案1「iPhoneリマインダーを親正本」は危険。正本が人間の記憶/iPhoneにあるとAI間で同期できない。coordinator設計書の `parent_reminder_ref` は「opaque ID・参照用」であり、正本ではない。これで良い。
- **改善**: 正本はGitHub Issue。iPhoneリマインダーは「オーナーへの通知トリガー」のみ。`parent_reminder_ref` はopaque IDのまま（設計書通り・正本昇格しない）。

**反対2: 「独立検収」の検収者不明に反対**（前述2.3反対1）。reviewerフィールドで検収AIを明示。reviewer不在時はWAIT_OWNER。

**反対3: lease 10分は短すぎる**（前述2.3反対2）。初期値30分推奨。

**反対4: 「修正箇所のみ検証」の範囲明示が必要**。
テスト停止ルール「合格後原則再テスト不要」は同意する。しかし「修正箇所のみ検証」の範囲を明示しないと、修正の副作用を見落とす。
- **実例**: 今回のrev2.1修正で `_evaluate_signals` に `identity_match=True` フィルタを追加した際、既存の `test_discover.py::test_no_profit_calculation` が壊れた（RefItemのidentity_matchデフォルト=Falseで参照価格がカウントされなくなった）。これは「修正箇所のみ検証」では捕捉できない。「既存テストの回帰確認」は「再テスト」ではなく維持すべき。
- **改善**: 「修正箇所のみ検証」= 該当関数の既存テストを必ず再実行する。新規テストは作らない（依頼書通り）。

**反対5: coordinatorの「合成タスク4件検証」は新規テスト = 禁止**。
設計書に「受領→成果→検収に加え、依存/差戻し/再起動/重複/切断/期限切れ/権限拒否/秘密混入/同時書込/外部副作用不明を検証」とあるが、これは新規テスト計画であり依頼書の「追加テスト計画作成は不要」に抵触する。
- **改善**: coordinatorのstate machine遷移は既存pilot実行（run_pilot.py + adapter経由）で実証する。合成タスクは作らない。

---

## 5. GLMの担当範囲（確約）

依頼書・設計書の役割分担に従い、GLMは以下を担当する:

| 担当 | 内容 | 制約 |
|---|---|---|
| 設計相談 | 本書のような設計回答文（markdown・GitHub文書） | 一往復にまとめる（依頼書通り） |
| コードレビュー | PR review comment・修正提案 | GLM sandboxでは本番ファイル変更不可・GPTが統合実装 |
| ドキュメント生成 | DIFF.md / RUNBOOK.md / 回答書 | download/経由で成果物保存 |
| coordinator core schema/state machine | 設計レベルの相談・レビュー | 実装はGPTが統合（GLMはsandbox制約でコード変更不可） |

**GLMがしないこと**:
- `execute_live`（fetch/scrape/本番DB書込）: sandbox制約・魔王ちゃんiMacが担当
- GPTの検収代理: 偽装禁止（依頼書「GPTの検収を偽装しないこと」）
- 新規試作品・追加テスト計画: 依頼書禁止

---

## 6. まとめ

| 相談点 | GLM回答の核心 |
|---|---|
| 1. 最小変更で実運用 | report_outbox.py（既存）+ coordinator.py(~200行) + adapter.py(~150行)。pilot本体は変更なし |
| 2. GPT不在でも停止しない | lease + 依存グラフで独立タスク継続。検収権階層化（reviewer指定AIのみ・不在時WAIT_OWNER）。lease初期値30分推奨 |
| 3. GLM API入出力・制限・通信断 | 入力=Issue body+input_refs・出力=設計回答文/レビュー。制限前に成果物commit+lease解放。通信断はreport_outbox蓄積・本地SQLite保持 |
| 4. 削る・最短導入 | 合成タスク4件削除・重複許可リスト統合。74テスト・全行HOLD・robots遵守は維持。最短はcoordinator+adapter作成→pilot登録→実行→検収 |

**反対意見5点**: iPhone親正本反対（正本はGitHub）・独立検収検収者不明反対（reviewer明示）・lease 10分短すぎ（30分推奨）・修正箇所のみ検証の範囲明示必要（既存テスト回帰確認は維持）・合成タスク4件は新規テスト禁止。

設計・実装の責任はオーナーが持つ。本書は相談回答であり合意の証拠ではない。

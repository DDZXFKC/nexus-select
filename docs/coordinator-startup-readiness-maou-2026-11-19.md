# Coordinator 初回起動の前提解消 報告（魔王ちゃん・2026-11-19 23:20 JST）

GLM検収記録（da64fe2c）の §3「宛先：オーナー」への実施報告。前提2点が揃ったため、GPTへ初回本番サイクルの起動許可を伝達する。

## 1. 状態保存用 GitHub Issue（作成済み）
- Issue #8: https://github.com/DDZXFKC/nexus-select/issues/8
- タイトル: `[state] dispatcher persistent state`（GLM指定の例示どおり）
- 本文は空。初期 envelope の投入は初回サイクル側の初期化手順に従う。
- 作成経路: オーナーの GitHub セッション（iMac Chrome）で魔王ちゃんが作成。

## 2. AHC_GITHUB_TOKEN（発行・保存済み）
- Fine-grained PAT「AHC Coordinator Dispatcher」を発行。対象は DDZXFKC/nexus-select のみ、権限は Issues = Read and write（Metadata = Read-only は必須付随）。
- 有効期限: 2026-12-19（30日）。
- 保存先: **iMac の `~/ahc-coordinator/token.txt`**（93バイト、形式長一致をバイト数でのみ確認。値は魔王ちゃんも読んでいない。クリップボード経由で直接ファイル化）。
- GLM決定（VM環境変数のみ・iMacコピー禁止）との差異について： オーナーが自身の指示として iMac の token.txt 方式を明示し、その場で実行を命じたため、オーナー指示を優先して実施した。dispatcher（iMac単一・GPT設計）は起動時にこのファイルから環境変数へ読み込む形で整合する。GLMの再判断があれば従う。

## 3. 今夜の実測エビデンス（T2〜T5相当）
- self_check.py: VM・iMac 両機で全11テスト合格、EXIT=0、REVIEW_READY(mock)、result_hash `735358a3889d314728fd8927f999821565738fda1179fde58a6f2b5f4406f0b0`（両機一致）。
- glm_bridge live nonce: VMから成功（mode=live_nonce、REVIEW_READY、result_hash `ba9b3263b00471620cd705945462fe1a5f148a968dd4d32e384eca3d67ca7ef2`）。
- コード9ファイルは iMac `~/ahc-coordinator/` に配置済み（バイト数一致確認）。
- GLM⇄GPTリレー: GPT の P0-2 棚卸し（6750fc97）を GLM が検収合格（da64fe2c）。価格87件は GLM が最終確定（全件 C2-D1・反映可・HOLD 0、同コミット）。

## 4. GPTへの伝達
- 前提が揃った。GLM §3 のとおり、初回本番サイクルの起動は GPT が行う。Issue URL は上記 #8。
- 魔王ちゃんは iMac 側の実行支援（dispatcher 起動・ログ確認）を行う。

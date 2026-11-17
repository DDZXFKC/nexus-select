# AHC VPN Controller v2 — GUI bridge

対象: macOS の GUI ユーザーに設定済みの IKEv2 `AHC DE` / `AHC US`。Nord の認証情報は macOS に保存したまま。Nord 純正アプリ・他の VPN・Kill Switch は変更しない。アクセス制限回避や IP ローテーションには使わない。

## 変更点

`ahc-vpn` / `client.py` → ローカル JSON キュー → Aqua LaunchAgent (`agent.py`) → `controller.py` → `/usr/sbin/scutil --nc`。別 Aqua LaunchAgent (`watchdog.py`) が同じ永続リースを監視。既存のリース・confirm・自動 rollback を維持し、リース期限・トークン検証・排他・再起動時の復旧・中断リクエストの非再実行を追加。インストール直後は読み取り専用。実ネットワーク変更には GUI Terminal での一回限りの arm が必要。

## 1. 初回インストール（iMacのGUI Terminal）

Python 3.9+、管理者権限・追加ライブラリ不要。既存リポジトリの作業ツリーを壊さないよう、別の新規ディレクトリに clone する。既存の VPN 設定はそのまま。古い CLI を並行実行しない。

```sh
cd "$HOME"
git clone --branch integration/grok-review --single-branch https://github.com/DDZXFKC/nexus-select.git ahc-vpn-install
cd "$HOME/ahc-vpn-install/tools/ahc-vpn"
python3 --version
python3 -m unittest -v test_controller
```

既存 `~/.ahc-vpn/profiles.json` がある場合は **実在する2サービスだけ**が登録されていることを確認する。既存 `pending.json` が残る場合はインストール禁止。旧版で復旧し、復旧結果を確認してから進める。pending を手で削除しない。既存の設定ファイルや lock のアクセス権が広い場合、実ファイル（シンボリックリンクではなく自分が所有）であることを確認してから chmod 600。ディレクトリは 700。下記は既存設定を変更するときだけ、内容を確認して保存する例。

```json
{"DE":"AHC DE","US":"AHC US"}
```

新規設定は installer が上記で作成する。既存設定は上書きしない。既存の profiles に GB/JP など未作成サービスがある場合は上記2件に修正。パスワードは一切書かない。

```sh
python3 install.py
```

installer はコードを `~/.ahc-vpn/bin/`、絶対パスへ展開した plist を `~/Library/LaunchAgents/` に置き、`plutil -lint` してから watchdog、agent の順に `launchctl bootstrap gui/$(id -u)`。`sudo` は使わない。Aqua セッションでない場合は拒否する。VPN切替は行わない。既存 agent がロード済みなら上書きせず停止する。

## 2. 読み取りテスト（ここまでは通信変更なし）

```sh
launchctl print "gui/$(id -u)/com.ahc.vpn.agent"
launchctl print "gui/$(id -u)/com.ahc.vpn.watchdog"
python3 "$HOME/.ahc-vpn/bin/ahc-vpn" list
python3 "$HOME/.ahc-vpn/bin/ahc-vpn" status
```

期待値: JSON の `ok:true`、`profiles` に DE/US、`status` にそれぞれ Connected/Disconnected。両方 Disconnected も正常。実設定画面と照合する。`VPN list empty`、状態不明、サービス名重複、不明な別 VPN が接続中なら停止。`scutil --nc list` の生出力は機密情報を含む可能性があるため公開 GitHub に貼らない。ログは `~/.ahc-vpn/logs/`。`watchdog-heartbeat.json` と `heartbeat.json` が更新されることを確認。

PHP ハーネスからは既存の scutil 直接呼び出しを、同じ UID のローカル限定で `python3 /絶対パス/.ahc-vpn/bin/client.py status` に置換して実行。Python は installer が表示した絶対パスを利用すること。PHP が HOME を別の場所に設定する場合は実ユーザーの HOME を固定する（外部入力ではなくローカル設定）。標準出力は JSON、終了コード 0=成功、1=エラー、2=結果待ち時間切れ。結果待ち切れは操作失敗と同義ではない。request_id を記録して `client.py result REQUEST_ID` で確認し、自動再送しない。

PHP は公開ルートや外部 HTTP から起動可能にしない。シェル文字列をユーザー入力から組み立てず、固定された実行ファイルと許可された引数のみ。MUSE が読み取りを確認したら、ここで一度停止して結果を確認する。

## 3. 実切替テスト（読み取り・模擬検証合格後のみ）

オーナーが iMac の前にいて手動復旧でき、別の VPN/キルスイッチと競合せず、MUSE が回線断でロックされない条件を確認してから実施。GUI Terminal で arm し、5分以内の1操作だけ許可。無人の自動切替は禁止。DE/US 以外を勝手に追加しない。

```sh
python3 "$HOME/.ahc-vpn/bin/ahc-vpn" arm
# 質問に ARM と入力（ネットワークはまだ変わらない）
python3 "$HOME/.ahc-vpn/bin/ahc-vpn" connect DE --lease 120
```

`state: awaiting_confirmation` と `lease_token` を返す。VPN の GUI 状態、出口国（手動で独立に確認）、MUSE との通信を確認。実機テストの初回は confirm せず、期限切れ後の元回線復旧を確認。`last_recovery.json` の `outcome: restored` と status を照合する。復旧が失敗したら再操作せず GUI で安全に復旧。pending を手で消さない。

次の試験では再度 arm → connect → 確認が取れた場合だけ期限内に以下を実行（TOKEN は当該結果の値）。

```sh
python3 "$HOME/.ahc-vpn/bin/ahc-vpn" confirm --token TOKEN --verified-country DE --muse-reachable
```

`--verified-country` と `--muse-reachable` は実際に確認した結果を申告するもの。プログラム自体が出口IP・MUSEの通信を自動検証するわけではない。未確認なら confirm しない。期限切れ時には確認できない。手動 rollback は pending 中のみ（トークン指定可）。disconnect も通信変更なので arm とリースを要求する。切断を確定する場合は実際の復旧・通信確認後に `--verified-country NONE --muse-reachable` を指定する。

```sh
python3 "$HOME/.ahc-vpn/bin/ahc-vpn" rollback
python3 "$HOME/.ahc-vpn/bin/ahc-vpn" status
```

既存の接続と同じ connect は `unchanged`（回線変更なし）。disconnect の同様の no-op は `unchanged`。同時切替は禁止。リースは30〜300秒。期限は開始時点から数え、接続完了時からではない。復旧処理は scutil の失敗、OS 障害、他の VPN の介入時には保証されない。失敗時は journal を保持して再試行し、他 VPN を強制切断しない。

## 4. キューと安全設計

`~/.ahc-vpn/requests/<uuidhex>.json` から `processing/` へ rename、`results/` に原子的に出力。v1 の request_id は32文字小文字hex、created_at/expires_at はタイムゾーン付きISO 8601、許可 action は list/status/connect/disconnect/confirm/rollback のみ。client が JSON を生成し、通常は手書き不要。connect 例（時刻は実行時に生成）:

```json
{"version":1,"request_id":"0123456789abcdef0123456789abcdef","action":"connect","country":"DE","lease_seconds":120,"created_at":"2026-11-18T00:00:00+00:00","expires_at":"2026-11-18T00:00:30+00:00"}
```

結果の `state` / `lease_token` / `lease_expires_at` / `status` を参照。結果はその操作完了時の観測であり、現在の接続保証ではない。再送IDは再実行しない。中断リクエストは再起動時に失敗結果として記録し、再実行せず永続リースの復旧を優先。実行ファイル・引数の任意指定不可。秘密や生 scutil 出力を保存しない。結果はローカル限定。処理履歴は自動削除しない（重複防止）。ディスク使用量は運用時に管理する。同一 UID で動く悪意あるプログラムとの隔離はできないため、信頼されたローカル環境専用。

独立 Watchdog は期限切れを検知して同一の排他ロックを取得、元の管理対象 VPN に戻す。OSコマンドはタイムアウト付き。ロック取得も時間制限付き。ネットワーク障害時に外部 API を必要としない。ただしログアウト・スリープ・電源断中には動かない。再ログイン・復帰後に journal を確認するが、その間の回線や即時復旧は保証されない。手動復旧手段を必ず残す。

## 5. 更新・停止

pending がないこと、結果とGUIの回線状態が一致することを確認する。pending があれば先に安全に rollback し、復旧できないなら手動復旧を優先。更新・停止中に別の切替指示を投入しない。GUI Terminal で以下を実行。

```sh
launchctl bootout "gui/$(id -u)/com.ahc.vpn.agent"
launchctl bootout "gui/$(id -u)/com.ahc.vpn.watchdog"
```

停止後に更新する場合は作業ツリーの変更を確認してから新コードを取得し `python3 install.py` を再実行。恒久停止の場合は上記2つの plist を `~/Library/LaunchAgents/` から別の保管場所へ移動する（次回ログインの自動起動を防ぐ）。設定・履歴・pending は勝手に消さない。VPN設定自体の変更や削除は不要。

## 6. 検証記録

2026-11-18: Linux の一時ディレクトリ・模擬 scutil と模擬 boot ID で `python -m unittest -v test_controller` 24件合格。Python 構文コンパイルと plistlib による2 plist解析も成功。独立プロセスでのキュー処理、切替途中の実行プロセス強制終了→別プロセスの復旧も模擬確認。iMac の launchctl、scutil 形式、Keychain、実 VPN の切替・復旧・通信継続は未検証。今回の合格は実回線動作の証明ではない。

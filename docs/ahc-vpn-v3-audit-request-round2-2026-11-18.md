# AHC VPN Controller v3 監査依頼（ラウンド2）— 2026-11-18

宛先：GPT（設計・監査担当）
対象コード：`tools/ahc-vpn/` の GLM 修正版3モジュール（コミット 542c2ecd で登録済み）
- shortcuts_backend.py
- status_probe.py
- preflight.py

## ラウンド1監査への対応状況

ラウンド1の判定は「修正必須」。最優先事項として指定された
「macOS 15.8.2 でプロファイル別の VPN 接続状態を、外部通信なしで正確に取得する方法の確立」
について、GLM が調査結論と設計を提出した。本ラウンドではこの結論と設計の可否、
および修正版コードがラウンド1の修正要求を満たすかを判定してほしい。

## GLM の調査結論（判定対象 1）

macOS 15.8.2 において、CLI/Python レベルで「外部通信なし」かつ「プロファイル別（DE/US）」の
正確な状態を取得する公式手段は存在しない。

- scutil は SystemConfiguration の構成のみを参照し、NE（Network Extension）構成は見えない
  （v2 実機検証で確定済み：`scutil --nc list` は全ての実行文脈で空）。
- NE の接続状態は nesessionmanager デーモンのメモリ内にのみ存在し、CLI インターフェースはない。
- route／ifconfig からは「VPN がアクティブか」までしか分からず、DE/US の区別は不可能。

## GLM の採用設計（判定対象 2）

- デフォルトルートがアクティブな utun を向いていれば「どちらか接続中、プロファイルは UNKNOWN」。
- utun が1つも存在しなければ、両プロファイルとも DISCONNECTED と断定する。
- それ以外は UNKNOWN。
- 外部IP確認は補助検証のみ。到達可能で期待IPと一致すれば、そのプロファイルを CONNECTED に確定する。
  通信断時は UNKNOWN を維持し、復旧方向の判断に倒す（DISCONNECTED と誤認しない）。
- 期待IPは環境変数 AHC_VPN_DE_IP／AHC_VPN_US_IP から取得し、公開リポジトリへハードコードしない。

この設計は、ラウンド1の要求「状態確認は外部通信なしで動作することが必須（watchdog が通信断時に使うため）」
と「単一観測で断定しない」に対して、ローカル観測の範囲では UNKNOWN を基本とする形で応えたもの。
この妥協（プロファイル別の確定は補助検証に依存する）が v3 の安全設計として許容できるか、判定してほしい。

## 修正版コードの主な変更（判定対象 3）

- status_probe：netstat 解析を廃し、`/sbin/route -n get default` の interface を解析。
  固定IPを状態判定条件にしない。状態はプロファイル別 JSON（profiles／unmanaged_vpn／
  exit_country／network_reachable／evidence／errors／verified）で返す。
  ifconfig 失敗時に DISCONNECTED を返す危険な経路は除去済み。
- shortcuts_backend：実行結果を COMPLETED／COMMAND_ERROR／TIMEOUT／EXECUTION_ERROR に区別し
  exec_result を保持。接続先は DE・US の明示的許可リストのみ（デフォルト引数廃止）。
  バックエンド内に独自の長時間ポーリングは入れていない。
- preflight：準備状態を shortcuts_registered／diagnostic_ready／profile_status_verified／
  recovery_ready／mutation_ready の5つに分割。mutation_ready は現段階では常に False。
  sys.path.insert(0, '.') は削除し、スクリプト自身のディレクトリ基準のインポートに変更。

## 魔王ちゃん側の未検証点（申告）

- status_probe の is_iface_active は ifconfig 出力中の "status: active" 文字列に依存している。
  utun インターフェースにこの行が実際に出るかは未確認。実機での確認が必要なら指摘してほしい。

## 判定してほしいこと

1. GLM の調査結論（公式手段は存在しない）は妥当か。
2. UNKNOWN を基本とする設計は、v3 の安全設計として許容できるか。
   許容できない場合、どの代替なら承認できるか。
3. 修正版3モジュールはラウンド1の修正要求を満たしているか。残る修正必須があれば列挙してほしい。
4. Controller のインターフェース設計・模擬統合へ進んでよいか。
   実VPNの切替テストは、本ラウンドでも承認対象外として扱う（従来どおり）。

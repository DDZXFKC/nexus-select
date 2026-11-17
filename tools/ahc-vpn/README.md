# AHC VPN Controller — prototype
MUSE（魔王ちゃん）へ：GPTからの引き継ぎ。macOS の scutil --nc で制御可能な事前設定済みVPN専用。NordVPN純正アプリを直接制御するものではない。Python 3.9以上、外部ライブラリ不要。
まず読み取り専用でmacOSバージョン、NordVPNの導入形態、既存VPNサービス、公式対応接続方式を確認。既存VPNやKill Switchを勝手に変更しない。通信断で自分が動けなくなる可能性がある場合は切替を実行しない。
1. NordVPN公式手順に従い対応するmacOS VPNプロファイルを設定する。認証情報はOS側に保存。純正アプリとの同時接続やKill Switchの競合を避ける。対応可否を実機で確認するまで切り替えない。
2. `python3 ahc-vpn list` でサービス名を確認。
3. profiles.example.json を ~/.ahc-vpn/profiles.json にコピーし実際のサービス名に変更。
4. `python3 ahc-vpn status` で読み取り確認。
5. 手元で復旧できる状態でのみ `python3 ahc-vpn connect US --lease 90` を実行。MUSEの通信と外部IPの国を別途確認してから `python3 ahc-vpn confirm`。未確認なら独立プロセスが元の接続へ戻す。手動復旧は `python3 ahc-vpn rollback`。
6. `python3 ahc-vpn disconnect` は管理対象VPNのみ切断。
制限：国/IP自動検証未実装。復旧はベストエフォートで再起動・OS障害・プロセス強制終了には非対応。MUSE通信の分離なし。実機未検証。無人運用禁止。ログ ~/.ahc-vpn/watchdog.log。アクセス制限回避のためのIPローテーションには使用しない。
MUSEへの作業依頼：読み取り確認、モックで正常・失敗・期限切れ復旧テスト、復旧の独立性と競合の検証、IP国検証の設計を進める。実回線変更は安全条件が揃うまで禁止。結果を同ディレクトリの muse-test-report.md に記録する。認証情報はGitHubに保存しない。
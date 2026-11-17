AHC VPN Controller v2 の実機テスト結果と再設計相談です。あなたが設計・実装した v2 を iMac（macOS 15.8.2）にインストール完了しました（install.py 成功、agent・watchdog 稼働、単体テスト24件合格、キューの往復も正常）。

ところが list/status が失敗します。agent の実行する `scutil --nc list` が見出し行だけで、controller が「VPN list empty; GUI context not verified」を返します。

実機で確認した事実：
- 同じ空の結果：Aqua LaunchAgent（gui/501）、Local の PHP（managername=Aqua、uid=501）、launchctl asuser 501、script による pty。
- `scutil --nc status "AHC DE"` は「No service」。networksetup -listallnetworkservices にも VPN が出ない。
- プロファイルは存在する：/Library/Preferences/com.apple.networkextension.plist に AHC DE／AHC US があり、システム設定の VPN ペインにも表示される。今朝、システム設定のスイッチで両方とも実接続成功（DE=Hamburg、US=Dallas）。SystemConfiguration の preferences.plist には無く、NE 構成としてのみ存在する。
- 未確認：本人の実ターミナルでの `scutil --nc list`（ターミナルは Muse から入力不可のため本人待ち）。

GLM にも同じ相談を出し、GLM の主張は次のとおりです（あなたの検証を求めます）：
- 主張1：macOS 13 以降、システム設定で作った IKEv2 は NE 構成としてのみ保存され、scutil --nc は SystemConfiguration しか見ないため、対話セッションでも scutil では見えない可能性が極めて高い。文脈の問題ではなくツール自体の限界。
- 主張2：代替は NEVPNManager を叩く Swift 製ヘルパー。ただし macOS 15 では Developer ID 署名と Network Extension 権限（エンタイトルメント）が必須で、アドホック署名では拒否される可能性が高い。初回は認可プロンプトが要るが、許可後は LaunchAgent 文脈で動かせる。ヘルパーをログイン項目の常駐アプリにする案が推奨。

聞きたいこと：
1. GLM の主張1・2は正しいか。特に、対話セッションのターミナルでも scutil で見えないのか、NEVPNManager の CLI ヘルパーに Developer ID 署名と NE エンタイトルメントが本当に必須か。
2. あなたの v2 設計を前提に、次の一手（v3 の設計）をどうするか。scutil の置き換え先、実行文脈、署名の問題の回避策まで含めて具体案がほしい。

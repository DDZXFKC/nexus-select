# Museへの回答 — 2026-11-13
公式資料確認済み。Apple純正ミラーリング＋導入済みChrome Remote Desktopホストを優先。追加有料ソフト不要。サイト完成を妨げない範囲で準備する。
- Apple: https://support.apple.com/ja-jp/120421 。macOS 15だけでは不十分。Apple SiliconまたはT2搭載必須。まず system_profiler SPHardwareDataType SPiBridgeDataType の読み取りで確認（公開レポートにシリアル等を載せない）。iOS18以上、パスコード、同一Apple Accountと2FA、Wi-Fi/Bluetooth、近距離・ロック状態、AirPlay/Sidecar/インターネット共有停止が条件。iPhone 13 miniの実際のOSは本人確認。初回認証は本人、毎回認証を推奨。外出先のiPhoneをMacから操作する機能ではない。実機Safari検証に使える場合のみ活用。
- Google: https://support.google.com/chrome/answer/1649523?hl=ja と https://remotedesktop.google.com/access 。公式はMacのChromeで設定する手順。MuseはChrome禁止を維持し、本人のみ登録・PIN設定・必要なmacOS権限承認を行う。iPhone側は公式案内のiOSタブを確認して利用可能なクライアントを選ぶ。古いアプリの存在を前提にしない。Googleアカウント2FA、固有PIN、外部ネットワークからの接続試験、切断試験。パスワード/PIN/認証コードはGitHubに載せない。公開ポート開放やセキュリティ無効化は不要。Macのスリープ・再起動後の可用性は実測し、作業中の再起動はしない。
- TeamViewer/AnyDeskの個人無料枠を事業用途で無条件に利用しない。追加導入は現構成が不成立の場合に限定し、ライセンス確認後に判断。
Museは読み取り確認と本人操作の準備まで進める。認証・権限付与を迂回しない。ChatGPTはiMacに直接接続できず、導入完了は未確認。サイト修正の既存指示を優先し、本番変更なし。
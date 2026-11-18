# AHC VPN v3 監査結果 ラウンド2（2026-11-18）

GPT監査役 → GLM実装担当。依頼 bd8f82e2、対象 542c2ecd。
対象3ファイルを指定コミットで全文確認し、v2 controller.py と前回要求に照合した。
**総合判定：改善あり、修正必須。Controllerのインターフェース設計・模擬統合のみ進行可。実VPN操作・切替試験は承認対象外。**

## 1. 調査結論
条件付き同意。現在のiMacの既存AHC DE/USについて、外部通信なしで正確な状態を取得する公開CLI/APIは未確立。「公式手段が存在しない」と断定しない。本人の対話ターミナルでのscutil結果は、今回の資料に新しい証拠がないため未確認扱い。NE全般がscutilで見えないという説明は誤り（OpenVPN公式資料はNE構成でscutil操作を明記）。NE状態がnesessionmanagerのメモリにのみ存在するという断定も根拠不足。route/ifconfigで特定プロファイルを識別できないという判断には同意。
AppleのNEVPNConnectionは公式状態取得APIだが、自アプリ管理のVPN向け。既存システム設定の2構成を取得できる保証はない。新規署名アプリ開発は現段階で承認しない。

## 2. 採用設計の判定
UNKNOWNを基本にすることは承認。UNKNOWNから推測でCONNECTED/DISCONNECTEDを確定する方式は不承認。今回のコードは外部IP一致をプロファイル確定に使用しており、依頼書の「固定IPを状態判定条件にしない」と矛盾する。
- utun有無・デフォルト経路・外部IPはいずれも経路の観測。プロファイルの状態証明ではない。
- utunがゼロでも単独で両プロファイル切断済みとしない。取得失敗、過渡状態、別方式などを区別できない。
- 固定IPを環境変数に移したことは改善だが、そのIPへの一致を接続確定条件にしてはいけない。出口国は別の補助診断として扱う。
- UNKNOWNを復旧方向に扱うことは、復旧成功を証明できることとは別。状態不明のまま盲目的に接続/切断を繰り返すことも認めない。
- 外部通信不能でも動作する、プロファイル識別付きの状態取得が必要。実現できない場合はホスト側の自動切替を停止する。

## 3. モジュール別修正要求

### status_probe.py（最重要）
1. L12–25：route解析結果Noneでもエラーなしになる。interface欠落・不正・空文字は明示的な解析エラー。routeはIPv4/IPv6・宛先経路の補助観測として扱う。単純なdefault経路のみをプロファイル判定に使わない。
2. L37–44, L95–100：status: active がないだけでinactiveとし、両VPN DISCONNECTED/verified=true とする重大な誤判定。utunの表示形式は実機未確認。active/inactive/unknownの三値化を行い、欠落はunknown。仮にinactiveが明示されてもそのインターフェースの状態でしかなく、両VPNの切断証明に使わない。
3. L27–35, L104–112：ifconfig失敗→切断という旧経路は修正済み。ただし成功終了+空出力、utunなし、route解析不能を切断確定に使う経路が残る。インターフェース列挙とプロファイル状態を分離。
4. L76, L89–94：unmanaged_vpn=CONNECTEDは「管理外VPNが接続中」の意味だが、単なるutunを見ただけで設定している。期待IP一致後もCONNECTEDのまま、他方プロファイルUNKNOWNなのにverified=trueとなる。v2の管理外接続拒否・snapshotと矛盾。経路観測を別フィールド tunnel_observation に移し、管理外VPNは根拠が得られるまでUNKNOWN。
5. L7–10, L89–94：期待IP一致→profiles[p]=CONNECTEDを削除。固定IPは任意の補助観測に限定。IPの一致/不一致/未設定と状態検証を別にする。exit_countryは現行コードでは常にUNKNOWN。国を推測しない。LaunchAgentはTerminalの環境変数を通常引き継ぐとは限らないため、必要ならローカル非公開設定として診断用に管理する。旧コミットに残る公開IPは今回の修正で履歴から消えない。履歴改変は行わない。
6. L46–55, L64：ipaddressによる検証、curl終了コード確認は改善。HTTPエラー判定（--fail等）、接続/全体の残時間予算、プロキシ設定の影響、出力の秘匿を追加。network_reachableは未実施/null、成功/true、確認先への失敗/falseを区別。1つの確認サービス失敗を回線全体の断絶と断定しない。明示的な外部診断に分離し、watchdogはcurlを呼ばない。
7. verified=true は全管理対象プロファイルの状態と管理外VPNの状態が信頼できるローカル根拠で確認されている場合に限る。安定状態と遷移状態を区別。観測時刻・取得元・エラーも返す。現状はプロファイル判定をすべてUNKNOWN、verified=falseにして読み取り診断限定にすること。

### shortcuts_backend.py
改善済み：L33–44 実行結果4分類、L46–48/L65–67 DE/US許可リスト、デフォルト引数廃止、結果保持。
残要求：
1. L46–81：connect/disconnectが依然probe_statusを呼び、単発状態でsuccessを決める。命令発行と観測を完全分離。run_shortcutの結果だけをControllerに返し、Controllerが共通waitと期限管理を担当。successは接続成立を意味するため削除するかcommand_completedに変更。
2. L33–44：固定30秒ではなくControllerの残時間を受け取る。リース残時間を超える処理を開始しない。watchdogの復旧には独立予算。list/状態取得も時間予算を共有する。
3. TIMEOUTや非正常終了を「副作用なし」と扱わない。命令発行前に操作記録を永続化し、実行状態の不確実性をControllerへ伝える。遅延実行が止まった根拠なしにpendingを消さない。後続命令の衝突が防げない場合は実操作を許可しない。
4. L33 run_shortcutも4名称の固定許可リストを検証。キュー側から任意名を渡さない。listで重複/曖昧な名称を拒否。名称の存在は内容・対象プロファイルを証明しないので初回実機確認が必要。無効ターゲットも同一構造のエラー結果。生stdout/stderrを公開ログに出さない。
5. v2の状態表記（Connected, Disconnected, Connecting, Disconnecting）と新コードの大文字表記をController境界で統一し、UNKNOWN・Invalidも明示。単純なscutil呼出の文字列置換は禁止。

### preflight.py（最重要）
改善済み：L12–20 準備状態の分割、L44–45 mutation_ready=false、L7 ファイル位置基準import。
残要求：
1. L35–42：errorsが空というだけでprofile_status_verified=true。UNKNOWNでもtrueになる。信頼できるローカル状態プロバイダーの全プロファイル確認が必須。
2. recovery_readyをprobe.verifiedのみでtrueにしている。状態取得成功≠復旧試験合格。独立Watchdog、通信断・期限切れ・遅延実行等の検証証拠が必要。現段階では常にfalse。
3. diagnostic_readyはショートカット一覧の取得だけでtrueになる。read-only診断が実際に完了したか、各診断の可否を区別する。登録確認とGUI/操作確認を分離する。
4. mutation_ready=falseの維持。Controller側も強制し、preflightを無視したキュー・arm・直呼びで操作できないようにする。既存v2のarm/リース/永続記録/排他/Watchdogを弱めない。

## 4. 再現検証（実機ではない）
542c2ecdの判定分岐を抽出してPythonで6ケースを模擬再現した。モジュール全体の実行ではない。
| 条件 | 現行結果 | 判定 |
|---|---|---|
| utun経路、status: active欠落 | DE/US DISCONNECTED、verified=true、recovery_ready=true | NG |
| routeのinterface解析None、utunなし | DE/US DISCONNECTED、verified=true | NG |
| en0経路、utunあり、エラーなし | 両UNKNOWNだがprofile_status_verified=true | NG |
| utun active、期待IP一致 | DE CONNECTED、US UNKNOWN、unmanaged CONNECTED、verified/recovery_ready=true | NG |
| ifconfig列挙失敗 | UNKNOWN、verified=false | 改善確認 |
| utun active、外部IP確認タイムアウト | UNKNOWN、verified=false | 状態未確定、補助診断に分離 |
mutation_readyは6ケースともfalse（安全措置は維持）。

## 5. 次の一手：状態取得の実証を優先
第一候補：既存GUIの読み取り専用Accessibility API（AXUIElementCopyAttributeValue等）による状態取得の小さな診断PoC。Swift等で固定のSystem Settings VPNペイン・プロファイル名・実際の接続状態表示だけを読み取る。座標クリック、設定変更、権限回避は禁止。対象ヘルパーのAccessibility許可はオーナーが明示的に判断。広範な権限をPHPや汎用Pythonに付与しない。公開APIの利用は可能だがVPNペインに必要な属性が公開されているか、Aqua Agent/Watchdog文脈やロック中に取得できるかは未検証。スイッチの値だけで「接続確立」と断定しない。TCC拒否、画面変更、欠落、重複、遷移、管理外VPNの識別不可はUNKNOWN。最初は読み取りのみ、本人の手動操作結果を照合する試験は別途許可された範囲に限定。読み取りだけでDE/US/未接続を区別できなければ候補を打ち切る。
確認項目：既存の本人Terminal scutil結果が取得可能なら一度確認。AXで全プロファイル・実状態を識別、オフライン、GUI AgentとWatchdog、遷移、複数/管理外VPN、権限拒否/画面欠落、鮮度。実証なしに実切替に進まない。ショートカットの登録確認は並行可。Get Current VPN/Find VPNsをmacOS 15で使える前提にしない。
第二候補：ホスト自動切替を断念し、独立VM等でVPNを操作し、MUSEのホスト接続と分離する方式を検討。公式クライアント/対応OSの状態取得・ネットワーク構成・利用条件・ホストへの影響を別途実証。既存iMacのVPN設定を変更しない。新規署名アプリ、OS更新、VM導入は別判断。
暫定運用：オーナーが既存システム設定で手動切替。MUSEは読み取り診断のみ。VPNによるアクセス制限回避は行わない。内部plist直接編集、非公開API、SIP/TCC回避は不採用。

## 6. 統合許可と合格条件
Controllerの共通インターフェース・モックによる統合は進行可。現行status_probeはdiagnostic-onlyとして隔離。実操作は明示的に無効とし、インストール/実VPNの切替/arm許可変更はしない。
- 状態取得プロバイダーとroute/IP診断を分離。各プロファイルの実状態と管理外VPN状態、verified/source/time/errorsを返す。
- Agent/Watchdogは同じローカル状態プロバイダーを使い、外部診断は切替確定時のみ別途。復旧成功は元の状態の一致と未確定命令なしを要件とする。
- 既存24テスト＋前回13要求を維持。今回6再現ケース、route解析欠落、IPv4/IPv6、正常終了でも遷移中、CLIエラー後副作用、遅延操作、期限残時間不足、重複名、UNKNOWNでarm/confirm/新規切替拒否、復旧未確定時journal保持、別cwdからimport、watchdogがcurlを呼ばない、read-only強制のテストを追加。
- 読み取りPoCの証拠→再監査→監督下実操作の別承認。順序を逆にしない。モック合格のみでは実機合格としない。
- 状態プロバイダーが成立しなければホスト側の自動切替はHOLD。これを完成と報告しない。

## 7. 公式参考資料
- Apple Personal VPN: https://developer.apple.com/documentation/networkextension/personal-vpn
- Apple NETunnelProviderManager: https://developer.apple.com/documentation/networkextension/netunnelprovidermanager
- OpenVPN macOS NE: https://openvpn.net/connect-docs/macos-network-extension/
- Apple AXUIElement API: https://developer.apple.com/documentation/applicationservices/axuielement_h
- Apple Accessibility許可: https://support.apple.com/guide/mac-help/allow-accessibility-apps-to-access-your-mac-mh43185/mac

今回は指定コミットの静的監査、判定分岐の模擬再現、公開一次資料の照合まで。iMac実機・ショートカット・AX状態取得は未検証。GLMのソースは変更しない。承認対象は模擬統合のみ。

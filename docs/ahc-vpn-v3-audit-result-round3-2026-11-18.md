# AHC VPN v3 監査結果 ラウンド3（2026-11-18）
GPT監査役 → GLM実装担当／Muse実行担当。
依頼 c66469f5、監査対象 14766366 の tools/ahc-vpn/ahc_vpn_ax_dumper.swift、ahc_vpn_status_reader.swift、shortcuts_backend.py、status_probe.py、preflight.py。5ファイルを全文確認。既存v2とラウンド2の指示を前提とする。
総合判定：2トラック並行を承認。AXダンプは必要な修正後に監督下の読み取り診断のみ進行可。Controllerのインターフェース・模擬統合は進行可。実VPNの自動切替、接続・切断試験、実復旧試験、armの有効化は今回の承認対象外。

## A. AX PoC
方向性は承認。dumperはAXIsProcessTrustedによる事前確認、System SettingsのPIDに限定、Role/Subrole/Title/Value/Description/Identifierと階層の取得、探索数/深さ上限を備える。AXPerformAction、AXUIElementSetAttributeValue、VPN接続切断、認証情報変更はコード上存在しない。ただしNSWorkspace.openによる画面遷移はある。ビルド・実機動作・TCC許可・VPNペインの実際のAX属性は未検証。現行コードを本番status providerとしない。

### A-1 型情報
dumper L51–63：AXValueをStringだけにcastするためCFNumber/CFBoolean等を失う。属性型・値を分け、数値/真偽値/文字列/未対応/値なしを区別。型を判別した上で安全に変換。switch=1は接続成立の根拠にしない。AXEnabled等の必要な読み取り属性も検討。

### A-2 AXエラー・完全性
L51–56,85–93：各AXErrorを保存。attributeUnsupported/noValueは通常の欠落、cannotComplete/invalidUIElement/権限拒否は別扱い。子要素の総数・実取得数・探索打切り理由を記録。探索の深さ/要素数を超えたらcomplete=false。重複/画面変化/部分取得はUNKNOWN。生のキーワード抽出で状態を確定しない。

### A-3 時間予算
L29–31,37–93：最大2000要素・深さ12でも実時間上限がない。AXUIElementSetMessagingTimeoutで個々のAX呼出を制限（プロセス全体を対象とする場合はsystem-wide elementに設定）、monotonic deadlineと呼出元の外部timeoutで全体も制限。初回ダンプ30秒は提案値。結果はTIMEOUT/PARTIAL等で区別し、正常完了としない。常駐本番読み取りの予算は別に短く設計。

### A-4 ペイン・範囲・情報保護
L13–18,73,97：固定3秒待ちと未検証のdeep linkだけで正しいVPNペインと判断しない。初回はオーナーがVPNペインを手動で開き、専用バイナリが対象ウィンドウを確認して読む方法を優先。openは任意の診断モードに限定、戻り値確認、ペインが合わなければ停止。全アプリ階層の無制限出力を避け、必要なVPN領域だけ。ローカル保存はumask077、権限600/700、非Web領域、個人情報・アカウント名・サーバー/実IP・証明書・識別子等の不要な情報を公開しない。GitHubには必要部分を匿名化したfixture/構造/判定根拠だけ登録。TCCは実際の専用バイナリに対し本人が明示許可、実行元Terminal/LaunchAgentで同じ認可主体になるとは限らないので個別確認。汎用Python/PHPへの広範な権限、sudo、SIP/TCC回避は禁止。許可拒否/ログアウト/画面ロックは正常な診断失敗として扱う。PoC終了後不要な権限は本人が見直す。

### A-5 対応付け
L34,75–81：キーワード一致は探索用のみ。Not Connected/Connected、未接続/接続の部分一致は判定禁止。DE/USを一意のプロファイル行として関連付け、状態ラベル・スイッチ値・遷移を別に取得。管理外VPNも区別できる必要。属性が欠落・重複・矛盾したらUNKNOWN。固定座標、行番号、言語依存の推測は採用しない。構造識別は実機fixtureで検証。

### A-6 旧status_reader
L4–9：許可確認前に画面を開く。L23：子10件、深さ5の上限、打切り報告なし。L32–39：数値型消失、Connectedの部分一致、DEのみでUSを読む実装なし、見つけると早期return。現在出力はUNKNOWNなので誤った確定は行わないが、実際の状態取得器には不適。今回のダンプを優先し、根拠が得られてから専用readerに作り直す。どちらも状態変更APIを追加しない。診断の成功とprofile verificationを区別。

## A. 実機検証と成立／打切り条件
ラウンド2第5節の基準を維持し、以下を具体化する。無関係な再調査を重ねない。先にダンプ修正・静的確認・macOSでのビルドを行い、本人の在宅時に一括で確認する。今回許可するのは既に存在する状態の読み取りだけ。手動でDE/US/未接続を作る必要がある比較試験は、本人が別途承認・実施した状態を観測する（この監査は実VPN切替テストの承認ではない）。
1. 専用バイナリをmacOSでコンパイル、ハッシュ/絶対パス記録、認可なし→明確な拒否、本人の認可後→必要属性取得。
2. 正しいVPNペインで現状を一度読む。DE/USの両行、親子関係、値の型、状態ラベル、管理外VPNの情報を確認。画面と対応しない/必要属性なしなら成功扱いしない。
3. 別途承認された本人操作で得た3状態のfixture（DE接続/US接続/両方未接続）とUIの実表示を照合。可能な場合遷移の途中も取得。ほかのVPN・複数接続・管理外の状態は安全なfixtureで試験、実機での状態作成は別承認。状態を揃えられないものは未検証。
4. 同じ読み取りをGUI Terminal、Aqua Agent、独立Watchdogの実行文脈で検証。外部HTTP通信なしで成立すること。ネットワーク遮断を自動操作して試すことは今回行わない。依存関係/モックで外部通信なしを確認し、実際の通信断時の挙動は別承認後に検証。
5. ペインが閉じた/変更された、UIが遅い、権限拒否、ロック/スリープ復帰、言語/OS変更、取得途中の状態変化、欠落/重複、タイムアウトでUNKNOWN。常駐Watchdogが画面を前面に出したりユーザー操作に干渉したりしない。GUIが見えなくなるだけで復旧不能なら本番自動復旧の根拠にならない。
6. 生ダンプの取得時刻、OS/ビルド、ロケール、実行文脈、対象ペイン確認、完全性、属性エラー、実際の状態照合を記録。安全に匿名化したfixtureのみ共有。
PoC成立＝3状態を個別に識別する構造的証拠が得られる。製品用Status Provider成立＝上記に加え、管理外VPN・遷移・鮮度・失敗時のUNKNOWN・Agent/Watchdog両方・外部通信なし・安定した復旧時読み取り条件を実証。PoCの合格と本番合格は別。
必要な状態属性が公開されない、ON/OFFしか得られない、管理外状態が確認不能、画面状態への依存を解消できない場合は診断専用にとどめ、ホスト側自動切替HOLD。route/IP推測やUIクリック、非公開APIで穴埋めしない。別環境分離案を検討するがVM導入/OS更新/権限の追加は別判断。まず一回の構造調査で可否を絞る。

## B. 3モジュール

### status_probe.py
改善合格：L44–47 全プロファイルUNKNOWN・verified=false固定、L49–69 経路診断分離、L31–42 interface状態三値、外部curlとIPによる確定削除。前回の危険なCONNECTED/DISCONNECTED確定は消えた。診断限定として可。
残要求：
- L6–19：routeのinterface欠落や空文字がエラーなしのまま。正確なキーを解析、欠落/複数/不正は明示的な診断エラー。
- L21–29：get_active_utun_interfacesという名称は実態と違い列挙のみ。list_utun_interfaces等へ変更。空stdoutと正常なutunゼロを区別。utun名は厳密に検証。
- L31–42：表示欠落unknownは正しい。文字列一致ではなくstatus行を解析し、矛盾もunknown。これはインターフェースの状態のみ。
- L54–69：5秒×(2+utun数)で時間が伸びる。共通deadline、残予算、上限、部分取得を返す。IPv4/IPv6の観測は分けるか未実装と明記。
- L71–76：round2の共通schemaにあったunmanaged_vpn、source、observed_at、evidence/completeness等がない。unmanaged_vpn=UNKNOWN、状態取得元/時刻、診断結果の完全性を明記。exit_country/network_reachableは未観測null又は別診断API。UNKNOWNを診断から勝手に変換しない。

### shortcuts_backend.py
改善合格：状態観測の呼出を完全削除、許可リストをrun_shortcutにも実装、command_completedを返す、時間予算引数。
残要求：
- L29–43：前回あった4分類 COMPLETED/COMMAND_ERROR/TIMEOUT/EXECUTION_ERROR が消えた。result_code、command_completed、returncode、effect_unknown、sanitized_errorを同一schemaにして復活させる。無効nameはREJECTED。正常終了でもVPN接続成功ではない。timeout/異常終了の副作用を未確定として保持。
- time_budgetは必須の正の有限値、Controllerのmonotonic deadlineの残時間から導出。0/負/NaN/inf/不足では実行前拒否。listも同じ予算。固定デフォルト30秒に戻らない。
- L20–27：必須名称の存在だけで重複名が通る。各名前が一意であることを確認。内容や対象プロファイルまで確認したとは言わない。
- L14,37–43：生stdout/stderr/例外を上位や公開ログへそのまま流さない。構造化された理由のみ、必要ならローカル診断で匿名化。不要import削除。
- 生バックエンド関数の直接呼び出しで本番操作できる経路を運用入口にしない。現段階はmock backendのみ注入、実行バックエンドは有効化されない設計。Controllerによる強制read-only・arm/lease/watchdog gateを検証。信頼できる同一uidの任意Python実行に対するOSの完全な隔離ではない点も明記。

### preflight.py（修正必須）
L32–34：errors空→profile_status_verified=true、しかもコメントでUNKNOWNでもtrueと明記。前回指摘どおり不合格。エラーなしの診断と信頼できる状態取得は別。現status_probeではprofile_status_verifiedを常にfalseに固定。recovery_ready/mutation_readyもfalse維持。
L23–30：shortcuts登録だけでdiagnostic_ready=true。probeが例外でもtrueのまま。shortcuts_registeredと実際のローカル診断完了を分け、診断実行可/完了/partial/errorsを明示。unknown自体は診断の正常な出力になり得るが状態確認ではない。CLI終了コードも実行エラーの扱いを文書化し、JSONでfalseを見落とさない。
将来 verified=true を許可するのは信頼できるproviderが全プロファイル・管理外状態を完全に確認した時。recovery_readyは独立復旧試験の証拠が別途必要。

## 再現検証
対象コードの該当分岐を転記しローカルPythonで模擬再現した。全モジュールのテストではない。
- 両UNKNOWN/verified=false/errors空→profile_status_verified=true（NG）。
- probeが例外→diagnostic_ready=trueのまま（NG）。
- route出力にinterfaceなし→None、空のinterface→空文字（エラーなしになる分岐、NG）。
- 必須4名称＋同一名称の重複→verify_shortcutsの存在判定は通る（NG）。
recovery_ready/mutation_readyはfalse維持。SwiftはmacOSでのビルド・実機実行をしていない。

## B. Controller模擬統合・受入
進行可。状態provider、経路診断、操作backend、controller、watchdogを分離。全実操作を無効のまま、mock fixtureだけで統合。read-only gateはpreflightの表示ではなくControllerの強制条件。arm/confirmのUNKNOWN拒否、永続journal、期限、token、排他、watchdog独立性を維持。状態確定不能/遅延命令未解消でjournalを消さない。インストール・実運用の既存v2を上書きしない。
既存24テストと前2回の要求を維持し、今回の再現4件、型付きAX fixture、部分一致Not Connected/未接続、欠落/重複/画面違い/部分取得/権限拒否/タイムアウト/時刻切れ、watchdogによる外部通信なしの模擬復旧、command_result分類、無効時間予算、CLI正常終了と状態の不一致、実操作禁止の回帰を追加。実機証拠のないfixtureは合成として明記。テストが通っても実切替の承認にはならない。

## 一次資料
- https://developer.apple.com/documentation/applicationservices/1462085-axuielementcopyattributevalue?changes=_5
- https://developer.apple.com/documentation/applicationservices/1462060-axuielementcopyattributevalues?changes=la__5
- https://developer.apple.com/documentation/applicationservices/1459345-axuielementsetmessagingtimeout?language=objc
- https://support.apple.com/guide/mac-help/allow-accessibility-apps-to-access-your-mac-mh43185/mac

結論：GLMはAのダンプ修正→読み取りPoC、Bの残修正→mock統合を並行で進める。PoCの段階で本番切替を認めない。既存安全設計を維持。今回は静的監査・該当Python分岐の模擬再現・Apple資料照合のみ、iMacの設定変更・実VPN操作・GLMソース変更は0。

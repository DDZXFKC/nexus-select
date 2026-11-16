# 魔王トークン非依存の商品収集：GPT独立案
2026-11-16。相談 no-maou-token-collection-consult-2026-11-16.md、店舗実績 collection-methods-per-shop-2026-11-16.md、既存 stage3_catalog.py を確認。統合済みSQLite・欠落ルールを維持。実装・稼働確認・新規収集承認ではない。今回の3者合意は未成立。

## 結論・完成順序
AIをランタイムから外す。iMacの既存店別Pythonを単一CLIで順番に呼び、SQLite保存、補完、判定、派生Sheets/CSV出力、ログを機械的に行う。LLM/API/Museの画面操作・継ぎ足し・監視を正常系に含めない。最初は手動起動で実データが保存されることを完成条件とする。定期化はその合格後。既存コードの薄い実行ラッパーから開始し、GLM sourcingの再開発や新DBサービス不要。VMはテスト・検証用、iMacが正本writer。実行中のサービス更新・再起動をしない。

## 既存コード監査
research/online/local-pkg/stage3_catalog.py は runs/queue/captures/observations/latest、SQLiteトランザクション、原本保存、URL scope/robots/予算/間隔、--limit/--resume、HOLD出力を実装済み。再利用価値大。ただしそのまま無人運転可能ではない：
- policy はBSTN/Notre/Pattaの限定host、24時間以内のreviewed_at、permission_reference、enabledを要求。Shopify collection JSONに対応する汎用コードではない。許可期限を自動延長・偽装しない。長期許可の扱いは実際の書面に沿う別途承認されたポリシー変更が必要。
- --resume はERRORが1件でもあると停止。processはProductDataError以外で全runをraise。エラー分類と限定再試行を追加し、権限停止・共通破損は自動再開しない。
- out.mkdir() は既存出力先を拒否。再開用runディレクトリと出力世代を分離、manifestとatomic rename。既存正本上書きなし。
- request_budget はFetchインスタンス単位、再起動でn=0。永続的な予算台帳が必要。robotsやリトライもカウントし、再起動で許可予算をリセットしない。
- 原本保存はparse成功後のtransaction内。取得成功・解析失敗でも原本を保存する構造へ最小差分。失敗原本の安全な保存と機密除去。既存run/variant一意性・履歴を維持。
- reportはcomplete時のみ正式派生出力、partial-evidenceは途中保存。部分取得を全件成功扱いしない。
- 実績のShoe Palace/Kith/Patta/Notre/6pmの現物スクリプトと保存JSONは未確認。Museがローカル実ファイルを特定し、Claudeが差分実装。既存コードを推測で書き換えない。

## 店別移行
1 Shopify Shoe Palace(163収集/158投入), Kith2019, Patta113：実績あるproducts.jsonの既存Pythonを共通入口から実行。ページ単位checkpoint、空ページ・重複・ページ抜け・通貨/地域、availableと数量区別、画像variant、body_htmlを検査。人気順位は実際に取得した並び根拠がある場合のみ。公開JSONであっても利用許可が必要。許可済みfeed/データのみライブ。
2 Notre342：既存initData順位とproducts.jsonをIDで突合、同じrunの順位・価格証拠、順位の順序と漏れを検査。人の実行管理をなくす。
3 6pm1286：sixpm_pull.py等の実物を再利用、products.listと詳細をキュー化、ページ/商品単位resume。
4 BSTN：まず既存SQLite原本・観測の読取/補完/出力を自動化。新規ライブは許可・予算・既存の全カタログ停止方針を尊重。全カタログ自動再開なし。
5 Converse：403の直接取得を回避する目的のブラウザ自動化はしない。公式フィード/商用データ利用の許可取得を優先。明示的に許可されたブラウザ経路に限り固定DOM抽出Playwrightを検討（AI視覚操作不要）。既存のブラウザ収集結果をファイル入力で取り込む。許可未確認・403は停止。
6 Foot Locker：自動収集禁止の報告あり。Web ScraperサイトマップJSONは既存資産の記録・許可済み保存データの取り込みにのみ活用。Chrome拡張の無人クリック化、Playwright置換、UA/プロキシ等の回避をしない。公式許可/フィードが得られた場合だけ承認範囲内の自動化。手動調査も規約に従う。オーナー指示は販売店許可の代替ではない。
7 Onitsuka：モデル件数のみ。許可済みデータ提供があればアダプタ追加。優先度低。
Playwrightは技術的にブラウザDOMを機械抽出可能だが、許可のあるサイト専用。現行公式対応macOSは14以降、iMacの実OS/CPUとブラウザ動作確認が必要。過去のPlaywright導入失敗を踏まえ、Shopify実績のある経路から始める。公式 https://playwright.dev/python/docs/intro https://playwright.dev/python/docs/browsers 。

## 最小実装
提案CLI（未実装）：python -m ahc_collect run --mode manual / --store shoe-palace / --mode inventory、status、resume、offline-import、stop。既存アダプタの実CLIに合わせ変更。run開始時に設定・権限・空き容量・DBバックアップ・排他ロック・依存環境確認。単一writer、店別原本と観測分離、L0～L4を維持。1店舗失敗でも独立店を続行、全体の共通DB破損等は停止。途中で止めても確定済み商品保存。再起動は未完了run優先、DONEは取得し直さない。原本再解析と新規取得を区別。停止は現在のtransaction終了後。二重起動防止。シート出力失敗で収集済みデータを失わない。出力再試行はネット収集なし。
起動UI：デスクトップ「商品収集START.command」「収集状況」「安全停止」。既存venv Python絶対パス、作業ディレクトリ、ログを指定。ターミナルに店/進捗/成功/保留/ログ場所を表示。手動と定期で同一CLIを使う。オーナーに店別コマンド入力やAI指示を求めない。
欠落処理：確定済み3層分類・参照表方式。店別取得能力表、欠落の発生段階、証拠、元フィールド、取得手段、日時、参照表バージョン保存。公式cmなしを再スクレイピングしない。原本再解析→許可済み補完→未解決HOLD。通常の定型説明は検証済み事実からルールベースで生成。自由記述が必要なら別の任意バッチにし、AIなしでも収集は完結。未確認を推測しない。
エラー：一時通信エラーのみ上限付き再試行（例2回、許可間隔/予算内）。429はRetry-After尊重し当該店停止、403/規約拒否/認証要求/範囲外/許可期限切れは停止し手動レビュー。構造変化は原本保存・該当店隔離、推測パースなし。欠落は別キュー。予算不足は正常な中断として保存し次の承認済み予算枠へ。ストレージ不足・DB整合性異常は全停止。ログに資格情報を載せない。
ログ：run_id、store、mode、start/end、許可参照、リクエスト消費、発見/取得/ユニーク商品/variant/更新/欠落/保留、最終成功日時、エラー原因、次回再開位置、出力hash、exit status。JSONL＋短いsummary.json。毎回自動レポート生成、異常のみ通知可能な既存手段で。AIの常時監視不要。トークン削減は実行時のLLM呼出し0を測定、保守工数は別に計測。
定期化：手動実行合格後、macOS launchd LaunchAgent StartCalendarIntervalで週2回の在庫確認（例火・金午前2時JST、オーナー決定待ち）、新規商品発掘は別の許可済み周期・予算。実行中のアイドルスリープ抑制はcaffeinate等を環境確認後使用。電源OFFでは実行不能、sleep時のcalendar jobはwake後起動。ログイン状態、タイムゾーン、重複/未完了処理、電源条件を検証。無断で電源設定やシステム更新を変更しない。Apple公式 https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/ScheduledJobs.html 。定期起動のために魔王を起こさない。

## 合格条件（最重要）
段階1：既存保存データで手動START1回。少なくとも実績ある1店から実商品・variantを読み、SQLiteに保存・出力、値と原本を照合。これはオフライン合格のみ。
段階2：利用許可済み1店を手動START1回、実際の現行商品とサイズ価格/在庫を取得しSQLite・出力の読み戻し確認。許可なしならライブ合格は未達。ダミー・固定候補・保存済みデータ再移行を新規収集と称さない。LLM呼出し0、操作追加なし、完了ログ。
段階3：途中停止→再開、DONE重複なし、予算永続、原本・既知値保持、異常店の隔離と次店継続、欠落検出・出力ゲート、二重起動防止を実測。実商品データを使う。正常店を止めない。無断公開なし。
段階4：他の許可済み店を順次追加。手動で一連の実行が完了してからlaunchdを入れ、実際のスケジュール起動とsleep/wake後の挙動・ログを確認。既存サイト/注文DBを変更しない。
最初の対象は実績あるShopify系1店（許可ありならShoe Palace、なければ別の許可済み店）。Museは実コードとローカル環境特定・初回実行、Claudeは薄いラッパーと最小差分、GPTはコード/結果監査、GLMは独立レビュー。長い設計や全面再開発を先行させない。許可済みライブ経路がなければ公式データ提供を取得することが唯一のライブ実行前提。
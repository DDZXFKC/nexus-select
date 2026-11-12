# サイト全体受け入れ確認レポート — 2026-11-13（Muse）

基準：`docs/site-wide-acceptance-runbook-2026-11-13.md`（コミット ba58ff76）。基準は「購入者が商品を探してから注文完了まで一連の操作に問題がないか」。
環境：Local（kaitsuke-shop.local）のみ、iMac の Safari のみ使用（Chrome は不使用）。本番・実決済・実仕入・発送・顧客向けメール送信・外部 webhook は行っていない。テスト注文は合成データ＋代金引換（オフライン決済）のみで、顧客向けメールは隔離し、変更した設定は全て復元した。

## 結論

必須機能項目は全て PASS。不具合3件（ギャラリー色切替、ホームの横はみ出し、ヘッダーの横はみ出し）は原因特定→修正→再検証→関連再確認まで完了した。
実機 iPhone での確認と実決済は環境制約のため未実施であり、合格には含めていない（「限界」参照）。

## ① 棚卸し・事前確認

- WP 7.1.4 / WooCommerce 11.2.1 / テーマ Nexus Select 0.8.0。パーマリンク /%postname%/
- プラグイン：custom-order-statuses-woocommerce、nexus-order-tracker、okuricart、vanquish-attach-me-for-woocommerce、woo-advanced-shipment-tracking、woocommerce、wpforms-lite
- 公開商品199件（全て variable）、多色商品56件
- ブランド pa_brand：nike 106、asics 42、jordan 27、patta 5、adidas 4、new-balance 4、carhartt-wip 2、li-ning 2、vans 2、ewing-athletics 1、on 1、timberland 1。アーカイブ /brand/<slug>/ と /brands/ ページのリンクは一致
- カテゴリ：mens 149、womens 48、kids 0、mens-sneakers 143、womens-sneakers 48、mens-jacket 4、mens-tshirt 1、mens-hoodie 1
- 決済ゲートウェイは全て無効（bacs/cheque/cod）。配送ゾーン「日本」→ free_shipping 有効。通貨 JPY、ゲストチェックアウト可、税は税別表示・税率未設定
- サイズガイド（商品メタ `_nexus_size_guide_html`）：196/199件に設定あり。無いのは 14697（テスト用）、14577（テスト用）、8484（Patta x Carhartt WIP Tシャツ）
- テスト商品：Timberland 18788（26バリエーション、全て¥52,700、Wheat US15.0=variation 18801 のみ在庫切れ）、Patta x Nike Air Max 1 18743（全44バリエーション在庫切れ）、adidas Anthony Edwards 3 18815（58中22在庫切れ）

## ② 検索・ブランド・カテゴリ一覧（Safari 574px）— 全て PASS

| テスト | 期待 | 実際 | 判定 |
|---|---|---|---|
| 検索「Timberland」 | 該当商品へ遷移 | 1件のため商品ページへ直接遷移 | PASS |
| 検索「timberland」（小文字） | 大文字小文字を区別しない | 同じく直接遷移 | PASS |
| 検索「Air Max」 | 部分一致の一覧 | 19件、16件/ページ、ページネーション・ソートあり | PASS |
| 検索「ブーツ」（日本語） | 日本語検索が機能 | 2件（Timberland、Nike Air Max Goadome） | PASS |
| 検索「zzzzqqq」 | 該当なし表示 | 専用メッセージ「選択に一致する商品が見つかりませんでした。」 | PASS |
| 空検索 | エラーなく一覧表示 | 全件一覧197件を表示 | PASS |
| 特殊文字「<script>alert」 | 安全に処理 | 該当なし表示、実行されず | PASS |
| 型番「10061」 | 型番でも検索可能 | Timberland 商品へ直接遷移 | PASS |
| /brand/nike/ | 棚卸しと一致 | 106件、/page/2/ は17〜32件目 | PASS |
| /brands/ ページ | ブランドと件数 | 全ブランドを件数つきで表示 | PASS |
| カテゴリ mens/womens/kids | 件数と空状態 | mens 149件、womens 48件（ヘッダーリンク実クリックで確認）、kids 0件で空状態メッセージ | PASS |
| ソート ?orderby=price | 価格昇順 | 最安¥17,500帯が先頭 | PASS |

観察：一覧・検索の総数は197件で公開199件と2件差。テスト用2商品（14697/14577）が表示対象外設定のためとみられ、機能不良ではない。

## ③ サイズガイド — PASS

- Timberland 18788：SIZE GUIDE の開閉が動作し、US/UK/EU/足長(cm) の表（US7.5〜15）が 574px でも崩れず表示
- ガイド無し商品 8484：SIZE GUIDE 自体が表示されない（未入力なら何も出さない設計どおり）
- 記録事項（表示機能の不具合ではない）：ガイド内に出典 URL を含むものは0件、出典の文言があるのは4件のみ。出典 URL・確認日の記録はデータ側の改善点

## ④ 商品ページ（ギャラリー修正の回帰含む）— 全て PASS

対象：Timberland 18788、Patta x Nike Air Max 1 18743。viewport は Safari 574px。

- 色のみ Black → ギャラリーが Black 画像のみに切替（スクショ確認）。色のみ Wheat → Wheat 画像に切替
- Wheat + US 15.0（在庫切れ 18801）→ 「在庫切れ」表示。Wheat + US 8.0 → 在庫切れ表示が消え価格 ¥52,700 のまま
- クリア → 色・サイズ両方リセット＋リセット案内文を表示
- 未選択でカゴ追加 → アラートで阻止され追加されない
- Patta 18743：White/Hyper Crimson + US 9.0 → 「在庫切れ」（全バリエーション在庫切れと一致）
- 観察：サイズ選択のたびにページ上部へ自動スクロールする。許容範囲だが記録する

## ⑤ カート — 全て PASS

- 開始時点：Air Jordan 1 Mid（Light Smoke Grey/Black/White・US 10.0）×2 = ¥66,400、送料無料、ヘッダー BAG (2) と一致
- 数量変更：+ で3（¥99,600）、− で2（¥66,400）に即時反映
- 同一バリエーション再追加：別行にならず数量3に統合（¥99,600）
- 別バリエーション追加（Black/Palomino/University Red/Phantom・US 9.0）：別行 ×1 ¥33,200、合計 ¥132,800
- 別商品追加（Timberland Wheat US 8.0）：3行目、合計 ¥185,500、BAG (5)
- 再読込で全行・合計を保持。行削除でその場に合計が更新（185,500→132,800→99,600→空）
- 空カート：「現在お買い物カゴには何も入っていません。」＋閲覧リンク＋おすすめ表示。再読込で BAG (0)
- 観察：ヘッダーの BAG バッジはページ読み込み時に更新される（カート内金額は即時更新）。戻る操作で POST 済みページに戻ると Safari の再送信ダイアログが出るが、キャンセルで状態は壊れない（標準動作）

## ⑥ チェックアウト（隔離つきテスト注文）— 全て PASS

隔離：顧客向けメール8種（failed/on-hold/processing/completed/refunded/note/new-account/verify-email）を一時停止し、COD（代金引換）を一時有効化。実施前の設定は `/Users/discodadz/nexus-run/checkout-state-backup.json` に保存し、復元後の設定ダンプが実施前とバイト単位で一致（1,659バイト）することを確認済み。管理者メールは自店用 Gmail（kaitsuke.shop@gmail.com）のみ。

- 表示：注文概要 ¥52,700、商品・バリエーション（Wheat/US 8.0）・小計・送料無料・合計がカートと一致
- 空送信：項目別エラー（姓/名/セイ/メイ/郵便番号/市区町村/住所）。注文は作られない
- 形式エラー：メール「invalid-email」→「有効なメールアドレスを入力してください」。郵便番号「123」→「正しい郵便番号を入力してください」。注文は作られない
- 注文確定：テスト注文 **18914**（合成データ、acceptance-test@example.com、代金引換）。確認画面に注文番号・日付 2026-11-13・合計 ¥52,700・決済方法・商品内訳・送料無料が表示され、注文追跡の進捗表示「ご注文を受け付けました」も表示。注文後にカートは空
- DB 照合（wc_get_order）：status=processing、total/subtotal=52700、送料0、税0、payment=cod、postcode は 611-0011 に整形、state=JP26、city=宇治市、address1=テスト1-2-3。重複注文なし。注文メモは管理者向け「新規注文」メールのみで、顧客向けメールの送信記録なし（隔離が機能）
- 観察：(1) 郵便番号から都道府県が京都府（JP26）へ自動補正された。(2) 市区町村欄の「宇治市五ケ庄」は city=宇治市 として保存され、「五ケ庄」は住所欄に残らなかった。町名は住所欄に書く前提の可能性があり、入力案内の観点で要観察。(3) 注文はカスタマーID 4（過去のテストセッション）に紐付いたため、完全なゲスト購入の再現ではない。(4) 税額0は税率未設定・税別表示どおり

## ⑦ 画面幅・reduced motion・キーボード — PASS（不具合2件を修正）

計測：iframe 幅 320/360/390/430/574/768/1024/1280/1440 で document の scrollWidth と clientWidth を比較。

### 修正前の計測
- ホーム：320〜430px で横はみ出し（320→406、360→426、390→441、430→461）
- 商品ページ：320/360→440、390/430→514 の横はみ出し。574px 以上は両ページとも正常

### 不具合 A（ホーム）
- 原因：FEATURED DROPS の商品 10623「J Balvin × Air Jordan 4 Retro OG SP "Amazonas"（Lemonade/Lemonade）」のタイトル内 `"Amazonas"（Lemonade/Lemonade）` が空白のない約240pxの塊で折り返せず、カード（156px）からはみ出していた。タイトル自体は正当なデータのため CSS で修正
- 修正：テーマ style.css 末尾に `.woocommerce ul.products li.product .woocommerce-loop-product__title { overflow-wrap: anywhere; }` を追加（マーカー `nx-title-wrap-fix`、追加のみ・適用1回を確認）
- 再検証：当該セクション 324/324 に正常化。ホーム全9幅ではみ出しなし

### 不具合 B（v08 ヘッダー、全ページ共通）
- 原因：閉じた状態のドロップダウンパネル `.nx-dd__panel`（position:absolute、幅200px、visibility:hidden）が画面外にあり、非表示でもスクロール領域を広げていた（360px 時 WOMEN'S パネルが 240..440）。header/body/html とも overflow-x は visible
- 修正：style.css 末尾に `.nexus-v08-header { overflow-x: clip; }` を追加（マーカー `nx-nav-overflow-fix`）。computed style で overflowY=visible の維持を確認し、パネル自体のルールには触れていない
- 再検証：商品ページ全9幅ではみ出しなし。ホームも再計測してはみ出しなし（回帰なし）
- 回帰確認（ドロップダウン）：実タブ 574px で MEN'S にフォーカスするとパネルが開き（:focus-within）、項目がヘッダー下に完全に表示されることをスクショで確認。clip による欠けなし
- 観察：360px では MEN'S パネルが 187..387、WOMEN'S が 240..440 の位置にあり、開いた際に右側が画面外になる（横スクロールは発生しない）。リンク文字は左寄せで実用の支障は小さいが、右端寄せへの調整はデザイン判断として申し送る。KIDS パネルは折り返し2行目で 18..218 に収まる

### reduced motion
- macOS「視差効果を減らす」を一時オンにして計測。matchMedia `(prefers-reduced-motion: reduce)` = true で、表示中のヒーロー動画が paused のまま進まない（t=0.00）ことを確認。オフに戻すと再生が再開（t が進行）。OS 設定は元のオフへ復元済み。ベースライン（オフ時）は動画が再生・進行

### キーボード操作
- ヘッダーのリンクは Tab で到達可能。MEN'S にフォーカスするとドロップダウンが開き、サブメニュー項目が Tab 順序に入る
- 色スウォッチは実 <button> でフォーカス可能。実タブで Black にフォーカス→Space で選択され、チェック状態とギャラリーの Black 画像への切替をスクショで確認
- サイズはチェックボックス入力、数量ステッパーと「お買い物カゴに追加」ボタンもフォーカス可能

### モバイルホームのブランドロゴ（欠陥3の残件）
- 320px のホーム下部 SHOP BY BRAND をスクショで確認。全12ブランドのロゴが2列グリッドで表示され、件数も棚卸しと一致（Nike 106、ASICS 42、Jordan 27、Patta 5、adidas 4、New Balance 4、Carhartt WIP 2、Vans 2、LI-NING 2、Timberland 1、On 1、Ewing 1）。DOM 側でも `.nexus-v08-brands` 内にロゴ画像12点を確認。テキストリンク表示への退行なし
- 観察：ホームには PC 用ブランドインデックス（ロゴ8点）と v08 ブランドグリッド（12点）の両方が DOM にあり、幅で表示が切り替わる

## 発見した不具合と修正（本日の変更ファイル）

| # | 不具合 | 修正 | ファイル |
|---|---|---|---|
| 1 | 商品ページで色だけの変更ではギャラリーが切り替わらない（欠陥2） | mu-plugin の bind() 内 CM2 ブロックをフォーム委譲（change/click）に書き換え。初期表示の絞り込みは維持 | `wp-content/mu-plugins/nexus-variation-gallery.php` |
| 2 | 次の画像が右端に覗く（欠陥1、本日以前に対応済み・④で回帰確認） | style.css のギャラリー gap 8px→0、flex 88%→100% | `wp-content/themes/nexus-select/style.css` |
| 3 | モバイルホームのブランドがテキストリンク（欠陥3、本日以前に対応済み・⑦で最終確認） | ロゴ表示へ変更 | テーマ front-page.php ほか |
| 4 | ホームの横はみ出し（長い商品タイトル） | ルールを末尾に追加（nx-title-wrap-fix） | style.css（43,107バイト、修正前 42,724バイト） |
| 5 | 商品ページ等の横はみ出し（隠れたドロップダウンパネル） | ルールを末尾に追加（nx-nav-overflow-fix） | style.css（同上） |

バックアップ：#1 は `/Users/discodadz/nexus-run/theme-backup-2026-11-13-galleryfix/`、#4・#5 は `/Users/discodadz/nexus-run/theme-backup-2026-11-13-titlefix/style.css`（42,724バイト＝両修正の適用前）。style.css の変更はいずれも末尾への追加のみで、既存ルールの書き換えはない（#2 を除く）。

## 後片付け

- サイト直下に置いた検証用ハーネス nx-*.php 37件と nx-inv1-list.tsv 1件を iMac のゴミ箱へ移動（復元可能）
- nexus-run 配下の診断出力31件をゴミ箱へ移動。バックアップ類（theme-backup-*、checkout-state-backup.json）と収集系の成果物は残置
- 後片付け後にホームの正常表示を確認済み

## 限界（合格に含めていないもの）

- 実機 iPhone での確認：Live Link（lyrical-tooth.localsite.io）が全パス404で復旧せず未実施。画面幅の確認は iframe 計測と Safari 実表示で代替した
- 実決済：ゲートウェイは全て無効のままで、検証は代金引換（オフライン）で実施。オンライン決済（KOMOJU 等）の実フローは未検証
- ゲスト購入：テスト注文は過去のテストセッション（カスタマーID 4）に紐付いた。設定上ゲストチェックアウトは有効だが、完全な未ログイン状態での注文再現はしていない
- ホーム素材：本番用メイン動画は未制作（現行は参考写真スライドショーの仮動画）。AI 制作素材への差し替え判断も未了。これはホームの「完成」宣言とは分けて扱う

## 申し送り（残課題）

1. 狭幅（〜430px）で MEN'S / WOMEN'S のドロップダウンパネル右側が画面外に出る件：右端寄せへの調整はデザイン判断としてチャッピー側で検討してほしい
2. サイズガイドの出典 URL・確認日の記録（データ側の改善）
3. 市区町村欄で町名（五ケ庄）が保存されなかった件：入力案内文の追加要否
4. サイズ選択時のページ上部への自動スクロール：仕様として許容するか確認

## ホーム完成について（2026-11-12 レポートの補足）

`docs/website-home-completion-report-2026-11-12.md` 時点で未完了だった項目の現況：ヒーロー動画は設置済みで、reduced motion 時の停止と通常時の再生を本日確認した。モバイル承認ロゴ（Brush Italic）は設置済み。ブランドロゴは ⑦ で最終確認済み。本番用メイン動画の制作と AI 素材への差し替え判断は引き続き未了であり、ホームを「完成」と宣言するかどうかは素材の確定後に判断する。

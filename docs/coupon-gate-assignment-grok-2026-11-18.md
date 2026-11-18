# Grok担当：クーポン入口ゲート実装（2026-11-18 オーナー決定）

オーナーが本日、入口ゲートの実装をGrokへ分担すると決定した。GLM担当分（A/B/C軸の修正）は現行ファイルに反映済みで、旧テスト33件は合格している。残る最優先がこの入口ゲート。

## 読むもの（このリポジトリ内）
- 原則：docs/owner-layered-filtering-development-principle-2026-11-18.md
- 再監査（入口ゲート最優先の指示）：docs/coupon-reaudit-round2-gpt-result-2026-11-18.md
- オーナールール：docs/owner-rule-check-own-assets-first-2026-11-18.md
- 対象ファイル：collector/coupon_bridge.py（このコミットの版が現行・正）

## 実装仕様
1. L0 対象店舗レジストリ：対象は「AFTER HOURS CLUB 商品管理」シートの収集サマリー等に記録されている取引・収集店舗。shop_code は既存の store_slug 表記に合わせる：bstn / foot-locker / notre-shop / converse / shoe-palace / shiekh。
2. レジストリはコード内定数にせず、CouponBridge が外から受け取る形（コンストラクタ引数または設定）にする。対象店舗の増減は記録側の更新で対応できるようにする。
3. 空のレジストリで全許可にフォールバックしない。空なら全件拒否。
4. ゲート位置は保存の前：record_discovery / record_raw で対象外 shop_code を ValueError で拒否し、DBへ保存しない。対象外クーポンが A/B/C 判定・実測へ進まないこと。
5. 既存の価格ゲート（select / record_check の処理本体）には触らない。

## テスト（新規追加分を提示）
- 対象外店舗の discovery が保存されないこと
- 対象店舗は従来どおり保存・候補化できること
- 空レジストリで全件拒否になること

## 出力方法
Grok はこのリポジトリへ push できないため、変更したセクションの全文（または unified diff）と新規テストをチャットで返すこと。適用と検証は魔王ちゃんが行う。

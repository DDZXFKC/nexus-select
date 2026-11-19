# SP158 色スウォッチ Local apply 実施報告（Stage H 残差検証＋Stage I apply）

- 実施: 魔王ちゃん（実行担当）
- 日時: 2026-11-19
- 前提: GPT 判定「正式 dry-run 合格、SP158 一括 apply は条件付き承認。fixture 残差7件を完了し、問題がなければ再度の承認を待たずに apply へ進んでよい」
- 結論: **残差7件は全件合格し、SP158 の Local 一括 apply は完了した。追加は指定 meta 2種類×158件＝316キーのみで、対象外の変更は0件。**

## Stage H: fixture 残差7件の検証（全件合格）

残差専用の隔離 fixture を新規作成して検証した（run_id `fx-20261119095559-plqIzW`、親 ID 21442 / 21447 / 21452 / 21457、各4バリエーション、draft・hidden）。writer apply は written=4、readback_mismatch=0、other_fields_changed=0。

1. **21402 White/Black（白黒2等分と白色の視認性）: 合格**
   21442 の実画面で丸窓が左白・右黒の縦2等分で表示された。白半分は細い灰色の輪郭により白背景上でも視認できた。
2. **21417 Black/Black（同色反復の保持）: 合格**
   readback で components に Black が2要素保持されていた（`[{"name":"Black","hex":"#171717"},{"name":"Black","hex":"#171717"}]`）。実画面は黒一色の丸＋原文「Black/Black」。
3. **21422 UNKNOWN（中立表示・原文保持）: 合格**
   21452 の実画面で白地＋灰色点線の丸（中立表示）＋原文「Pink/Rock Rose」が表示された。
4. **21437 構成色なし（不要な丸窓を出さない）: 合格**
   21457 の実画面で「カラー」ラベルの横に丸もテキストも何も表示されなかった（仕様どおり）。Claude 側の未確認点だった 21437 と同型ケースの視覚確認にもなった。
5. **直接 POST でも購入拒否: 合格（範囲を明記）**
   検証方法は、UI を経由せずサーバー側フックを直接叩くアプリ層の直接呼び出しである（HTTP の生 POST ではない）。結果: `parent_is_purchasable=false`、`variation_is_purchasable=false`、`add_to_cart_validation=false`、`cart_add_result=false`、`cart_contents_count=0`、購入不可のエラー通知2件。guard（mu-plugins/ahc-fixture-guard.php）は `woocommerce_is_purchasable` / `woocommerce_variation_is_purchasable` / `woocommerce_add_to_cart_validation` / カート内 fixture 除去をサーバー側で実装しており、wc-ajax やフォーム POST も同じフックを通る。
6. **コンソール JS エラー0件: 合格（対象ページを明記）**
   Safari の JavaScript コンソールを開いた状態で、21457 の再読み込みと 21442 への遷移の両方を確認し、JS エラーは0件だった。表示されたのは AdGuard 拡張機能のログと JQMIGRATE のログのみ。
7. **サイズ切替（価格・在庫・画像の既存動作維持）: 合格**
   21442 で US 5Y (25cm) を選択し、選択状態が切り替わり、表示 SKU が親の FX-SP-4631211606062 からバリエーションの FX-SP-4631211606062-3 へ更新され、「オプションをクリア」が出た。価格・在庫注記も正常。

### teardown（省略不可分）
- writer rollback: restored=4、readback_mismatch=0
- fixture remove: 親4件・子16件を削除。再 dry-run は 0/0（冪等）
- inventory after が作業前と**バイト単位で一致**（COUNT=11,324、md5 `4064448c8f46ec597cd5426335da0faf`）
- 注文件数は不変（wc_orders=13、適用前後とも同じ計数方法）

## Stage I: SP158 一括 apply（GPT 条件への適合）

1. **適用直前の DB バックアップ**: `db-before-sp158-apply.sql`（44,783,286 bytes、iMac `~/ahc-swatch-check/`）を取得。
2. **再照合**: probe の事前値が Stage G 正式 dry-run 時と完全一致（parents=158、variations=1,713、meta_rows=37,572、postmeta_dump_md5=`2940888418a57a441155094e98700518`、comp/ctx holders=0/0）。
3. **先行適用（pilot）**: 代表3件に先に適用した。
   - SP-4631411785774（Chestnut Brown、CONFIRMED）
   - SP-7669318451406（Black/Black、CONFIRMED）
   - SP-8845462929614（Archive Marshmallow、UNKNOWN）
   結果: written=3、readback_mismatch=0、other_fields_changed=0。実商品ページ（Bondi 7）で黒一色の丸＋原文表示を実画面で確認してから残りへ進んだ。
4. **本適用**: planned=158、unchanged=3（pilot 分）、written=155、readback_mismatch=0、other_fields_changed=0。backup は `writer_backup_sp158.json`。
5. **追加は316キーのみ**: probe 前後の postmeta ダンプ差分は、追加316行のみ（`_ahc_color_components` 158行＋`_ahc_color_components_context` 158行）、削除0行、対象外キー0行。meta_rows は 37,572 → 37,888、holders は 158/158。
6. **再 dry-run**: unchanged=158 / would_write=0。
7. **実商品ページ検証**:
   - PC: SP-7669318451406（黒一色の丸）、SP-7607088545998 White/Black（左白・右黒の縦2等分。白は輪郭で視認可）、SP-7719431635150 Black/White/Grey（黒・白・灰の縦3等分）、SP-8845462929614 UNKNOWN（白地＋灰色点線の丸）
   - スマホ（Safari レスポンシブデザインモード 430×852）: SP-8845462929614 で点線丸＋原文が正常表示され、レイアウトの崩れはなかった
8. **rollback**: 異常がなかったため未実施。total_products=619 は不変、注文件数（wc_orders=13）も不変。

## 結論

SP158 の Local 反映は完了し、色スウォッチが実商品158件で表示開始された。GPT の apply 条件8項目はすべて満たした。

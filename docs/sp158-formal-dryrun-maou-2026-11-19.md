# SP158 正式dry-run 実施報告（魔王ちゃん）

GPT検収文書（swatch-fixture-local-qa-gpt-acceptance-2026-11-19 / b9557ce8）の指定に基づく正式dry-run。全行manifestを添付する（docs/sp158-formal-dryrun-manifest-2026-11-19.csv）。**一括applyはGPT判定まで禁止を維持。本報告はdry-runのみで、書き込みは行っていない。**

実施: 2026-11-19 18:42 JST、Local（kaitsuke-shop.local、iMac）、単一writer = ahc_color_components_to_woo.php（Stage C/F と同一ツール）。

## 結果サマリー
- writer dry-run: `{"planned":158,"unchanged":0,"would_write":158,"written":0}`、終了コード0、PLAN行158件（全件manifestに転記）
- 実行前後の読み取りプローブ（対象158親＋バリエーション1,713件の全postmetaダンプ）が完全一致し、dry-runが何も書かなかったことを実証:
  - parents_found=158 / variations_found=1,713 / meta_rows=37,572 / total_products=619
  - postmeta_dump_md5 = 2940888418a57a441155094e98700518（前後同一）
  - このダンプには価格・在庫・画像・サイズを含む対象全metaが入るため、変更対象外データの保護も同値で確認できる
- 既存meta差分: 対象158件は全件 `_ahc_color_components` / `_ahc_color_components_context` を未保持（holders=0/0）。apply時は全件が新規追加（旧値＝不在）になる

## manifest の全行確認（158件）
- shop=SP / market=US は全行一致（CSV 228構成色行すべて SP・US）
- mapping（supplier_product_id, market, parent_sku）・allowlist・Local実在SKU（SP-<id>）の3集合が完全一致。重複0、対象外0、全件 publish
- カラーウェイは全件単一（colorway_original が商品内で複数になる例0、supplier_color_key も単一）
- 商品単位の状態: CONFIRMED 139 / UNKNOWN 17 / HOLD 2（構成色単位では CONFIRMED 196 / UNKNOWN 30 / HOLD 2）
- 構成色数: 1色92件 / 2色62件 / 3色4件、合計228
- HEX規律: CONFIRMED は全構成色に承認HEXあり（null混入0）。UNKNOWN・HOLD は全構成色 hex=null（混入0）。同色反復（Black/Black 等）も重複保持で計画されている

## バックアップとテーマのハッシュ
- 適用直前想定の完全DBスナップショットを今回新規取得: iMac `~/ahc-swatch-check/db-before-sp158-formal.sql`（44,750,690 bytes）
- Local現行テーマと GitHub 正本（local-snapshot-2026-11-15）の md5 が全ファイル一致:
  - theme/functions.php 031be6cccc0af38a154d17d7161cfbf7
  - theme/main.js 4b736d99ce08bdd64a791b17fc039af3
  - theme/style.css 67e4be36a7dc0cf872ee3c3b8fa42555
  - mu-plugins/nexus-variation-gallery.php 4f6602c773da1344000556c28c56f665
  - （参考）mu-plugins/ahc-fixture-guard.php（Local側のみの検証用）8d1252a4456e6d194b6090e1bdee2a35

## apply時の計画（GPT判定後に実施する手順）
1. 適用直前に完全DBスナップショットを再取得し、writer の backup ファイル（排他作成）を必須とする
2. 単一writer（ahc_color_components_to_woo.php の apply）のみで書き込む。他経路の書き込みはしない
3. 書き込み後は全件 readback 照合（Stage C と同じ方式、mismatch=0 を合格条件）
4. 再dry-runで unchanged=158 / would_write=0 を確認する
5. 異常時は backup から rollback（CAS相当の旧値照合付き。Stage E で2回実施・冪等を確認済み）

## fixture残差の既存証拠での照合（GPT指定分）
- 指定9件と実fixture 9件の対応: manifest（run_id fx-20261119083406-3RanZV）どおり全件一致（Stage B 記録）
- 画面証拠あり: 1色（21397）/ 3色（21407、PC・430px両方）/ 4色→先頭3色（21412）/ UNKNOWN点線丸（21427）/ HOLD点線丸（21432）。UNKNOWN・HOLD の中立表示は 57a52aec で訂正済みのとおり仕様どおり
- **不足（既存証拠にないもの）**: 2色 White/Black（21402）、同色反復 Black/Black（21417）、UNKNOWN Pink/Rock Rose（21422）の画面証拠。構成色なし（21437）の画像確認。カート拒否はUI経路のみで、guard への直接POSTの証拠。コンソールエラーの記録
- 不足分は、必要と判断されれば隔離fixtureの最小ケースだけ再検証する（成功済みの作成・削除・rollback の全反復はしない）

以上。GPTの判定（apply可否と残差の扱い）を待つ。

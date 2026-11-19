# GPT設計決定：Local丸窓接続（3f1e0ae5 / 420a82c5）
現状619 variable、SP158全てpa_colorなし、MERGED58/PROTO2のみ色variation、メタ0、描画未実装。停止妥当。Claude担当は実装、MuseはLocal実行。オーナー追加承認不要（Localのみ、公開禁止）。
## 1. 取り込みと突合
新規SP取り込みは原文colorwayをpa_colorの表示属性として付与（単一colorwayはvariation=false、サイズvariationのID/属性/価格/在庫を維持）。色不明は属性を捏造しない。複数colorwayを統合する場合だけ既存のpa_color variationを使い、各仕入先product/color keyとWoo親ID・term slug・variation IDの明示対応表を作る。タイトル末尾・HEX・色名の類似で突合禁止。
既存SP158はまず属性変更なしで親SKU SP-<supplier_product_id>とシートのshop+market+pid+singleを一意照合し、親商品メタを付けられるようwriter修正。marketは実データで確認しSKUが複数marketに対応する場合停止。既存158の属性追加は別dry-runで差分確認後に実行、サイズvariationは変更しない。MERGED/PROTO/FL/CVは今回書き込み対象外、既存色対応表が確認できるまで旧表示を維持。
## 2. データ契約
既存 _ahc_color_components のslug→配列形式は互換維持。新規の単一色・属性なしは予約キー __single__ に配列を格納（実term slugと衝突禁止）。単一表示属性も同キーで扱う。別メタ _ahc_color_components_context に schema_version=2, shop_code, market, supplier_product_id, supplier_color_key, colorway_original, swatch_status を格納。将来の複数色はslug単位contextを別途設計。全原文と順序・反復を保持。position0は空配列、UNKNOWN/HOLD/DRAFTは全て中立表示。メタなしと明示空配列を区別。HOLD/UNKNOWN/DRAFTは旧画像/パレットへfallback禁止。既存未移行商品だけ旧方式を維持。
exporterにmarket/colorway_original追加、statusを厳格検証。現行exporterはDRAFTで先頭3以外が未承認の場合などを含め明示statusをwriterが無視するため、status=CONFIRMED以外はHEX全空に統一。writerは完全な事前検証後のみapply。CSV列数、厳密整数position、重複marker、marker混在、非single、status/原文/market不一致、重複SKU/親ID、非対象shop、異常HEXを検出。行エラーを出しながら部分applyしない。allowlist必須（初回fixtureのみ）。Local host検査に加え対象サイト確認、バックアップ・readback・rollback・再実行差分0。旧メタ以外の価格/在庫/画像/variation/属性差分0。not_foundは全シート対Local差であり障害ではない。
## 3. 描画
Claudeが現行LocalテーマとGitHub差分を先に取得・比較（main.jsサイズ差あり）。PHPで安全なJSONを商品ページに渡し、JS/CSSで丸窓の1〜3等幅縦分割。CONFIRMEDかつ先頭min(3,n)全HEX有効のみ着色。単一色は非操作の丸窓＋原文表示（サイズ選択を妨げない）。複数色は既存selectと連動し、選択状態・キーボード・aria-labelを維持。4色以上も全原文表示。中立は白地灰点線、白色確定は実線境界で区別。メタなし旧方式は移行対象外のみ。既存画像ギャラリー/型番/価格/在庫/サイズイベントを変更しない。mu-pluginはデータ供給に利用可、見た目はテーマ担当。
## 4. QA
まず158のシート突合結果から実在する確認商品を選定。観点不足なら既存商品を変更せず、実データから9件をLocal下書きfixtureとして隔離取り込み（実SKU重複禁止、購入不可、必要ならfixture専用識別と明示mapping）。9件は1/2/3/4+、反復、UNKNOWN、特殊、HOLD、構成なし。単一色は画像切替不要、サイズ変更で価格/在庫連動を確認。複数色連動はMERGEDの複製下書きに検証済み対応表を用いて別fixture（本物の色選択・画像・型番・サイズ・価格・在庫）。9件の元データの現行statusを再確認し必要なら差し替え。PC/モバイル幅、実機は可能時、コンソール、スクショ、負例、再実行を証拠化。fixtureだけapply→描画検証→158対象dry-run→GPT検収→Local一括。公開/本番なし。
## 担当
Claude: exporter/writer/テーマ実装とテストをGitHubへ。Muse: Local snapshot共有、fixture実行、証拠登録。GPT: 差分監査。現時点でコード変更・Local実行は未実施。
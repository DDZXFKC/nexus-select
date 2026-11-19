# 隔離fixture実機検証 結果報告（2026-11-19、実行: 魔王ちゃん）

承認: GPT最終確認 7bf74dd1（CONDITIONAL PASS）に基づき、Local（kaitsuke-shop.local）の隔離fixture 9件のみで実施。公開158件へのapply・本番・購入は行っていない。

## 前提・保護措置
- 完全DBスナップショット取得済み: iMac `~/ahc-swatch-check/db-before-fixture.sql`（44,487,886 bytes、復元は wp db import）。今回は復元不要だった。
- テーマは snapshot 版3ファイル（main.js / style.css / nexus-variation-gallery.php）を deploy。旧版は iMac `~/ahc-swatch-check/backup-theme-20261119/` に保存（md5照合済み）。snapshot版は検証後もLocalに残置（これが正）。
- 単一writer（魔王ちゃんのみ）。fixture guard（mu-plugin）有効。
- 注記: fixture 9件の「色データ」は実export。画像・価格・サイズはテンプレート商品 SP-4631411785774 の合成コピー。

## Stage B: fixture作成
- create dry-run: 9件 WOULD CREATE（各 variations=4）
- apply: 親9件（ID 21397, 21402, 21407, 21412, 21417, 21422, 21427, 21432, 21437）＋子36件を作成。run_id = fx-20261119083406-3RanZV、manifest = manifest_fx.json（format ahc-fixture-manifest-v2）
- 作成前後の全件差分照合: 削除・変更 0件、追加は fixture 45件のみ。親は全件 draft・marker付き、子は SKU・親とも manifest planned と完全一致。

## Stage C: writer（色コンポーネント書き込み）
- dry-run: would_write=9（CONFIRMED はHEX付き、UNKNOWN/HOLD は hex=null、構成色なしは空配列。同色反復 Black/Black は重複保持）
- apply: written=9、readback_mismatch=0、other_fields_changed=0。backup = writer_backup_fx.json
- 再dry-run: unchanged=9・would_write=0（冪等 OK）

## Stage F（先行実施）: SP158 仮mapping
- dry-run（allow_published=1 は計画専用）: planned=158・would_write=158・written=0・エラーなし。一括applyは未実施（別途判断）。

## Stage D: 実画面確認（wp-adminログインは Local の One-click admin で実行者が実施）
対象は下書きプレビュー。PC幅＋モバイル幅430pxで確認。
- FX-SP-4646574424110（3色CONFIRMED Black/Grey/Red）: 丸窓＝黒/灰/赤の縦3等分 ✅、カラー原文「Black/Grey/Red」表示 ✅、価格 ¥40,800 ✅、サイズボタン均一（US 3Y 23cm / 4Y 24cm / 5Y 25cm / 6Y 26cm、cm併記）✅、画像表示 ✅
- 購入拒否: サイズ選択→「お買い物カゴに追加」で guard のアラート「この商品は対応しておりません。異なる組み合わせを選択してください。」が表示され追加拒否 ✅。カート内は従来の実商品2点のみで fixture は入っていないことをカート画面で確認 ✅
- FX-SP-6854640107726（4色 Wheat/White/Pollen/Gum Light Brown）: 丸窓＝先頭3色（Wheat/White/Pollen）の縦3等分 ✅
- FX-SP-4631241949230（1色 Grey）: 単色グレーの丸窓 ✅
- FX-SP-4771571925198（UNKNOWN Multi/Yellow）: 丸窓なし・原文のみ ✅
- FX-SP-7236286218446（HOLD Yellow/Red）: 丸窓なし・原文のみ ✅
- 構成色なし（FX-SP-4631353360430）: 丸窓なし・カラー値なし ✅
- モバイル幅430px（3色品）: 1カラムで丸窓・サイズボタン・カゴボタンとも正常 ✅

## Stage E: rollback と remove
- writer rollback 1回目: posts=9・restored=9・readback_mismatch=0。全9件の meta（components/context）が空に戻ったことを読み戻しで確認
- writer rollback 2回目: restored=0・mismatch=0・エラーなし（冪等）✅
- remove dry-run: parents=9・children=36。全ID・SKU・親・run が manifest planned と一致（ツールの全件照合もエラーなし）
- remove apply: REMOVED parents=9 children=36。再dry-run: parents=0・children=0（残存なし・冪等）✅
- 最終照合: inventory（product＋variation 全件）が検証前とバイト単位で一致（MD5 d52773bfeb91d8a187026043852fd1db、diff 0行）。実商品の変更 0 ✅
- 注文: 新規作成 0。既存の注文は 2026-11-10〜11-14 のテスト注文8件のみで、本検証による増減なし ✅

## 結論
GPT条件（スナップショット確保・単一writer・全件差分照合・remove前の manifest 照合・成功時のみ remove・実商品変更0/注文0/fixture残存0）をすべて満たして完了。隔離fixtureでの丸窓描画・購入拒否・rollback・remove の一連が実機で動作することを確認した。
スクリーンショット証拠は魔王ちゃんのワークスペース `swatch-local-check/shots/` に保存（GitHub push はテキストのみのため未添付）。

## 残件
- SP158件への一括applyは未実施（本報告の検収後に別途判断）。
- テーマ snapshot 3ファイルは Local に deploy 済みのまま（正の状態）。

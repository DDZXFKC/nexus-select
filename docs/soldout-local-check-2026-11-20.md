# sold out表示 実機確認結果（2026-11-20、魔王ちゃん実施）

対象：Claudeの実装コミット 9f1a18d8（sold out表示：商品カード・商品ページ・サイズ表示）
環境：Local（iMac）kaitsuke-shop.local

## 結論
sold out表示はLocalでは未動作。理由は表示の不具合ではなく、**9f1a18d8 の実装がLocalテーマへ未反映**のため。

## 根拠
- Localテーマのファイルmd5が2026-11-19時点と完全同一（functions.php 031be6cc／main.js 4b736d99／style.css 67e4be36／mu-plugin gallery 4f6602c7）。
- テーマ・mu-plugins・plugins の全域で "sold" を含む実装コードはゼロ（plugins内のヒットはWooCommerce本体の sold_individually 等のみ）。

## 確認内容
- 全サイズ在庫切れの公開商品は実在した：id=18743「Patta x Nike Air Max 1 '87 "Waves"」（全44バリエーション在庫切れ）、id=8474「Patta x Carhartt WIP OG Active Jacket」（全6バリエーション在庫切れ）。読み取り専用プローブで確認、商品データは変更していない。
- (b) 商品ページ（id=18743、再読み込み後の画面）：SOLD OUTの文字・バッジは一切なし。サイズボタンは全て通常表示。カラー＋サイズ選択後に限り、WooCommerce標準の赤文字「在庫切れ」が出る（既存挙動）。
- (c) カート追加：カラーとサイズを選んで追加を押すとアラート「この商品は対応しておりません。異なる組み合わせを選択してください。」で阻止され、BAGは(0)のまま。購入ブロックは既存のバリエーション検証で機能しているが、SOLD OUT表示によるものではない。
- (a) 商品カードのバッジ：一覧画面の目視は未実施（同一Safariウィンドウで別作業が進行中だったため干渉回避）。ただし実装コードがLocalに無いため、バッジが描画され得ないことはファイル確認で確定している。

## Claudeへの依頼
9f1a18d8 の実装をLocalテーマへ反映してください。反映後、魔王ちゃんが (a)〜(c) を再確認します。

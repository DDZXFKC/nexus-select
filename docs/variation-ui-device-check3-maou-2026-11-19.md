# バリエーションUI 再検収結果（魔王ちゃん実機確認）

対象コミット：610e1d9（キッズサイズ順修正、Claude）＋ f7c0af18（修正5：フォールバックを色の丸へ変更・切り抜き確定後に画像表示）
前提コミット：644959bf（GPT検収・修正仕様）、6b51741c（魔王ちゃん実機確認2）
確認者：魔王ちゃん（Local／iMac Safari、2026-11-19）

## Localへの反映

- GitHub HEAD（610e1d9）の theme/main.js と theme/style.css を Local の nexus-select テーマへ反映した。
  - main.js：18,787 bytes、sha256 93803970d2ed38f6d1941c888b96c721a7cf31bbc2883b70da55968911e99467
  - style.css：47,537 bytes、sha256 3b485378767a4dd98df30fb0b630ef315ca4a414ba2ff70c739e2b75b8c0312b
  - 書き込みバイト数は取得元と一致。

## キッズサイズ順：合格

- Clifton 10 Preschool Running Shoes (Beige/Pink)、商品コード SP-7601046651086（前回不合格だった当該商品）
  - 表示順：US 10.5C (16cm) → US 11C (16.5cm) → US 11.5C (17cm) → US 12C (18cm) → US 12.5C (18.5cm) → US 13C (19cm) → US 13.5C (19cm) → US 1Y (19.5cm) → US 1.5Y (20cm) → US 2Y (20.5cm) → US 2.5Y (21cm) → US 3Y (21.5cm)
  - GPT指定の合格条件と完全一致。cm併記は保持されている。
- Clifton 10 Preschool Running Shoes (Black)、SP-7601467523278：同一の順序で合格。
- Vans Premium Old Skool 36 Grade School、SP-8808947646670
  - 表示順：US 3.5Y (21.5cm) → US 4Y (22cm) → US 4.5Y (22.5cm) → US 5Y (23cm) → US 5.5Y (23.5cm) → US 6Y (24cm) → US 6.5Y (24.5cm) → US 7Y (25cm)
  - GPT指定の合格条件と完全一致。
- スマホ幅（Safariレスポンシブデザインモード 393×852、Clifton Beige/Pink）：同一の順序・cm併記保持を確認。
- 選択と variation の整合（Clifton Beige/Pink）
  - US 11C を選択 → 商品コード表示が 20979934 になり「在庫切れ」表示。
  - US 12C を選択 → 商品コード表示が 20979936 になり、在庫切れ表示は出ない。
  - サイズごとに異なる variation が正しく引けている。

## 回帰確認：合格

- 大人サイズ（Air Jordan 1 Mid SE）：US 7.0 → 18.0 の昇順、サイズボタン均一。
- 大人サイズ（ASICS GEL-1130 Women's）：US 5.0 → 12.0 の昇順。
- アパレル（Patta x Carhartt WIP Hartt And Soul T-Shirt）：XS → S → M → L → XL → XXL の順序を維持。
- 色連動（Jordan 1 Mid SE）
  - Black/White/Dark Concord 選択時：「カラー：Black/White/Dark Concord ／ 型番：DV1308-004」。
  - Cargo Khaki/Total Orange/Black 選択時：「カラー：Cargo Khaki/Total Orange/Black ／ 型番：JA4150-325」。
  - その色で買えない US 13.5 は、Concord 選択時に選択肢へ出ない。

## 色見本（修正5適用後）：合格

- Jordan 1 Mid SE の3色：全て商品部分だけで埋まっている。Black/White と Cargo の下部に見える白・クリーム色の帯は、拡大確認で境界が鮮明な各色自身のミッドソール（製品部分）であり、背景ではない。
- GEL-1130 Women's の19色：全て靴の素材（メッシュ・ストライプ・ミッドソール）で埋まり、背景だけの丸はない。白中心の色も同様。

## 色別の商品説明の整合性：合格

- Jordan 1 Mid SE の説明文は商品共通の単一テキストで、Black/White/Dark Concord 選択時と Cargo Khaki 選択時で全文が一致することを確認した。説明文に色固有の記述は含まれていない。
- 色で変わる要素（型番・画像・価格・買えるサイズ）は全て選択中の色に連動しており、他色の情報の混在はない。

## console・表示速度（GEL-1130 Women's、Local環境）

- Webインスペクタのコンソールに、ページ側のエラー・警告はなし（表示されたのは自ら評価した計測コマンドとその結果のみ）。
- performance.timing：load 2696ms / DOMContentLoaded 2397ms（19色・画像多数の最重量ページ、Local開発環境での値）。

## 隔離fixture（専用画像がない色）：未実施（wp-adminログイン待ち）

- GPT指示の Local 隔離 fixture は未実施。理由：fixture 作成には Local の wp-admin ログインが必要だが、Safari は未ログインで、保存パスワードの自動入力でも埋まらなかった。ログインはオーナー本人の操作が必要なため、ここで中断した。本番へのテスト商品作成はしていない。
- コード上の根拠（610e1d9 の main.js で魔王ちゃんが確認）
  1. その色のサムネイルが無い場合、見本は colorBackground(swatchColors(label)) の色の丸になる。サムネイルは thumbs.images[option.value] で自色の分だけを参照し、他色の画像は引かない。
  2. 画像の読み込みに失敗した場合（img.onerror）も色の丸に戻る。
  3. 背景を含まない窓が取れない場合も、中央拡大ではなく色の丸に戻る（修正5）。
- wp-admin にログインできる状態になれば、fixture を作って実機確認する。

## 白服・透明・非白背景について

- 白い靴：GEL-1130 の白中心の色で確認済み（上記）。
- 白い服の複数色商品：確認した範囲の現行カタログに存在しない（Patta の白Tシャツは単色商品で、色見本自体が発生しない）。
- 透明・非白背景の商品画像：確認した範囲の現行カタログに存在しない。解析できない画像の受け皿は上記 3. の色の丸。

## GPT仕様（644959bf）との差異の申告

- Claude の実装は、並び替え時に末尾の括弧内に「CM」を含む部分を除去する形（半角・全角括弧対応）で、GPT仕様の「数値＋CM の厳密な括弧のみ除去」より範囲が広い。実在のキッズラベルは全て「 (数値cm)」形式で、今回の3商品では仕様通りの結果になった。厳密化するかどうかは GPT の判断に委ねる。

## 結論

- キッズサイズ順は GPT 指定の合格条件を満たした。他の再検収項目（回帰・色見本・説明の整合性・console）も合格。
- 残りは隔離 fixture の実機確認のみで、wp-admin ログイン待ち。
- GPT の最終検収をお願いする。これはサイトの公開承認ではない。

証跡（スクリーンショット等）は VM の ~/workspace/variation-check3/ に保管。

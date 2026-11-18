# バリエーションUI 残りの実機確認結果（魔王ちゃん、2026-11-19）

対象：GPT指示書 def2cb9b の未検収4項目＋回帰確認。確認は全て再読み込み後の実画面（Local、kaitsuke-shop.local）で行った。証跡スクリーンショットは魔王ちゃんのVM `~/workspace/variation-check2/` に保管（GitHubは画像登録不可のため文章で記録する）。

## 1. キッズサイズ順：不合格（要修正）

### 実測
- Premium Old Skool 36 Grade School（Vans、Yのみ）：表示順は **3.5Y → 4.5Y → 4Y → 5.5Y → 5Y → 6.5Y → 6Y → 7Y**。昇順になっていない（証跡 kids-vans-size-order.jpg）。
- Clifton 10 Preschool（C/Y混在）：表示順は **1.5Y → 10.5C → 11.5C → 11C → 12.5C → 12C → 13.5C → 13C → 1Y → 2.5Y → 2Y → 3Y**。C→Yの順にも、各グループ内の昇順にもなっていない（証跡 kids-clifton-size-order.jpg）。

### 原因（魔王ちゃんが main.js 修正4版で特定）
- `sizeSortKey` の正規表現が末尾アンカー付きで、キッズのラベルに付く **「 (21.5cm)」のcm併記サフィックス** を許容していない。
- そのためキッズは全ラベルが解析失敗 → キーが null → 仕様どおり「元のWooCommerce順を維持」になり、取り込み順のまま表示されている。
- 大人サイズはcm併記がないため解析でき、昇順ソートが効いている（Jordanで確認済み）。これはオーナー決定「キッズのサイズ表記はUS表記にcmを併記」（2026-11-16）と実装の不整合である。

### 修正依頼（担当：Claude）
- kids／plain 両パターンで末尾の「 (…cm)」サフィックスを許容する（または照合前に末尾の括弧書きを取り除く）。
- 修正後の合格条件：Clifton 10 Preschool で 10.5C → 11C → 11.5C → 12C → 12.5C → 13C → 13.5C → 1Y → 1.5Y → 2Y → 2.5Y → 3Y の順になること。Vans Grade School で 3.5Y → 4Y → 4.5Y → 5Y → 5.5Y → 6Y → 6.5Y → 7Y になること。

## 2. アパレルサイズ順：合格
- Patta x Carhartt WIP T-Shirt：**XS → S → M → L → XL → XXL** の順で表示（証跡 apparel-patta-size-order.jpg）。

## 3. スマホ表示：合格
- Safari レスポンシブデザインモード（iPhoneサイズ 393×852）で Air Jordan 1 Mid SE を確認。
- レイアウト崩れなし。色見本3色とも表示され、タップで選択リング＋「カラー Black/White/Dark Concord」の色名表示が出る。その色で買えない US 13.5 はグレー＋取り消し線。クリアも表示される（証跡 smartphone-jordan.jpg、smartphone-jordan-selected.jpg）。
- サイズボタンは均一グリッドで US 7.0 → 18.0 昇順。

## 4. 白い靴の色見本：合格
- ASICS GEL-1130 (Women's) 全19色（うち White/Brown、White/Navy、White/Silver、Grey/White/White 等の白中心が8色以上）の見本を拡大確認。全ての丸が靴の素材（メッシュとストライプ）で埋まり、写真の背景が入った丸は1つもなかった（証跡 gel1130-womens-full.jpg、gel1130-swatches-zoom.png）。
- 白い靴の内側の白が商品として残る設計（縁から続く白だけを背景とみなす）が、白中心の実商品でも機能している。

## 5. 専用画像がない色：該当事例なし（確認範囲）
- 確認した複数色商品（Jordan 1 Mid SE 3色、Jordan 1 Mid 2色、Jordan Spizike Low 2色、GEL-1130 Women's 19色）は全色に写真の見本があった。
- Shoe Palace 全店データでも、複数色グループの中で画像0件のカラーは存在しない（魔王ちゃんが raw JSON で全件確認）。サイトの複数色商品はこの範囲では「専用画像がない色」が発生しない。
- したがって受け皿（色の丸に戻す挙動）の実機確認は対象がなく実施できなかった。コード上の挙動はGPTのコード監査（修正1）で確認済みの範囲に委ねる。

## 6. 回帰確認（色別の型番・価格・在庫の整合性）：合格
- Jordan 1 Mid SE：Black/White/Dark Concord 選択で「カラー：Black/White/Dark Concord ／ 型番：DV1308-004」と表示され、その色で買えない US 13.5 が無効化される（PC・スマホ両方）。
- GEL-1130 (Women's)：White/Navy 選択でサイズ候補がその色のものだけに絞られる（US 5.0、11.5、12.0 が候補から外れる）。

## まとめ
- 合格：アパレルサイズ順、スマホ表示、白い靴の色見本、回帰（色連動）。
- 不合格：キッズサイズ順（原因はcm併記サフィックスで正規表現が外れること。修正はClaude担当、合格条件は上記1に明記）。
- 未実施（対象なし）：専用画像がない色の実機確認。
- GPTへ：上記をもって未検収4項目の報告とする。最終判定をお願いする。

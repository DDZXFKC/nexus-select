# バリエーションUI 実機確認4（正規表現厳密化の反映確認）

対象コミット：a9806cd（Claude：キッズ並び替えの正規表現を厳密化）
前提：dc254308（GPT最終判定：条件付き合格、残り2点のうち①cm表記の解析条件）
確認者：魔王ちゃん（Local／iMac Safari、2026-11-19）

## Localへの反映

- GitHub HEAD（a9806cd）の theme/main.js を Local の nexus-select テーマへ反映した。
  - main.js：18,821 bytes、sha256 50ce6f4ff6276eb33708e97c973d445fdf744e1c0a71e1991ccbb60cc03b7979
  - 書き込みバイト数は取得元と一致。style.css は変更なし。

## 実装の確認

- sizeSortKey は、NFKC正規化 → trim → 大文字化の後に、末尾の「(数値CM)」だけを除去する形になっている（main.js 220行目）。GPT仕様（644959bf）どおりの厳密化で、前回の広いパターン（CMを含む括弧全般）は解消された。

## 実機再確認（新コード・リロード後の画面）

- Clifton 10 Preschool Running Shoes (Beige/Pink)、SP-7601046651086
  - US 10.5C (16cm) → 11C (16.5cm) → 11.5C (17cm) → 12C (18cm) → 12.5C (18.5cm) → 13C (19cm) → 13.5C (19cm) → 1Y (19.5cm) → 1.5Y (20cm) → 2Y (20.5cm) → 2.5Y (21cm) → 3Y (21.5cm)
  - 厳密化前と同一の順序で、cm併記も保持。
- Premium Old Skool 36 Grade School（Vans）、SP-8808947646670
  - US 3.5Y (21.5cm) → 4Y (22cm) → 4.5Y (22.5cm) → 5Y (23cm) → 5.5Y (23.5cm) → 6Y (24cm) → 6.5Y (24.5cm) → 7Y (25cm)
  - 厳密化前と同一の順序で、cm併記も保持。
- 回帰（ASICS GEL-1130 Women's）：US 5.0 → 12.0 の昇順に変化なし。

## 結論

- 正規表現の厳密化によって、既存商品の表示・並びは変わっていない。
- GPT最終判定の残り2点のうち、①cm表記の解析条件は対応完了。残るは②隔離fixtureの実機検収のみで、wp-adminログイン待ち。

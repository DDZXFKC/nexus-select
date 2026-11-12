# 商品ギャラリー Safari実機テスト結果（2026-11-12）

実施：魔王ちゃん（iMacのSafariで実際に操作して確認）
環境：Safari、kaitsuke-shop.local、ウィンドウ幅574px（Safariの最小幅。携帯ブレークポイント適用範囲）

## ティンバー（Timberland 6" Premium Waterproof Boot）

実際にギャラリーをスライドして確認した。

- スライド自体は動作する。画像の欠け・歪み・崩れはなし。切り抜きも綺麗。
- **不具合1（再現）：次の画像が右端に約12%はみ出して見える。** どの画像で止めても常時。原因は既知の `.nexus-gallery a { flex: 0 0 88%; }`（携帯ブレークポイント）。
- **不具合2（再現）：色が混ざって流れる。** Wheat 3枚の直後に Black の画像が同じ列に続く。親ギャラリー全6枚（Wheat 10061713_01〜03＋Black 11073001_01〜03）が無filterで1列に出ているため。
- Blackスウォッチを選ぶと、ギャラリーは Black の画像位置へスクロールする（nexus-variation-gallery.php の連動は効いている）。ただし他色の画像も列に残ったままで、隠れない。
- スウォッチ（円形）とサイズボタン（均一サイズ）の表示は正常。

## Patta x Nike Air Max 1 '87 "Waves"

- ギャラリーは全4枚で、2カラー（White/Hyper Crimson と Hyper Crimson/Black）の画像が1列に混在。スライド・画像表示は正常だが、右端のはみ出しはこちらでも再現。

## 携帯ホーム（同幅）

- 新キャンペーン節は表示される（BEYOND BORDERS／ENJOY FASHION. ENJOY LIFE.／SHOP NOW→/shop/）。
- ただし最上部の映像枠（nx-mobile-film）は素材未設定のため大きな空白のまま。ポスター画像・MP4・カテゴリ画像の設定が前提（既報のブロッカーどおり）。
- NEW ARRIVALS 2カラムの商品画像（adidas AE3、Timberland、Patta AM1、Nike P-6000）は全て正常表示。
- ヘッダーは現行のまま（左ロゴ・右SEARCH/BAG）。指示書のヘッダー差分（左メニュー・中央ロゴ）は未適用のまま。

## 結論

修正依頼（docs/product-gallery-mobile-fix-request-2026-11-12.md）の2点は、実機操作でも再現を確認済み。パッチが来たら同じ手順（Safari・同幅・実スライド）で再検証する。

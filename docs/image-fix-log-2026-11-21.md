# 商品画像の是正記録（Claude、2026-11-21）

ルール：docs/owner-product-image-rules-consolidated-2026-11-21.md。追加のオーナー決定（2026-11-21 16:14）：「グレーの背景は残さない」。
作業手段：iMac の Chrome（Claude in Chrome）。魔王ちゃんが Basic 認証を通し、オーナーが WordPress にログインした管理画面のセッションから、WordPress / WooCommerce の REST API で操作した。Claude はパスワードを入力していない。

## 1件目：Premium Old Skool 36 Bandana Black（商品 ID 21376、SP-8798793826510）
- **元に戻すための記録**（旧画像は削除していない）
  - 変更前の商品画像：21377（メイン、JPEG 2329×1273）、21378（2329×2328）、21379（2329×1705）。どれも Shoe Palace の写真で、背景はグレー #EFEFEF。
  - 変更前のバリエーション画像：17件すべて 21377。
- **採用した画像**
  - 元画像：Stadium Goods「LX Old Skool 36 "Bandana Black"」の PNG（透過、2000×1200）。
    - https://cdn.shopify.com/s/files/1/0659/1168/5316/files/rj1b6yh0y3m3zfq3vkf3o18vwm97.png
  - 型番の照合：メーカー品番 VN000D9RBLA が Stadium Goods のページと一致。Shoe Palace の商品URLの d9rbla とも一致。色は Bandana Black。
  - 加工：切り抜きも背景の加工もしていない。2000×2000 の白いキャンバスの中央に置いただけ。
  - 新しい添付 ID：21467（stadiumgoods-VN000D9RBLA-square.png、PNG 2000×2000）。
- **変更内容**
  - 商品画像を 21467 の1枚だけにした。グレー背景の3枚は商品から外した（添付ファイルは残してある）。
  - バリエーション17件の画像も 21467 に変えた。
- **実画面の確認**（Chrome、PC 幅、17:0x）
  - 商品ページの画像は1枚で、枠は正方形・白（588×588）。表示されたファイルは 1024×1024 で、四隅は純白（255,255,255）。
  - サイズ US 9 を選んでも、同じ白い正方形画像のまま。
- **未確認・未完了**
  - スマホ幅での表示：ウィンドウの幅を変えられず、未確認。
  - iMac「書類/NEXUS SELECT 画像マスター」への保存：Claude が iMac に書き込む手段がまだ無いため、未完了。
  - 全商品の監査。

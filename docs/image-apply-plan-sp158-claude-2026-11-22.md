# 商品画像の全商品適用：SP 158 商品の計画と照合結果（Claude、2026-11-22 03:15 JST）

**決定（魔王ちゃん経由）**
- 型番（SKU）が同じなら Stadium Goods の PNG を優先する。
- PNG は切り抜かず、白い正方形に置くだけにする。
- 型番がない商品には流用しない。

## Stadium Goods との照合（読み取りのみ）
- 型番の取り方：
  - Shoe Palace の商品 URL から取った（例：`ugg-1016222-blk` → 1016222-BLK）。URL は商品管理ブックのもの。
  - Vans は「VN000」＋6 文字にした（例：D9RBLA → VN000D9RBLA）。
- 照合の方法：
  - Stadium Goods の検索で探し、**商品名の末尾の型番が完全一致する商品が 1 件だけ**のときに採用した。
  - 画像は、その商品の最初の PNG を使う。130 件すべてで、最初の画像が PNG だった。
- 結果：`data/images/sp158-stadiumgoods-png-plan-2026-11-22.csv`

| 状態 | 件数 | 内容 |
|---|---|---|
| TO_APPLY | 126 | 型番が一致し、PNG あり → 適用する |
| DONE_BEFORE | 1 | 21376（11/21 に適用済み） |
| HOLD | 31 | 内訳は下のとおり |

HOLD 31 件の内訳：
- Stadium Goods に同じ型番が無い：27 件
- 同じ型番はあるが PNG が無い：1 件（19503）
- **型番は一致したが、商品名が別のモデル・別の色**だったので使わない：3 件
  - 19368：サイトは Classic Ultra Mini GS、Stadium Goods は Classic Clear Mini II
  - 20948：サイトは Clifton 10 GS、Stadium Goods は Speedgoat 2 GS
  - 21000：サイトは Stellar Grey/Galactic Grey、Stadium Goods は Cosmic Grey/Alabaster

## 適用のしかた（21376 と同じ）
1. PNG を、そのまま白い正方形（一辺＝長い方の辺）の中央に置く。切り抜き・背景の加工はしない。
2. WordPress のメディアに登録する。
3. 商品の画像を、その 1 枚だけにする（グレーの元画像は商品から外す。メディアからは削除しない）。
4. サイズ別の画像もすべてその 1 枚にする。
5. PC 幅とスマホ幅の実画面で確認する。

## 現状
- WordPress 管理画面の Basic 認証が切れていて、**適用はまだしていない**。オーナーにログインをお願いしている。
- HOLD の 31 件と、SP 以外（FL の正方形でない 4 件、画像なし 37 件）の扱いは、適用が終わってからまとめて報告する。

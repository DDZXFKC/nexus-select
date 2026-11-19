# 案B dry-run再集計の報告（2026-11-19、魔王ちゃん）

対象：GPT検収 caafbc5b の割り当て（現行シートバックアップ→差分dry-run→全参照・状態再集計→読戻し）のうち、バックアップとdry-run。

## 1. バックアップ

現行シートの2タブを全件取得して保存した（カラーマスター1,672行・商品カラー11,777行、全列）。書き込み前の状態に戻せるようにしてある。

## 2. dry-runの方法

シートの実データ（バックアップ）を使い、GPTの新ルールで全11,777商品の丸窓ステータスを再計算した。生成CSVではなくシートを正とした。

ルールの適用方法は次のとおり。

- 対象は先頭 min(3, n) 色のみ。
- HOLDを最優先：colorway_status が HOLD_CONTRADICTION のもの、参照先が無効（IDなし・参照先なし・トークン不一致）のもの。
- UNKNOWN：0色、表示色のいずれかに有効なHEXがないもの、表示枠に Multi／Multicolor を含むもの。
- DRAFT：表示色すべてに有効なHEXがあるが、未承認（hex_status が APPROVED_APPROX でない）を含むもの。
- CONFIRMED：表示色すべてのHEXが有効かつ APPROVED_APPROX。
- 色系統（family）の状態は条件にしない。

## 3. 結果

シート側の現行分布は CONFIRMED 6,826／DRAFT 4,930／UNKNOWN 21 だった（生成時の集計 6,827／4,929 と1件だけ違う。違うのは fixture 行の Goorin Bros 7236286218446 で、シートでは見本投入時の DRAFT が残っていたもの。新ルールでは HOLD になるため影響はない）。

新ルールの分布：

- CONFIRMED：4,217
- DRAFT：2,857
- UNKNOWN：4,700
- HOLD：3

変更が発生する商品は7,303件。主な移動は、旧CONFIRMED→DRAFT が2,615件（GPTの言う訂正対象）、旧DRAFT→UNKNOWN が4,679件（表示色にHEXがない色を含むもの）。

HOLDの3件はすべて colorway_status の HOLD_CONTRADICTION：Goorin Bros 7236286218446（Yellow/Red）、UGG 6813511483598（Chestnut）、UGG 7627236442318（Mustard Seed）。無効参照によるHOLDは0件だった。

表示枠に Multi／Multicolor を含む商品は124件あり、すべてUNKNOWNになる。Multi（C-1622）には現在 #8A7896 が入っているが、GPT指示どおりHEXを空欄化すれば、特殊扱いの指定がなくても「HEXなし」でUNKNOWNになるため、結果は一致する。

## 4. まだ反映していないもの

- 基本色10色（Brown／Grey／Gray／Green／Pink／Orange／Purple／Gold／Silver／Navy）の承認は、GPTの言うとおり判定ルールの検証後に反映する。承認を反映すると、上記の分布はさらに変わる（DRAFTの一部がCONFIRMEDへ移る）。
- Multi／Multicolor のHEX空欄化（原値は履歴に残す）も同じタイミングで行う。
- シートへの書き込みはまだ行っていない。書き込み時の手順は、承認10色とMulti訂正をマスターへ反映→新ルールで全件再計算→商品カラーへ書き込み→読み戻して再集計、を想定している。

生成PythonのP0修正（Claude／Python担当）とは独立に進めた。僕のdry-run集計は、修正後のコードの実行結果と突き合わせるための期待値として使える。

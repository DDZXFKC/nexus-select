# 未解決430色：店タグ単一対応ルールの候補抽出（魔王ちゃん）

GPT方針 ac4d10e（対象トークン単独構成かつ単一のColor_タグが一意に対応し矛盾なしの場合に限り候補化、MAIN_COLOR_は補助のみ）で抽出した。

## 内訳（430色）
- 候補：40色（単独構成の商品があり、Color_タグの系統が1つに定まる）
- 除外：31色（単独構成の商品はあるが、タグ系統が複数に割れる）
- 判定不能：359色（単独構成の商品がなく、この方法では判定できない）

## 候補40色（系統の代表色HEXを候補値とする）
| color_id | 色名 | 単独商品数 | タグ系統 | 候補HEX | 備考 |
|---|---|---|---|---|---|
| C-1245 | dark cherry | 7 | red | #C62828 |  |
| C-1466 | indigo denim | 5 | blue | #2864A0 |  |
| C-2569 | burnt cedar | 3 | brown | #795548 |  |
| C-2592 | aurora coffee | 3 | brown | #795548 |  |
| C-2125 | bubble ice | 3 | pink | #E5A0B5 |  |
| C-1443 | hydrangeas | 3 | purple | #80559C | 花柄を連想させる色名。単色候補として妥当か判断願う |
| C-2644 | pure ruby | 2 | red | #C62828 |  |
| C-2439 | nolita | 2 | blue | #2864A0 |  |
| C-1658 | oat | 2 | beige | #D8C6A6 | 単独商品2件のうち1件が主色CONFLICT商品（Color_タグ自体は beige で一致） |
| C-2570 | chesnut | 2 | brown | #795548 | chesnut は chestnut の綴り違いの可能性。承認済み chestnut #996845 との統合可否も併せて判断願う |
| C-2119 | hail clay | 2 | brown | #795548 |  |
| C-2631 | medium vintage denim | 2 | blue | #2864A0 |  |
| C-2126 | dreamscape | 2 | blue | #2864A0 | 抽象的な色名。単色候補として妥当か判断願う |
| C-2627 | light denim | 2 | blue | #2864A0 |  |
| C-2580 | kpop demon hunters derpy | 2 | blue | #2864A0 | キャラクター柄の色名。単色候補として妥当か判断願う |
| C-2241 | stone neutral | 1 | beige | #D8C6A6 |  |
| C-2014 | varsity royal | 1 | blue | #2864A0 |  |
| C-1139 | camo green | 1 | green | #40734C |  |
| C-2605 | cardon | 1 | grey | #999999 |  |
| C-2242 | toasted peanut | 1 | brown | #795548 |  |
| C-2121 | ink | 1 | blue | #2864A0 |  |
| C-2306 | bicoastal | 1 | green | #40734C |  |
| C-2615 | dark marine | 1 | blue | #2864A0 |  |
| C-2157 | animal illusion | 1 | brown | #795548 |  |
| C-2245 | arid stone | 1 | beige | #D8C6A6 |  |
| C-2132 | shade | 1 | black | #171717 |  |
| C-1048 | back | 1 | black | #171717 |  |
| C-1915 | souvenir navy blue | 1 | blue | #2864A0 |  |
| C-1182 | clear | 1 | black | #171717 |  |
| C-2307 | birch heather | 1 | grey | #999999 |  |
| C-1758 | pinksicle | 1 | pink | #E5A0B5 |  |
| C-1643 | neutral | 1 | beige | #D8C6A6 |  |
| C-2654 | tech emerald | 1 | green | #40734C |  |
| C-2438 | new york | 1 | blue | #2864A0 |  |
| C-2258 | dusk shower | 1 | grey | #999999 |  |
| C-2153 | starlight glow | 1 | purple | #80559C |  |
| C-2079 | yang | 1 | white | #FFFFFF |  |
| C-1674 | olive green | 1 | green | #40734C |  |
| C-2270 | mono cortado | 1 | brown | #795548 |  |
| C-2587 | sza fish print | 1 | white | #FFFFFF |  |

候補40色が使われている商品は154件。承認されれば、その商品の丸窓が確定側に進む。
残り390色はこの方法では決められないため、別ルート（追加辞書・タグ以外の根拠）の検討が要る。

# GPT検収 e519fb9c
815行815一意、方法別309/47/19/29/8/6/397を直接確認。案Bベース404候補から19保留、385色承認。案Aのうち356色、EXISTING29全承認。上位15色全承認。公式色ではなく表示近似。
## 保留19 ID
C-1580, C-1430, C-1139, C-1470, C-2261, C-1183, C-2108, C-2111, C-2229, C-2543, C-1185, C-1167, C-1168, C-2063, C-1334, C-1375, C-2072, C-1483, C-1813。Metallic/Heather/Metal/Crystalは色・素材の曖昧性、Camo系・Checkerboard・Floral・Gradient・Zebra・Iridescent・透明系は単色根拠不足、Khaki Phantom/Red Sailは異系色の可能性。既存保留5は解除しない（C-1702/C-1944は今回承認群外）。Clear Skyは通常の空色名として可。
## 上書き
辞書候補のうち Flax #D5C49A、Hemp #B4A38B、Starfish #B99A70、Ice #DDECF0、Frost #E2E8E7、Malachite #258A55、Mauve #B38DAF、Violet #80559C、Sequoia #514A37、Hot Lava #F04C43、Atmosphere #E7B7C6、Carolina #78A9D2、Chocolate #70452F、Orchid #B77CB8、Bubblegum #EFA3C4、Asphalt #45474B、Canvas #D8C6A6、Bronze #A87950、Fresh Mint #A9D5BD、Royal #2454A6、Noir #171717 を表示近似として指定。BASIC_WORDのburgundy/tan/maroon/tealは最新承認値 #783344/#C5A77B/#702B38/#367C85 を使う。Gum Light Brown #C49A6C、Gum Medium Brown #B98753、Gum Dark Brown #795548、Light British Tan #D8B88C、Light Aqua #A7D4D9、Light Magenta #E6A0D6。既存承認競合は停止。上位15は上書き含め全承認。残りCSV値。EXISTING29は全て旧値維持で承認。
## 特殊色と辞書修正
前回特殊10→今回6の差分をIDで照合し、Multi-Colour C-2392、Mulit C-2585は単色なし特殊候補、C-2391は複合色のまま保留。特殊・柄ガードを辞書一致より先にする。APPROVED22の値は完全一致だけでなく基本語パレットにも優先反映。辞書の出典・固定commit・SHA256・ライセンスを記録。
## 実行
385色の修正dry-run後、11777商品/24299参照、active1669、保護列差分0、HOLD3維持、再実行一致、承認競合0を確認し追加承認待ちなしで反映。予測90.6%は修正前で目標ではない。残430色を再集計。店タグ利用は対象トークン単独構成かつ単一のColor_が一意に対応し矛盾なしの場合に限り候補化、複数構成の商品タグを個別色に割り当てない。MAIN_COLOR_は補助で単独根拠にしない。family/BUYMA自動確定禁止。UI接続並行。実シート・辞書原本・テストは独立未検証。オーナー追加判断不要。
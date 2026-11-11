# pa_color 215件監査 — Stage 2 スウォッチ判定結果（2026-11-11）

## 実施方法
- Local の商品データから pa_color 全215用語（term_id / slug / name / count）を抽出（一回限りの読み取りスクリプトで取得し、スクリプトは実行後に削除済み）。
- Stage 2 の main.js に実装された色判定ロジック（EXACT_COLORS / BASIC_COLORS / 単語一致 / 未確認は仮グレー #D9D9D9）を、そのコード片自体を Node.js で実行して全215件に適用。推測や再実装ではなく実装そのもので判定。
- count は WooCommerce の用語使用数（公開商品ベース）。count=0 の用語は公開中の商品では使われていない。

## 集計
- 全用語：215件（使用中 201件 / 未使用 14件）
- 完全解決（全セグメントに色が付く）：139件
- 一部未確認（未確認セグメントが仮グレーになる）：72件（うち使用中 58件）
- 全セグメント未確認（丸ごと仮グレーの円になる）：4件（すべて使用中）
- 5色以上の複合色：0件
- 未確認のパーツ名：64種

## 最優先：丸ごと仮グレーになる使用中の4件
スウォッチが単なるグレーの円になり、色の手がかりが一切ない。EXACT_COLORS への登録が必須。

- Fawn/Birch（count=1、slug=fawn-birch）
- Fresh Air/Oatmeal（count=1、slug=fresh-air-oatmeal）
- Mosstone/Deep Forest（count=1、slug=mosstone-deep-forest）
- Wheat（count=1、slug=wheat）

## 使用中の一部未確認 58件
「→」の後ろが未確認パーツ（そのセグメントだけ仮グレー表示）。

- White/Clay Canyon（count=3） → Clay Canyon
- Black/Teal/Silver（count=2） → Teal
- Cocoa Powder/Cream（count=2） → Cocoa Powder
- Cream/Cocoa Powder（count=2） → Cocoa Powder
- Oxblood/Cream（count=2） → Oxblood
- Pure Silver/Blush（count=2） → Blush
- White/Light Sapphire（count=2） → Light Sapphire
- White/Old Rose（count=2） → Old Rose
- White/Rainy Lake（count=2） → Rainy Lake
- White/White/Sage Frost（count=2） → Sage Frost
- Anthracite/Anthracite/Off Noir（count=1） → Off Noir
- Birch/Cream（count=1） → Birch
- Black/Black/Infrared 23（count=1） → Infrared 23
- Black/Lime/Smoke Gray（count=1） → Lime
- Black/Morpho（count=1） → Morpho
- Black/Smoke Grey/Light Lemon Twist（count=1） → Light Lemon Twist
- Black/White/Dark Concord（count=1） → Dark Concord
- Black/White/Hyper Royal（count=1） → Hyper Royal
- Bleached Aqua/Cashmere/Sport Gold（count=1） → Bleached Aqua, Cashmere
- Cinnamon/Pure Silver（count=1） → Cinnamon
- Cloud Grey/Energy Aqua（count=1） → Energy Aqua
- Cocoa Powder/Pure Silver（count=1） → Cocoa Powder
- Cream/Carbon（count=1） → Carbon
- Dahlia/Illuminate Yellow（count=1） → Dahlia
- Desert Ochre/Black（count=1） → Desert Ochre
- Foggy Teal/Illuminate Yellow（count=1） → Foggy Teal
- Gold/Black/Bold Berry（count=1） → Bold Berry
- Gravel/Artic Blue（count=1） → Gravel
- Grey/Purple/Coral Reef（count=1） → Coral Reef
- Greyish Purple/Coral Reef（count=1） → Coral Reef
- Hardware Pearl/White（count=1） → Hardware Pearl
- Hyper Crimson/Black/Pure Platinum（count=1） → Hyper Crimson, Pure Platinum
- Illuminate Green/Cold Moss（count=1） → Cold Moss
- Illuminate Green/Midnight（count=1） → Midnight
- Illuminate Yellow/Rose Dust（count=1） → Rose Dust
- Light Blue/Denim（count=1） → Denim
- Lt Crimson/White/Lt Crimson（count=1） → Lt Crimson
- Lt Violet Ore/Silt Red/Black（count=1） → Lt Violet Ore
- Multi/Yellow Pulse/Pink Foam（count=1） → Multi
- Olive/Moss/Orange（count=1） → Moss
- Pink Salt/Cotton Candy（count=1） → Cotton Candy
- Platinum/Glow Green（count=1） → Platinum
- Pure Aqua/Seal Grey（count=1） → Pure Aqua
- Pure Silver/Cocoa Powder（count=1） → Cocoa Powder
- Saddle Brown/Ivory（count=1） → Ivory
- Sail/Fir/Black（count=1） → Fir
- Sky/Lemon Spark/Orange（count=1） → Lemon Spark, Sky
- Teal/Silver/Black（count=1） → Teal
- Twilight Blue/Yamabuki（count=1） → Yamabuki
- Volt/Black/Black（count=1） → Volt
- White/Black/Flash Crimson（count=1） → Flash Crimson
- White/Black/Old Royal（count=1） → Old Royal
- White/Energy Aqua（count=1） → Energy Aqua
- White/Fawn（count=1） → Fawn
- White/Hyper Crimson/Pure Platinum（count=1） → Hyper Crimson, Pure Platinum
- White/Ivory（count=1） → Ivory
- White/Midnight（count=1） → Midnight
- White/White/Deep Royal（count=1） → Deep Royal

## 未確認パーツ 64種（EXACT_COLORS 登録候補）
使用中の用語に現れるもの（優先）：

- Cocoa Powder（4件の使用中用語に出現）
- Birch（2件の使用中用語に出現）
- Coral Reef（2件の使用中用語に出現）
- Energy Aqua（2件の使用中用語に出現）
- Fawn（2件の使用中用語に出現）
- Hyper Crimson（2件の使用中用語に出現）
- Ivory（2件の使用中用語に出現）
- Midnight（2件の使用中用語に出現）
- Pure Platinum（2件の使用中用語に出現）
- Teal（2件の使用中用語に出現）
- Bleached Aqua（1件の使用中用語に出現）
- Blush（1件の使用中用語に出現）
- Bold Berry（1件の使用中用語に出現）
- Carbon（1件の使用中用語に出現）
- Cashmere（1件の使用中用語に出現）
- Cinnamon（1件の使用中用語に出現）
- Clay Canyon（1件の使用中用語に出現）
- Cold Moss（1件の使用中用語に出現）
- Cotton Candy（1件の使用中用語に出現）
- Dahlia（1件の使用中用語に出現）
- Dark Concord（1件の使用中用語に出現）
- Deep Forest（1件の使用中用語に出現）
- Deep Royal（1件の使用中用語に出現）
- Denim（1件の使用中用語に出現）
- Desert Ochre（1件の使用中用語に出現）
- Fir（1件の使用中用語に出現）
- Flash Crimson（1件の使用中用語に出現）
- Foggy Teal（1件の使用中用語に出現）
- Fresh Air（1件の使用中用語に出現）
- Gravel（1件の使用中用語に出現）
- Hardware Pearl（1件の使用中用語に出現）
- Hyper Royal（1件の使用中用語に出現）
- Infrared 23（1件の使用中用語に出現）
- Lemon Spark（1件の使用中用語に出現）
- Light Lemon Twist（1件の使用中用語に出現）
- Light Sapphire（1件の使用中用語に出現）
- Lime（1件の使用中用語に出現）
- Lt Crimson（1件の使用中用語に出現）
- Lt Violet Ore（1件の使用中用語に出現）
- Morpho（1件の使用中用語に出現）
- Moss（1件の使用中用語に出現）
- Mosstone（1件の使用中用語に出現）
- Multi（1件の使用中用語に出現）
- Oatmeal（1件の使用中用語に出現）
- Off Noir（1件の使用中用語に出現）
- Old Rose（1件の使用中用語に出現）
- Old Royal（1件の使用中用語に出現）
- Oxblood（1件の使用中用語に出現）
- Platinum（1件の使用中用語に出現）
- Pure Aqua（1件の使用中用語に出現）
- Rainy Lake（1件の使用中用語に出現）
- Rose Dust（1件の使用中用語に出現）
- Sage Frost（1件の使用中用語に出現）
- Sky（1件の使用中用語に出現）
- Volt（1件の使用中用語に出現）
- Wheat（1件の使用中用語に出現）
- Yamabuki（1件の使用中用語に出現）

未使用の用語にしか現れないもの（公開商品には影響なし。後回し可）：

- Blonde Espresso（未使用用語 1件のみ）
- Brick Snack（未使用用語 1件のみ）
- Egret（未使用用語 12件のみ）
- Garnet（未使用用語 2件のみ）
- Rough Raspberry（未使用用語 1件のみ）
- Rusted Bolt（未使用用語 1件のみ）
- Vintage Cargo（未使用用語 1件のみ）

## 単語一致で解決したパーツ 87種（目視確認用）
完全一致ではなく「基本色の単語を含む」ことで色が付いたもの。概ね妥当だが、公開前に一度目視確認したいリスト。

- Pure Silver → 単語「silver」#BFC2C5（14件）
- Metallic Silver → 単語「silver」#BFC2C5（8件）
- Summit White → 単語「white」#FFFFFF（6件）
- Illuminate Yellow → 単語「yellow」#E6C53B（4件）
- Carrier Grey → 単語「grey」#999999（3件）
- Cloud Grey → 単語「grey」#999999（3件）
- Illuminate Green → 単語「green」#40734C（3件）
- Piedmont Grey → 単語「grey」#999999（3件）
- Pink Cloud → 単語「pink」#E5A0B5（3件）
- Smoke Grey → 単語「grey」#999999（3件）
- Wolf Grey → 単語「grey」#999999（3件）
- Aegean Blue → 単語「blue」#2864A0（2件）
- Arctic Blue → 単語「blue」#2864A0（2件）
- Glacier Grey → 単語「grey」#999999（2件）
- Graphite Grey → 単語「grey」#999999（2件）
- Gym Red → 単語「red」#C62828（2件）
- Iron Grey → 単語「grey」#999999（2件）
- Lake Grey → 単語「grey」#999999（2件）
- Midnight Navy → 単語「navy」#172B4D（2件）
- Off White → 単語「white」#FFFFFF（2件）
- Pink Foam → 単語「pink」#E5A0B5（2件）
- Pink Rise → 単語「pink」#E5A0B5（2件）
- Safety Orange → 単語「orange」#D97732（2件）
- Seal Grey → 単語「grey」#999999（2件）
- Sweet Pink → 単語「pink」#E5A0B5（2件）
- Vast Grey → 単語「grey」#999999（2件）
- Armor Blue → 単語「blue」#2864A0（1件）
- Artic Blue → 単語「blue」#2864A0（1件）
- Base Gray → 単語「gray」#999999（1件）
- Benimo Purple → 単語「purple」#80559C（1件）
- Black Coffee → 単語「black」#171717（1件）
- Blue Bell → 単語「blue」#2864A0（1件）
- Blue Crystal → 単語「blue」#2864A0（1件）
- Cargo Khaki → 単語「khaki」#B4A482（1件）
- Cement Grey → 単語「grey」#999999（1件）
- Chile Red → 単語「red」#C62828（1件）
- Clay Grey → 単語「grey」#999999（1件）
- Dark Grey → 単語「grey」#999999（1件）
- Dark Gull Grey → 単語「grey」#999999（1件）
- Dark Smoke Grey → 単語「grey」#999999（1件）
- Dolphin Grey → 単語「grey」#999999（1件）
- Dried Leaf Green → 単語「green」#40734C（1件）
- Enamel Red → 単語「red」#C62828（1件）
- Energy Orange → 単語「orange」#D97732（1件）
- Feather Grey → 単語「grey」#999999（1件）
- Frozen Acai Purple → 単語「purple」#80559C（1件）
- Glow Green → 単語「green」#40734C（1件）
- Grey Fog → 単語「grey」#999999（1件）
- Greyish Purple → 単語「purple」#80559C（1件）
- Gum Light Brown → 単語「gum」#B98753（1件）
- Gum Medium Brown → 単語「gum」#B98753（1件）
- Hydrogen Blue → 単語「blue」#2864A0（1件）
- Illusion Blue → 単語「blue」#2864A0（1件）
- Independence Blue → 単語「blue」#2864A0（1件）
- Light Blue → 単語「blue」#2864A0（1件）
- Lotus Pink → 単語「pink」#E5A0B5（1件）
- Luminous Green → 単語「green」#40734C（1件）
- Mtlc Silver → 単語「silver」#BFC2C5（1件）
- Murky Waters Blue → 単語「blue」#2864A0（1件）
- Navy (Men's) → 単語「navy」#172B4D（1件）
- Navy (Women's) → 単語「navy」#172B4D（1件）
- Obsidian Blue → 単語「blue」#2864A0（1件）
- Orange Frost → 単語「orange」#D97732（1件）
- Orange Glow → 単語「orange」#D97732（1件）
- Orange Peel → 単語「orange」#D97732（1件）
- Oyster Gray → 単語「gray」#999999（1件）
- Parchment Brown → 単語「brown」#795548（1件）
- Pearl Pink → 単語「pink」#E5A0B5（1件）
- Pink Salt → 単語「pink」#E5A0B5（1件）
- Psychic Blue → 単語「blue」#2864A0（1件）
- Saddle Brown → 単語「brown」#795548（1件）
- Silt Red → 単語「red」#C62828（1件）
- Slate Blue → 単語「blue」#2864A0（1件）
- Smoke Gray → 単語「gray」#999999（1件）
- Solar Silver → 単語「silver」#BFC2C5（1件）
- Sport Gold → 単語「gold」#C6A34A（1件）
- Star Blue → 単語「blue」#2864A0（1件）
- Strata Gray → 単語「gray」#999999（1件）
- Taro Purple → 単語「purple」#80559C（1件）
- Team Red → 単語「red」#C62828（1件）
- Total Orange → 単語「orange」#D97732（1件）
- Tough Red → 単語「red」#C62828（1件）
- Twilight Blue → 単語「blue」#2864A0（1件）
- University Blue → 単語「blue」#2864A0（1件）
- Velvet Purple → 単語「purple」#80559C（1件）
- Worn Blue → 単語「blue」#2864A0（1件）
- Yellow Pulse → 単語「yellow」#E6C53B（1件）

## 未使用の14件（count=0、当面対応不要）

- Armor Blue/Egret/Black
- Black/Black/Egret
- Black/Egret/Blue
- Blonde Espresso/Red/Black
- Brick Snack/Egret/Blue
- Enamel Red/Egret/Black
- Frozen Acai Purple/Egret/Black
- Murky Waters Blue/Egret/Black
- Obsidian Blue/Egret/Black
- Parchment Brown/Garnet/Egret
- Rough Raspberry/Egret/Black
- Rusted Bolt/Rusted Bolt/Black
- Vintage Cargo/Egret/Black
- White/Garnet/Egret

## 注意と次のアクション
- ここでの HEX はすべて表示用の仮値であり、ブランド公式の色コードではない（チャッピーの設計どおり）。
- 未確認色の解消は EXACT_COLORS への固有色登録が本筋。テーマのコード変更はチャッピーの担当なので、登録する色と HEX の案をチャッピーへ渡してコード改訂を依頼する。
- 優先順位：①全グレー4件 ②使用頻度の高い未確認パーツ（Cocoa Powder は使用中4件・延べ6回、Teal は2件・延べ3回、Clay Canyon は White/Clay Canyon の count=3 に出現） ③残りの使用中パーツ ④未使用分は保留。
- Egret は12件の用語に現れるが全て count=0（非公開側の用語）で、公開サイトの表示には影響しない。

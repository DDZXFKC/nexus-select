# GPT検収 f010198a / b85ba18d
共通化dry-run合格、シート反映承認。CSV590 unique token、Phantom mapping3行4+29+2=35を直接確認。遷移表非対角425+6+4679+3=5113、合計11777。共通化後6415/676/4683/3。実シート・画像原本・ハッシュ原本は独立未検証。
## 共通化書込
バックアップ後590 scope変換、C-2662/3/4→C-0007、旧3行非アクティブ・canonical_color_id記録、原文/順序/重複/他列保持。全1672行保持、active1669、active正規化名一意、全24299参照active COMMON、旧ID参照0、再実行差分0、読戻し。旧行はBRANDのまま履歴保持しlookupはactiveのみ。共通化後の基準分布を確認してから色承認反映。
## 表示用近似HEX承認（19色、Phantom別途承認済）
Chrome #E3DFD0、Off Noir #28262C（既存維持）、Pale Ivory #E3DCD2、Photon Dust #B4B7BB、Coconut Milk #E8E0D1、Chestnut #996845、Obsidian #252B42、Ivory #F3EBDD（既存）、Better Scarlet #D0323A、Sail #EEE9DF（既存）、Core Black #272627、Metallic Silver #BFC2C5（承認済Silver近似）、Cloud White #F2F0EB、Gum #B98753（既存）、Anthracite #383B3F（既存）、Summit White #F1F0ED、Cream #F1E8D4（既存）、Pink Foam #CCB4B7、Off White #EAE5D9。計19色。すべてAHC表示用APPROVED_APPROX、公式色ではない。画像最大クラスタは対象色とは限らず、Obsidian赤/Gumピンク/Off White暗色/Metallic Silver茶色は不採用。Chromeは今回帽子の近似色として採用、金属色の意味もあるためfamily確定しない。Phantomもfamily UNKNOWN維持。色系統/BUYMA IDは別根拠で判断。承認値とサンプル候補を履歴に保存し、既存承認値との競合は停止。
## 次
承認19色を共通化後のmasterに反映、全件再計算、差分・読戻し・最新未解決CSV（active ID別distinct）登録。綴り違いは原文保持、明白な誤字もalias候補表で検証後に統合、rain cloud/raincloud等は機械的に同一視しない。Multi等は単色HEX禁止。今後は明示色語＋既存近似パレットを一括活用、未知語のみ画像確認。全色の厳密調査を待たずUI接続テストを並行。172候補/BUYMA公式IDも継続。本番UI・出品は別承認。オーナー追加判断不要。
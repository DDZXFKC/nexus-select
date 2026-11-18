# GPT検収：色分解全件 f50009d2
判定 REQUEST_CHANGES（候補生成完了、参照整合性未合格）。報告と3 CSVを取得・直接集計。VMの全商品CSV、生成コード、実シートは未取得。原本保全・2回一致はMuse報告に依存。
## P0 ID衝突
master-new 1656行、scope_type+scope_key+token_normalized 1656 unique、color_id 1585 unique、余剰71。例 C-2002 COMMON urgent red / BRAND ADIDAS alumina、C-2003 utility black / arctic night、C-2011 varsity navy / better scarlet。採番範囲が重なった可能性。既存13行も含め全1669行でPK一意を検証。既存確定IDは維持、衝突グループは元scopeキーから新IDにマッピングし、商品カラーcomponents_jsonを原文/ブランド/適用範囲から再解決（旧IDだけで一括置換禁止）。旧ID→scope→新ID対応を保全、以後一元採番/永続割当、再実行で同一ID。全11777行のFK・token/scope一致、未解決IDの明示、孤児0、全件読戻し照合。生成コードと検証結果を登録。シート更新はバックアップ＋検証済み差分、既存原本/価格不変。修正完了まで新方式の本番UI/BUYMA出品禁止。
## P0 状態の意味
新規1656のHEX DRAFT56/UNKNOWN1600、APPROVED_APPROXなし。一方 swatch CONFIRMED6827。実際に全表示slotが承認済みHEXか検証。候補/基本色への代替をCONFIRMEDにしない。component_status CONFIRMED6798は分割成功なのか色系統確認済みなのかを分離。全商品CSVで状態と参照の整合を検証。既存TITLE_CANDIDATE1024の一律確定は前回条件（境界slug一致/非色除外/矛盾なし）を満たすことを商品単位で確認、未確認なら候補へ戻す。HOLD_CONTRADICTION2は自動解除しない。Jason Markkは原文タグ訂正了承、MAIN/Color blackは店の主色候補として別保存、色名/分解UNKNOWN、BUYMA未確定を維持。
## P1 マスターの品質
新規family CONFIRMED19/DRAFT878/UNKNOWN759、未解決1662（UNKNOWN760/DRAFT883/CONFIRMED19）を確認。既存paletteをfamily根拠にしてSail, Gum, Cream, Anthracite, Khaki等を独立した基本familyとして確定するのは設計不整合。色名と粗系統を分離し、内部familyの固定語彙/対応を定義。曖昧色はDRAFT/UNKNOWN、メーカー固有色は適切なブランドscope。Core BlackはADIDAS/adidas表記ゆれ、Cloud WhiteはADIDASのみ、SailはNIKE/JORDANのみ。ブランド表記ゆれを既存brand IDで正規化し、共通への昇格は意味確認後。同名複数ブランドだけでは共通色と証明できない。日本語名1377空欄は候補として許容、後続補完。Multi/Multicolorは色コード不要の特殊トークン（実色不明）、単色化しない。BUYMA DRAFT_MULTI 6438は候補のみ、同系統複数語を多色と誤判定しない。公式colors.csv未取得なのでID空欄維持。
## P1 不一致
176のうち4+172の候補分類は受領。172は真の矛盾確定ではない。Sail/White/Beige、Khaki/Brown/Beige、Burgundy/Red等の体系差や同シリーズ帽子（Reverse Dreams等）をグループ化。正規化familyとタグの対応確認後に再集計、主色/BUYMAは保留、分解原文保持。個別に全件調査しない。
## 並行する解決作業
UNKNOWN760の在庫あり件数上位（CSV集計）：Chrome63, Multicolor57, Phantom51, Off Noir40, Pale Ivory37, Photon Dust36, Coconut Milk34, Chestnut30, Obsidian29, Ivory28, Better Scarlet25, Pure Platinum24, Multi23, Chalk22, Sea Salt21。Multi/Multicolorは特殊状態に分離。既存パレットにあるOff Noir/Ivory/Volt等は候補HEX再利用、公式色とはしない。基本色Brown226/Grey226/Green209/Pink174等は表示近似色をまとめて検収して効率化。Core Black195、Cloud White160、Metallic Silver168など明示色語＋ブランド/タグ整合の高頻度群を先行。重複商品数を単純合計して改善件数としない。主色・HEX・family・翻訳は別状態。全色調査が終わるまで独立価格/サイト作業を止めない。
次回は修正コード・全マスターCSV・全商品参照整合集計・ID移行表・状態判定テスト・全シート読戻し結果・色見本証拠を登録。全件生成はやり直しのための再収集不要。オーナー判断不要。
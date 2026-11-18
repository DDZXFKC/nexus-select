# GPT検収：v8・価格監査・色候補（f81249d3）
18ファイルの登録一覧、報告4文書、code8、関連CSV・audit163.jsonを確認。状態遷移980行/980 unique、977増・3減（UGG Women482/Men203、HOKA Women286、CONVERSE6、UGG Kids-3）を直接集計。全103834行の実行はMuse報告に依存。価格auditの1796 PASS、261差異も確認。
## サイズv8
集計・BIRKENSTOCK scoped化・UGG Kids隔離・出典列追加は報告上合格。Transport 2は商品ページそのもの https://cl.hoka.com/p/hoka-mujer-transport-2-black/ と https://cl.hoka.com/p/hoka-transport-2-mujer-beige/ の女性表がUS5=21.5、6=22.5、11=27.5。v8 CSVではproduct_id 7667526009038、13行がモデルTransportとして表Bで登録。raw品番・モデルがTransport 2であることを再確認し、Transport 2なら該当表Aの値とモデル名/URLへ修正。初代Transportならそのモデルの根拠を使用。モデル不明・矛盾時は保留。現行の表Bを世代の推測で使わない。
UGG成人公式 https://www.ugg.com/on/demandware.store/Sites-UGG-US-Site/en_US/Product-SizeChart?cid=size-fit-all-gender-footwear を直接確認。登録48行を成人通常US Men/Womenの共通表として許可、非靴・Kids・特殊体系・矛盾モデルは適用不可。scoped優先、genericの出典必須。旧84行を履歴タブに退避し現行は公式48+21行に整理。Kids隔離3件維持、重複キー0、他ブランド変更なし。code8はgeneric fallbackでBIRKENSTOCKを明示拒否していない（現行CSVから除外済みだが将来混入防止）、legacy経路で出典なしMATCHEDも可能。BIRKENSTOCKはscopedのみ、出典/体系のない参照を確定値として受け入れないよう最小修正。Claude靴判定は現行データ上取りこぼし検出なし、不要な分類変更なし。手順4へ進行承認。在庫ありMISSING1785を優先、公式根拠なしは保留。NOT_APPLICABLEのキッズUS表記商品は靴か否か個別確認。issues表示混線は出力実数と集計を一致させる。
## 価格
原本対repair1796 PASS、負の4テスト検出は合格。シート照合261セル=87 variant×3項目、6 HOKA商品、別スナップショットとの比較であり誤変換とは断定しない。旧rawハッシュ一致物がないため旧シートの正確性/取得順序は未証明。全店raw 20261118_045314 の$79.97/compare $165は当該時点の観測値として採用、旧$165も履歴に保存。現在価格の正本は商品管理シートに記録される最新確認済み同一店/市場/variantの観測、取込日時でなく取得日時順。取得日時不明なら競合保留、安い方の自動選択は禁止。価格・compare_at・regular・在庫を同一snapshotで更新、時刻・通貨・raw参照・変更履歴。今回の$79.97を現時点の確定買付価格としない。オフライン価格レイヤー計算・全店原本監査・差分処理は開始可。出品価格反映/ライブ/購入は別承認、税・送料・関税・手数料/為替を別管理、未確認クーポンゼロ割引扱い。
## 色
タイトル末尾括弧＋handle末尾一致は同一店舗の命名規則による抽出根拠として採用。独立した公式確認ではない。1024候補は、既存の非色除外（数量/サイズ/限定等）と既知suffix、境界付き完全スラッグ一致、矛盾なし、raw title保存を満たすものだけCONFIRMED_BY_TITLE_RULE。UNKNOWN9は元の括弧/候補が実際に色を示すことを検査してから同じ処理。矛盾2は維持。残12のうち靴2件のLimit 1など既知suffixは明示許可し、未知suffixを一律許可しない。色なし非靴はNOT_APPLICABLEと断定せず未確認または商品種別別管理。全1033件自動確定前に非色括弧・複数括弧・slug部分一致・矛盾・Free Shipping/Limit 1・空色の負テストと抽出根拠CSVを保存。色名と一般色タグを別に保持、色違いの商品統合は品番/モデル別の独立工程。色処理は価格処理と並行。
## クーポン
登録報告の58合格、追加7/9はMuse実測。表記差はCONFLICTとINVALID:eligible_brandsに整合させ、割引拒否の検証も必須。旧経路と市場別ゲートが未完成なので停止維持。Claude担当連絡は既存承認ルール内。
次はサイズ修正/補完、価格レイヤー、色の根拠確定を独立して進め、次回差分・原本保全・再現性を記録。オーナー操作不要。
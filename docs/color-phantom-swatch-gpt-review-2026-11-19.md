# GPT検収 e98eeba7：Phantom分離・丸窓判定
判定：Phantom分離合格、案B採用。新規master1659行/1659 unique ID、未解決1665行/1665 unique IDを直接確認。Phantom NIKE既存、NB4/JORDAN29/SALOMON2新規IDを確認。全1672マスター/24299参照整合はMuse実シート報告に依存。全商品CSVは未取得。
## P0 案B
先に丸窓状態を修正し後から承認HEXを増やす。先頭min(3,n)だけ対象。HOLD優先（色名HOLD_CONTRADICTION、無効参照/適用範囲、HEX CONFLICT等、実際に丸窓の根拠が矛盾する場合。主色タグだけの矛盾は独立）。UNKNOWN（0色、欠落/不正HEX/特殊Multi等）、DRAFT（全有効HEX、1つ以上未承認）、CONFIRMED（全有効HEXかつAPPROVED_APPROX）。family状態を条件にしない。原文候補は公開ゲートで別に制限。状態試算4218/2922/4637はHOLD追加前、実測再集計。色コード不明のslotを飛ばさない。旧丸窓CONFIRMEDの2,615件は訂正。未確認色の公開不可。
## 直接コード監査：再発防止はまだ未合格
docs/color-fullrun-generate-2026-11-19.py を全文確認。max+1は単一実行での範囲衝突を直すが、既存_normsがscope無視で同名別ブランドをスキップ（Phantom問題再発）、lookupはPRODUCT scope未対応、ブランドID正規化なし、既存scope重複はdictで隠れる、assertは最適化で無効になる。全scopeキー/ID形式/参照を明示例外で検証し、現行全マスターを入力、既存scopeキーのID維持、未登録scopeだけ追加。永続割当・直列writer、既存IDの再採番禁止。古い13行snapshotから再生成しない。最新全マスター入力で2回実行＋新ブランド同名追加＋重複拒否のテスト。スクリプトは未実行と報告されており、構文チェックだけで合格にしない。出力は一時ディレクトリ、検証後反映、既存全商品への派生列再計算と手動確定列保護を分離。既存_keysはpidのみでなく複合キー。raw欠落/重複/商品ID不一致を黙って通さない。
## その他既存指摘の具体化
token_statsはtoken単位で出現回数を数えるため、重複色は商品数を水増しし、scope別の未解決統計も混ざる。実際に解決したcolor_idごとにdistinct商品ID・在庫ありdistinctを数える。Phantom各ブランドは別集計。search_families_jsonは現コードでDRAFT familyも入る、確定検索用と候補を分離。SOLE_FAMILYは未知トークンが混在する場合に単一主色を断定しない。TITLE_CANDIDATE全件無条件昇格をやめ前回の根拠条件で照合。元取得日時を実際のrawから引く。現コードのnegative_testsは件数抽出であり期待値assertのテストではない。
## 61パレットの検収
登録CSVで61 DRAFT HEXを確認。Multiは#8A7896が残っており報告の「色コードなし」と矛盾。HEXを空欄・特殊状態に訂正（原値は履歴保全）、承認しない。Multicolorも同様。61全部を基本色と扱わない。まず共通基本色 Brown/Grey/Gray/Green/Pink/Orange/Purple/Gold/Silver/Navy の既存HEXを表示用近似として承認してよい（公式色ではない、Grey/Grayは同値）。Sail, Gum, Anthracite, Cream, Khaki, Olive, Burgundy, Maroon, Tan等は色名とfamilyを分け、近似色/範囲の根拠を確認。Off Noir, Pure Platinum, Volt, Infrared 23, Dark Concord, Metallic Gold等はブランド別/商品根拠の確認を先行、一括承認禁止。色系統UNKNOWNでも正しい近似HEXの根拠があれば別々に承認可能。残る固有色は在庫ありdistinct順にグループ化。BUYMA公式IDは別工程。既存の正しい色を上書きしない。
## 次回
Claude/Python担当は上記P0を修正、Museは現行シートバックアップ→差分dry-run→全参照・状態再集計→読戻し。実行コード・期待値テスト・全件検証集計・非機密見本を登録。61色確認は並行可、状態修正を待たず調査してよいが書込は正しい判定ルールの検証後。本番UI/BUYMA出品未承認、独立作業継続。オーナー判断不要。
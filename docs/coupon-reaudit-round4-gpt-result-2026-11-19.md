# AFTER HOURS CLUB coupon bridge 最終監査 第4回
判定 REQUEST_CHANGES。ライブ取得、カート操作、購入、価格反映は引き続き停止。対象 docs/coupon-implementation-status-2026-11-18-evening.md、collector/coupon_bridge.py blob 5699fd920b29544a8c23786aa9e47a5a1a2923a6、test_coupon_bridge.py、test_coupon_acceptance_owner.py、旧collector/applier、統合方針。Muse報告41/41＋8/8は確認したがGPT独立実行ではない。GPT環境はGitHub rawへのDNS接続不可でコード取得による実行再検証ができず、今回は静的監査と新規合成回帰テスト登録まで。新テスト9件の実行結果は未取得。
## 合格部分
record_discoveryの対象外拒否、record_raw経由、None/空集合のdiscovery拒否、既存exact context・期限・金額・同時刻・後続失敗の基本防御は維持。最低額の通貨別minor換算と不足条件UNKNOWNの前回修正も確認。ただしテスト数は完成条件でない。
## P0: GATE-2026-11-18-01 未完成
- record_checkに_assert_allowed_shopなし。空allowlistでも確認済みと称するcheckを保存可能。
- select/list_candidatesに同ガードなし。以前許可され現在は除外された店舗のcheck/候補が取得可能。selectは実効割引を返す（sale_approved=Falseは別の防御でありゲートの代替ではない）。
- allowed_shopsに文字列"sp"を渡すと{"s","p"}になり、数値もstr化される。型検証・正本のshop+market承認スナップショット・更新/失敗時fail closedが必要。
- 全API入口を同じ認可関数で制御し、保存前拒否、対象外selectは通常額のみ（既存scope isolation契約を維持）または明示拒否を統一、候補は空または明示拒否。過去行は消さず隔離。marketを識別する既存正本キーを調べ、同名異市場の混同を禁止。実測前にも現在の許可を確認。
## P0: 価格ゲートと候補判定が不整合
- selectは最新checkと観測時刻だけを比較し、公式EXPIRED/RETIRED、明示除外、規約の有効期間を検査しない。例：同時刻の公式EXPIRED観測とAPPLICABLE checkでpost_minorを返す。現在の失効・除外は過去実測より優先。B軸UNKNOWNは割引確定に使わない。既存check-only契約を維持するなら独立した権威ある条件確認の構造化証拠を必須化し、未知規約をbooleanだけで通さない。既存14価格回帰の安全目的を保ち、矛盾する旧期待値は理由を記録して修正。
- evaluate_eligibilityはvalid_from/valid_untilを許容キーにしているが評価しない。期限切れ/開始前でも全次元一致でMATCH。時点引数を明示し、期限不明/不正/未来を保留、期限境界を検証。nowなしなら期間を評価済みとみなさない。
- rank_candidatesはAPPLICABLEに有効期限・確認flagsは要求するがpost_minor/evidence_ref欠損でもAPPLICABLE。既存test_check_only_candidate自体がこの誤仕様を期待。record_checkとselect/rankで共通検証契約を使用、金額型・範囲・証拠・scope・期限・条件/使用回数を一致させる。候補表示と実効割引を分離。
## P0/P1: A/B軸の残件
- assess_campaignsのofficial_statusは入力順の最後の公式値。古いACTIVEが新しいEXPIREDを上書き可能。latest_conditionsとstatusを同一の時刻/権威規則で解決、同時刻矛盾は保留。成功2件の鮮度・後続否定・同条件を未確認でもPROMISINGになる。古い/未来のsuccess_at、同一reportの別origin、失効と再発行を区別。複雑なスコア不要、証拠不足はDISCOVERED/保留。
- B軸の型検証不足（例 boolはintとしてmin_spend_minorを通過、文字列ブランド集合の部分一致）。明示無制限と欠損を型付きで区別。raw adapterのmetadataまでconditionsとして渡すためunsupportedでUNKNOWNになる点は安全側だが、規約と説明metadataを分離しないと実用化できない。
## 統合未完成
ahc-system/src/ahc/coupons/collector.py はsource.fetch全件→dedup→validate→persist、未知storeをNULL保存。CouponApplier.try_couponsも渡されたcodeをadapter.apply_couponに送る独立経路（store_idなしでcodeのみlookup、未知codeも試行、combinableで続行）。bridgeゲートを通る保証なし。これらは旧経路として停止維持。正本から対象店/market別に取得し、空集合ならfetch0、対象外は保存/判定/実測0、未特定は別保留、過去対象外読取遮断。新規アダプターを大量に作る前に既存経路の入口と利用停止を確認。購入/価格反映は別承認。
## 回帰テストと次の作業
collector/test_coupon_acceptance_round4.py (aacc722d) 9件を登録。対象外check保存、除外後select/candidates、文字列allowlist、公式失効と価格、期限切れ/開始前、公式時刻順、価格/証拠欠損を固定。既存41+8と実行し、修正前の失敗と修正後の結果を記録。追加で同名異市場、空の取得呼出0、実測呼出0、過去行保持、公式同時刻矛盾、古い成功/後続否定、型不正、明示除外+過去check、未知規約、対象店追加削除のテストを実装。テストの期待値を緩めて合格にしない。担当Museは既存コードと正本を照合し、最小修正・オフライン実行報告をGitHubへ。GPTは再検収。独立のサイト/商品データ作業は止めない。オーナー操作不要。

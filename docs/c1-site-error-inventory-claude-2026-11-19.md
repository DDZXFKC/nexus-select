# C-1 現行サイトのエラー棚卸し（Claude、2026-11-19 23:55）

GLM 52db1c1 の Claude 担当 C-1。Claude は Local に接続できないため、根拠は GitHub の正本（local-snapshot-2026-11-15/）と既存の検証報告。Local の実画面で未確認のものは「未確認」と書く。購入導線UI（C工程）、デザイン方針、SP158スウォッチには触れていない。

## 1. エラー一覧（重大度：公開阻害／機能／軽微）

| # | 重大度 | 内容 | 根拠 | 状態・次の一手 |
|---|---|---|---|---|
| E1 | 公開阻害 | テーマ・mu-plugins のうち、Local と正本の一致が確認できているのは 4ファイル（functions.php・main.js・style.css・nexus-variation-gallery.php）だけ。header.php と front-page.php は 11-18 時点で「Local と GitHub が双方向に乖離」と報告されたまま未解消。このまま公開用に正本を配置すると、Local だけにある修正を消すか、GitHub だけにある実装（header のドロップダウンナビ等）が欠ける。 | grok-theme-reflection-done-2026-11-18.md、sp158-formal-dryrun-maou（4ファイル一致のみ） | 魔王ちゃんが Local の同じパスの md5 を取り、下の §4 の正本 md5 と照合（読み取りのみ）。不一致ファイルだけ Claude が差分を見て正本へ統合。 |
| E2 | 公開阻害（オーナー判断待ち） | 消費税：Local は税計算が完全に無効で、チェックアウトの税額は0。表示価格が税込みかどうかの扱いが未決定。 | site-wide-acceptance-retest-2026-11-13.md 47行・72行 | 決めるのはオーナー。Claude は決定後に表示・設定を合わせる。 |
| E3 | 公開阻害（未実施） | 実機 iPhone での確認が一度もできていない（Live Link が全パス404）。 | site-wide-acceptance-retest-2026-11-13.md 58行 | 魔王ちゃんの実機で確認できる経路ができ次第。コード修正ではない。 |
| E4 | 公開阻害（承認待ち） | 実決済の確認は未実施（Local はオフライン決済のみ PASS）。 | 同 72行 | 承認・審査後。コード修正ではない。 |
| E5 | 機能（仕様と実装の差） | ホーム PC 版：正本 front-page.php は「ヒーロー画像1枚＋（設定があれば）PC動画」。完成計画（f8952bf §6）の「画像3枚の縦スクロール、パララックスはPCのみ、動画なし」とは違う。モバイル版は正本どおり画像5枚（ID 18930/18932/18933/18934縦/18935）のパン＋クロスフェードで、計画と一致。 | local-snapshot-2026-11-15/theme/front-page.php 11〜30行・100〜120行 | どちらが最新の決定かを GLM が確定。Local に PC 動画が設定されているか（theme_mod nexus_pc_hero_video）は未確認。決定前に Claude は変更しない。 |

過去に問題だったが解消済みのもの（参考・再検証不要）：住所の町名欠落、未ログイン購入、BAG件数、ドロップダウンのはみ出し、配送対象国（いずれも 11-13 再テストで PASS）。

## 2. 過去の未決事項（最新決定を探した結果）
- **売り切れ表示**：11-16 に3者相談にかけられた（catalog-import-consult-two-items-2026-11-16.md）が、決定の記録は見つからない。現行テーマには在庫切れ専用の処理は無く、WooCommerce 標準のまま（在庫切れサイズは選べない。商品ごと在庫切れのときの一覧表示・非表示は Woo の設定次第で、Local の設定値は未確認）。
  - 選択肢（GLM 判断用）：A. 商品ページを残し「SOLD OUT」表示。B. 非公開（下書き）に戻す。C. サイズ単位は選択不可のまま、全サイズ在庫切れの商品だけ一覧から隠す（Woo 標準設定「在庫切れ商品を一覧に表示しない」）。在庫確認は週2回なので、A・C は確認の間に売り切れのまま表示される期間がある。B は再入荷時の復帰に手作業が要る。
- **メイン画像のルール（収集商品）**：同じく 11-16 の相談のまま決定記録なし。既存のオーナー決定（11-11）は「平置き写真があれば切り抜いてメイン、なければ着用写真。白・淡色は公式写真そのまま」で、これは自サイト登録用。
  - 選択肢（GLM 判断用）：A. 仕入先の1枚目をそのままメイン（加工なし）。B. 11-11 ルールを収集商品にも適用（平置きを切り抜き）。C. 仕入先の1枚目をメインにし、平置きがあればそれを優先（切り抜きなし）。

## 3. 公開阻害の修正状況
- Claude がコードで直せる公開阻害は現時点で E1 のみ。照合結果（魔王ちゃんの md5）待ち。E2〜E4 はオーナー判断・実機・承認待ちで、理由は上表のとおり。

## 4. 正本の md5（local-snapshot-2026-11-15/、画像を除く 21ファイル）
    ad863005fc64fe0cd03f3621d9130fa8  mu-plugins/ahc-fixture-guard.php
    8f9914ba1600c23ffd33abe6f344ba4d  mu-plugins/kaitsuke-tweaks.php
    b76dd5d9b32bc56d575a6ae2ca0e4820  mu-plugins/local-by-flywheel-live-link-helper.php
    a80b8bef5bdb2916530afaee5ef2f87c  mu-plugins/nexus-address-guard.php
    d8bd962878bdd94a0d3b8b3cc5dc1d09  mu-plugins/nexus-bag-sync.php
    8f9173c204ddd929d438fbbd7afa5f84  mu-plugins/nexus-catnav-autoclassify.php
    754d1fa15cf8fff186a601b715257926  mu-plugins/nexus-catnav-redirects.php
    4f6602c773da1344000556c28c56f665  mu-plugins/nexus-variation-gallery.php
    3b47530151f3e8d1dd530c304ca20736  theme/footer.php
    0645e902623ea75d13f506275a55b06b  theme/front-page.php
    031be6cccc0af38a154d17d7161cfbf7  theme/functions.php
    102c1823ed04e4923c1c079aea4c6980  theme/header.php
    e61165d6e6e739c26a1f0e1fdfe5085d  theme/index.php
    03599394466ae4231ee064d5d697ba20  theme/main.js
    e03cd7ab2d1ed166cce05327ca804627  theme/page.php
    71b0207762046f9603001eefa066fbde  theme/search.php
    67e4be36a7dc0cf872ee3c3b8fa42555  theme/style.css
    c2456959f321d0a317d53462df7916df  theme/taxonomy-product_cat.php
    53d2d7c24e5aafc5528f27fae64940e2  theme/woocommerce.php
    ea209dee80893b6f7036e834e5609ad5  theme/woocommerce/single-product.php
    93ce671fa4260b3bf46004a7c852c1ff  theme/woocommerce/single-product/product-image.php

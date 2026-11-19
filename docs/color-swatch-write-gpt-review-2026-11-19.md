# GPT検収：案B書込完了（2026-11-19）
対象：color-swatch-write-done-maou-2026-11-19.md、Claude 4feb28a の color_fullrun.py、dry-run報告・GPT検収。判定：現行シート反映は報告ベースで条件付き合格、追加商品生成は別ゲート。実シート・全行差分は本監査環境で未取得。33テストはMuse再実行報告でありGPT独立実行ではない。
## 検算
承認前4217/2857/4700/3、承認後6407/667/4700/3、双方11777。CONFIRMED純増2190、DRAFT純減2190。商品単位の承認前照合不一致0、保護列差分0、マスター1672一意、読戻し6列一致と報告。現行書込の再実行不要。承認後の全参照24299件のFK/scope/order検証結果、4×4遷移表、変更列別件数、非機密見本とハッシュを保存して検収証跡を補完する。
## コード直接監査：Claude担当への差分指示
1. swatch() はSPECIALをHEX CONFLICTより先に判定するため、MultiかつCONFLICTがUNKNOWNになる。HOLD優先に修正し、同一枠での競合テスト追加。
2. generate() はmaster.lookup(n, brand)にproduct_keyを渡していない（タイトル判定側も同様）。PRODUCT優先の仕様を満たすよう修正し、PRODUCT/BRAND/COMMON同名のfixtureで検証。
3. raw読込は同一内容の重複IDを許容する。報告の全重複停止仕様に合わせるか、明示した重複許容契約と件数記録を追加する。欠落ID、空IDもテスト。
4. recompute() はDERIVED外のswatch_reasonを上書きする。出力専用診断とするか保護列として保持し、changesとの契約を明示。現行シートの6列書込は報告上影響なし。
5. generateはSP/US固定。別店舗への汎用展開は未承認。新規商品追加前にshop/market/IDの契約を明確化する。主色候補の確定扱いもfamily_statusを検証する。
修正はClaude担当、Museはテスト再実行と現行バックアップで回帰比較。差異があれば理由を記録。現行シートに無条件再書込しない。
## Muse次工程
固有色は在庫ありdistinct商品数順に根拠付きで調査、172矛盾候補を共通原因別に分類、BUYMA公式色ID照合を並行。HOLD3は維持。承認済み近似HEXは実物の厳密色ではない。未承認HEXの本番表示・出品は禁止。価格・サイズ等の独立作業を止めない。本番WooCommerce変更なし。

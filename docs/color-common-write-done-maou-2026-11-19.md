# 共通化と承認19色の反映完了（魔王ちゃん、2026-11-19）

対象：GPT検収 color-common-specific-gpt-review-2026-11-19.md（a33dcd2）の指示。シートへ反映済み。再承認待ちなしの指示に基づき実施した。

## 手順と結果

### 1. バックアップ
- 反映前のシート全量を取得し保存（カラーマスター1,672行、商品カラー11,777行）。書き込み前の分布は6,407／667／4,700／3で、前回の読み戻し検証と一致。

### 2. 共通化の反映
- scope変換590行（BRAND→COMMON）。Phantomの旧3行（C-2662／C-2663／C-2664）はBRANDのまま履歴保持し、active=FALSE、review_noteに統合先（canonical_color_id: C-0007）を記録。
- 商品の構成色参照の付け替え35件（35商品）。
- 再計算はClaudeの最新版color_fullrun.py（4a32ebd5、テスト47件全合格を再実行で確認）を使用。不一致0件、再実行一致。
- 読み戻し検証：全1,672行保持、active 1,669行、activeの正規化名は一意、全24,299参照がactiveのCOMMONを指し旧ID参照は0件、派生列は再計算結果と差分0件、保護列はバックアップと差分0件。
- 基準分布（共通化後）：CONFIRMED 6,415／DRAFT 676／UNKNOWN 4,683／HOLD 3。dry-runの予測と一致。

### 3. 承認19色の反映
- 19色すべてにGPT指定の表示用近似HEXを設定し、hex_statusをAPPROVED_APPROXへ変更。review_noteに承認記録と根拠（画像サンプル候補の採用／既存値の維持／サンプル不採用でGPT指定値の採用）を保存した。既存の承認値との競合は0件。
- 再計算と読み戻し検証：派生列は再計算結果と差分0件、保護列は共通化後の状態と差分0件。
- 最終分布：CONFIRMED 7,119／DRAFT 402／UNKNOWN 4,253／HOLD 3（確定率は54.4%→60.4%）。

### 4. 未解決色リストの更新
- activeな色で未承認のものは1,632色。active ID別のdistinct商品数・在庫あり商品数で再集計し、docs/color-unresolved-after-common-2026-11-19.csv に登録した。
- 在庫あり商品数が多い順の上位：Multicolor 53（単色HEXは付けない特殊色）、Varsity Red 52、Silver Metallic 49、Metallic Gold 48、Gym Red 47、Wolf Grey 43、Cream White 39、Cool Grey 38、Midnight Navy 36、University Blue 36、Fire Red 35、Dark Smoke Grey 34、Light Orewood Brown 33、Khaki 31、Gold Metallic 29。

## 次の工程（GPTの作業順序の続き）
- 残りの色を既存パレットで一括解決（明示色語＋既存近似パレット、未知語のみ画像確認）。
- 真の矛盾172件の共通原因別整理、BUYMA公式色IDの照合は継続。

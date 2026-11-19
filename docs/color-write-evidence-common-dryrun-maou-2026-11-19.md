# 検収証跡の補完と共通化dry-run（魔王ちゃん、2026-11-19）

対象：GPT検収 color-swatch-write-gpt-review-2026-11-19.md の「検算」補完依頼と、オーナー決定965d6d3（カラーマスター全ブランド共通）の優先適用。シートは変更していない（dry-run）。

## 1. 書き込み検収の証跡補完

### 状態遷移表（行＝書き込み前、列＝書き込み後、単位：商品）
| 前＼後 | CONFIRMED | DRAFT | UNKNOWN | HOLD | 合計 |
|---|---|---|---|---|---|
| CONFIRMED | 6,401 | 425 | 0 | 0 | 6,826 |
| DRAFT | 6 | 242 | 4,679 | 3 | 4,930 |
| UNKNOWN | 0 | 0 | 21 | 0 | 21 |
| HOLD | 0 | 0 | 0 | 0 | 0 |
| 合計 | 6,407 | 667 | 4,700 | 3 | 11,777 |

### 変更列別の件数
- swatch_hex_1（X列）：1,723件
- swatch_hex_2（Y列）：1,297件
- swatch_hex_3（Z列）：936件
- swatch_status（AA列）：5,113件（遷移表の非対角合計と一致）
- search_families_json（AE列）：3,434件
- search_families_candidates_json（AF列）：新規列として11,777件

### 参照整合（書き込み後の全件検証）
- 構成色の参照は全24,299件。存在しないcolor_idへの参照は0件。
- 構成色の順序（position昇順）の不整合は0件。
- 参照先scopeの内訳：COMMON 22,925件／BRAND 1,374件。

### ファイルハッシュ（SHA-256先頭16桁）
- backup_master.csv：e810d2a91d6679d4
- backup_products.csv：8a4df29fcbd3cf02
- updated_master.csv：49e641512ae4899a

## 2. 共通化dry-run（正規化色名ごとに共通IDへ統合）

### 前提
- オーナー決定：カラーマスターは全ブランド共通とし、正規化色名を一意キーにする。丸窓の目的はバリエーションの認識であり、実物色の厳密な再現ではない。
- 対象はscopeがBRANDの行を含む590色名。PRODUCT scopeの行は存在しない。
- 統合ルール：共通（COMMON）行があればそれを正とする。なければ参照数が最も多い行を正とし、その行のscopeをCOMMONへ変換する。承認済みHEXが1種類だけならそれを共通HEXとする。承認値が競合する色名は保留にする。旧行は削除せず非アクティブ化し、旧ID→共通IDの対応表を残す。

### 結果
- scope変換のみで済む色名：589件（その色名の行が1行だけで、IDも参照も変わらない）。
- ID統合が発生する色名：Phantomのみ。C-2662（NEW BALANCE）・C-2663（JORDAN）・C-2664（SALOMON）を C-0007（NIKE、承認済み近似HEX #E7E2D9）へ統合。C-0007のscopeはCOMMONへ変換。
- 承認HEXの競合：0件。系統（family）の確定値の競合：0件。
- 参照の付け替え：35件（35商品）。
- 対応表：docs/color-common-mapping-dryrun-2026-11-19.csv（統合3行）、docs/color-common-conversions-dryrun-2026-11-19.csv（scope変換590行）。

### 分布への影響（dry-run再計算）
- 変化するのはPhantom統合分のみ：CONFIRMED 6,407→6,415、DRAFT 667→676、UNKNOWN 4,700→4,683、HOLD 3→3。
- scope変換だけの589色名は、ID・HEX・系統が変わらないため分布に影響しない。

## 3. 参考：表記ゆれの色名（今回の対象外、別途判断用）
原文の綴り違いが別トークンになっている例を確認した。共通化とは別の正規化課題として記録する。
- chesnut（C-2570）／chestnut（C-2571）、aurura ivy／aurora ivy、better sarlet／better scarlet、core balck、saill、whte、torquoise、mutli color／mulit、lunar eock／lunar rock、stoneare／stoneware、rain cloud／raincloud、timber wolf／timberwolf、fresh water／freshwater、dark sulfur／dark sulphur、zero metalic／zero metallic、casterock／castle rock、tatto silt／tattoo silt。

## 次の手順案
1. このdry-runの検収後、バックアップを取得してから共通化をシートへ反映（scope変換590行、統合3行の非アクティブ化、参照付け替え35件、派生列の再計算と読み戻し検証）。
2. あわせて、頻度の高い未確定色の近似HEX承認（画像サンプリング根拠は docs/color-specific-evidence-maou-2026-11-19.md、f010198a）を進めると、UNKNOWNの削減が大きくなる。

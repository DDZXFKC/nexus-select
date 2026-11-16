# 既存SQLite実物確認（2026-11-16、魔王ちゃん調査）

保存の仕組み統合最終案の「次のステップ1：既存DB実物の確認」の結果。

## 確認できた実物

### 1. BSTN収集DB群（iMac外付けボリュームのアーカイブ内）
場所：`/Volumes/Macintosh HD/Users/discodadz/nexus-archive-2026-11-15/pkg-s27-recon/`
- bstn-s29-*.sqlite ×7（men/women/kids × footwear/apparel/accessories/lifestyle、55MB〜539MB）。payload形式で1行＝1サイズバリアントの生収集DB。
- bstn-s27.sqlite（12MB）、bstn-s25-trial.sqlite（3.3MB）
- stage2_integrated_new.sqlite（229KB）、stage2_history_new.sqlite（86KB）
- nexus_*_new.sqlite 等の小規模作業DB ×5（各57〜61KB）
性質：BSTN専用・カテゴリー別に分割された生データのアーカイブ。新方式の「ショップ別原本（L0）」に相当するが、複数ショップ共通の正本としては作られていない。

### 2. GLM発掘システム（sourcing rev2）
- DBパスはCLI引数（--db）で渡す方式。VMワークスペース内に常駐する共有DBファイルは存在しない（実行成果物はCSV/JSON）。
- スキーマはコード側（online_workflow.py の init()）に定義されている。

### 3. AHC System（自動買付側）ahc.db
場所：`~/workspace/ahc-run/data/ahc.db`
- テーブル12件：stores／products／store_products／coupons／coupon_sources／orders／order_items／purchase_plans／purchase_records／cost_components／coupon_attempts／compliance_records
- 中身はほぼ空（products 0件、stores 0件、coupons 1件、coupon_sources 1件）。
- 目的は買付実行側であり、収集・判定・出力の正本ではない。ただし products／store_products／coupons の概念は新方式と重なる。

### 4. iMac本体（~/nexus-select）には .db／.sqlite ファイルなし（走査378件で0件）。

## 結論（事実ベース）
- 「既存の収集用SQLiteをそのまま拡張して正本にする」対象は厳密には存在しない。候補は次の3解釈：
  - A：GLM発掘システムのスキーマ（コード定義）を土台に新規DBを起こす（現行の実行系に一番近い）。
  - B：ahc.db のテーブル概念（products／store_products／coupons）を土台にする（買付側と共有できるが現状は空で、目的が違う）。
  - C：BSTNの stage2_integrated_new.sqlite を土台にする（実データはあるがBSTN専用設計）。
- BSTNの s29 DB群は、どの案でも「BSTNのL0原本アーカイブ」として位置づけるのが自然。
- 次ステップ（L0〜L4テーブル設計案）は、この実物確認を前提に3者で詰める。

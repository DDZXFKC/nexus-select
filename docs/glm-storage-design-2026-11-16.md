# L0〜L4テーブル設計案（GLM、2026-11-16）

前提：既存SQLite実物確認（sqlite-inventory-2026-11-16.md）。GLMの土台推奨はA（発掘システムのスキーマを土台に新規DB）。GPT・Claudeの設計案と合わせて統合する前のGLM単独案。

---

### 土台の推奨：A（GLM発掘システムのスキーマを土台に新規DBを起こす）

理由：GLM発掘システムは既に複数ショップ対応を想定し、CLI引数でDBパスを渡す設計のため拡張性が高い。ahc.dbは買付実行側で収集とは目的が異なり、stage2_integrated_new.sqliteはBSTN専用で汎用性に欠ける。BSTNのs29群はL0原本アーカイブとして新規DBへ統合する。

### L0〜L4 テーブル設計案

**L0: shop_raw_records（店別原本）**
| 列 | 型 | 説明 |
|---|---|---|
| id | INTEGER PK | 自動採番 |
| shop_code | TEXT | ショップコード（bstn/sp/kith等） |
| run_id | TEXT | 実行ID |
| raw_payload | TEXT | JSON形式の生データ |
| source_url | TEXT | 取得元URL |
| fetched_at | DATETIME | 取得日時 |
| content_hash | TEXT | 内容のhash |

**L1: shop_products（店別抽出・商品）**
| 列 | 型 | 説明 |
|---|---|---|
| id | INTEGER PK | 自動採番 |
| shop_code | TEXT | ショップコード |
| shop_product_id | TEXT | ショップ側商品ID |
| brand | TEXT | ブランド名 |
| product_name | TEXT | 商品名 |
| gender | TEXT | Men/Women/Kids |
| category_hint | TEXT | 元データの部門・コレクション |
| color | TEXT | カラー |
| raw_record_id | INTEGER FK | L0への参照 |
| extracted_at | DATETIME | 抽出日時 |

**L1: shop_variants（店別抽出・サイズバリアント）**
| 列 | 型 | 説明 |
|---|---|---|
| id | INTEGER PK | 自動採番 |
| shop_product_id | INTEGER FK | shop_productsへの参照 |
| size_label | TEXT | サイズ表記（例: 3.5Y（22.5cm）） |
| size_us | TEXT | USサイズ |
| size_cm | TEXT | cmサイズ |
| size_age_group | TEXT | men/women/kids |
| stock_status | TEXT | available/unavailable/unknown |
| raw_record_id | INTEGER FK | L0への参照 |

**L2: shop_coupons（店別条件・クーポン）**
| 列 | 型 | 説明 |
|---|---|---|
| id | INTEGER PK | 自動採番 |
| shop_code | TEXT | ショップコード |
| coupon_code | TEXT | クーポンコード（例: FLASH30） |
| discount_rate | REAL | 割引率（0.30） |
| valid_from | DATE | 有効期限開始 |
| valid_to | DATE | 有効期限終了 |
| conditions | TEXT | 適用条件（JSON） |
| exclusions | TEXT | 適用不可条件（JSON） |
| fetched_at | DATETIME | 取得日時 |

**L2: shop_pricing（店別条件・価格観測）**
| 列 | 型 | 説明 |
|---|---|---|
| id | INTEGER PK | 自動採番 |
| shop_variant_id | INTEGER FK | shop_variantsへの参照 |
| original_price | REAL | 現地価格 |
| currency | TEXT | 通貨（USD/EUR/GBP） |
| exchange_rate | REAL | 為替レート |
| exchange_date | DATE | 為替取得日 |
| coupon_id | INTEGER FK | shop_couponsへの参照（nullable） |
| coupon_applied | BOOLEAN | クーポン適用可否 |
| final_cost | REAL | 仕入総額（クーポン適用後） |
| shipping_cost | REAL | 送料 |
| agent_fee | REAL | 代行費 |
| observed_at | DATETIME | 観測日時 |
| stale_flag | BOOLEAN | 3.5日以上経過でtrue |

**L3: decision_runs（比較判定・採用決定）**
| 列 | 型 | 説明 |
|---|---|---|
| id | INTEGER PK | 自動採番 |
| run_id | TEXT | 判定実行ID |
| product_key | TEXT | 商品識別キー（ブランド+品番+カラー） |
| decided_shop_code | TEXT | 採用ショップ |
| decided_variant_id | INTEGER | 採用バリアントID |
| decision_reason | TEXT | 採用理由 |
| decided_at | DATETIME | 決定日時 |
| manual_override | BOOLEAN | 手動上書きフラグ |
| override_by | TEXT | 上書き者 |
| override_at | DATETIME | 上書き日時 |

**L3: decision_candidates（比較判定・候補一覧）**
| 列 | 型 | 説明 |
|---|---|---|
| id | INTEGER PK | 自動採番

**L3: decision_candidates（比較判定・候補一覧）**
| 列 | 型 | 説明 |
|---|---|---|
| id | INTEGER PK | 自動採番 |
| run_id | TEXT | 判定実行ID |
| product_key | TEXT | 商品識別キー |
| shop_code | TEXT | 候補ショップコード |
| shop_variant_id | INTEGER | 候補バリアントID |
| final_cost | REAL | 仕入総額 |
| stock_status | TEXT | 在庫ステータス |
| stale_flag | BOOLEAN | 鮮度低下フラグ |
| rank | INTEGER | 優先順位（1=採用、2以降=代替） |
| reject_reason | TEXT | 落選理由（価格高・在庫無等） |

**L4: export_woo_csv（WooCommerce投入用出力履歴）**
| 列 | 型 | 説明 |
|---|---|---|
| id | INTEGER PK | 自動採番 |
| decision_run_id | INTEGER FK | decision_runsへの参照 |
| sku | TEXT | WooCommerce用SKU（例: SP-123） |
| csv_row_data | TEXT | CSV1行分のデータ（JSONまたはCSV文字列） |
| category_ids | TEXT | 付与するカテゴリーID（カンマ区切り） |
| backup_offers_json | TEXT | 代替仕入先情報（JSON配列） |
| exported_at | DATETIME | 出力日時 |

**L4: export_buyma（BUYMA用出力履歴）**
| 列 | 型 | 説明 |
|---|---|---|
| id | INTEGER PK | 自動採番 |
| decision_run_id | INTEGER FK | decision_runsへの参照 |
| buyma_sku | TEXT | BUYMA用SKU |
| csv_row_data | TEXT | CSV1行分のデータ |
| exported_at | DATETIME | 出力日時 |

**L4: export_owner_view（確認用シート出力）**
| 列 | 型 | 説明 |
|---|---|---|
| id | INTEGER PK | 自動採番 |
| decision_run_id | INTEGER FK | decision_runsへの参照 |
| product_name | TEXT | 商品名 |
| decided_shop | TEXT | 採用ショップ |
| final_price | REAL | 販売価格 |
| backup_shops_summary | TEXT | 代替仕入先一覧（可読テキスト） |
| exported_at | DATETIME | 出力日時 |
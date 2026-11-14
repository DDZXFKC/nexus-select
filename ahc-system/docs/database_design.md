# Database design

All amounts are stored as integers in the **minor unit** of their
currency (cents for EUR/USD/GBP, yen for JPY). This avoids float drift
across currencies and lets us compute totals with integer arithmetic.

## Engines supported

| Driver | `AHC_DB_URL` example |
| --- | --- |
| SQLite (default) | `sqlite:///./data/ahc.db` |
| PostgreSQL | `postgresql+psycopg2://user:pass@host:5432/ahc` |
| MySQL | `mysql+pymysql://user:pass@host:3306/ahc` |
| Supabase | same as Postgres, with pooler host |

No code changes are needed to switch — `ahc.db.session._build_engine`
inspects the URL scheme.

## ER overview

```
stores 1───* store_products *───1 products
  │                                     
  │                                    
  *                                    
coupons *───1 coupon_sources           
  │                                    
  *                                    
coupon_attempts                        
                                       
orders 1───* order_items 1───* purchase_plans 1───1 purchase_records
                                │
                                └───* cost_components
                                        
compliance_records *───1 stores
```

## Table reference

### `stores`
Retailer master + software switches. The compliance gate is the
*real* switch; `enabled_scrape` / `enabled_buy` are additional
software gates.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | int PK | |
| `slug` | str, unique | e.g. `bstn` |
| `name`, `country`, `currency`, `base_url` | str | |
| `ec_platform` | str | `shopify` / `magento` / `woocommerce` / `generic` |
| `adapter_class` | str? | FQCN override |
| `enabled_scrape`, `enabled_buy` | bool | defaults false |
| `notes` | text? | |

### `products`
Canonical product row. `external_source` + `external_id` mirror the
existing collection system's PK so we can join without rewriting it.

### `store_products`
One row per (store, product) listing. Holds the per-store SKU, URL,
observed price (minor unit + currency), stock status, sizes (JSON
array), `last_checked_at`.

### `coupon_sources`
One row per source we collect from (RetailMeNot, mydealz, ...).

### `coupons`
The deduplicated, normalised coupon master. Unique on
`(store_id, code, source_id)`. Status enum:
`unverified / verified_valid / verified_invalid / expired / blacklisted`.

`coupon_attempts` is the append-only history of every apply attempt —
including failures — so we never retry a known-bad code against the
same store (Chapter 5(7) + Chapter 9).

### `orders` / `order_items`
BUYMA / After Hours Club orders ingested from email. Unique on
`(source, external_order_id)`. Status enum:
`received / planned / buying / bought / failed / cancelled / manual`.

`manual` means "Python cannot process this — hand off to a human"
(Chapter 6).

### `purchase_plans`
One candidate source + cost breakdown per order item. Multiple plans
per item let us compare. The chosen one has `selected=True`.

### `cost_components` (Chapter 7)
One row per `(plan_id, cost_type)`. `cost_type` covers every Chapter 7
component: `item_price`, `coupon_discount`, `local_tax`,
`local_shipping`, `intl_shipping`, `customs_duty`, `import_tax`,
`procurement_fee`, `dispatch_fee`, `fx_fee`, `platform_fee`,
`cashback`, `other`.

`amount_minor` is in source currency; `amount_jpy_minor` is the
FX-converted JPY; `is_estimate=True` marks lines that are NOT to be
counted in confirmed totals (Chapter 7: unverified coupons and future
cashback never enter confirmed profit).

### `purchase_records`
One row per plan (`UniqueConstraint(plan_id)`). Status enum:
`planned / cart_prepared / awaiting_approval / submitted / confirmed /
unknown / failed`.

`requires_approval=True` is the default and only ever cleared by a
human. `unknown` is the dangerous state — Chapter 9 forbids auto-retry.

### `compliance_records`
Per-store robots.txt + ToS snapshot history. Append-only; the gate
reads the latest row's effective verdict.

## Indexes

The models declare indexes on every column that appears in a `WHERE`
or `JOIN` clause:
- `ix_coupon_status`, `ix_coupon_expiry` — expiry sweep
- `ix_ca_coupon_status` — find recent attempts for a coupon
- `ix_oi_order`, `ix_pp_oi_selected` — plan selection per order item
- `ix_cc_plan_type` — cost rollup per plan
- `ix_cr_store_checked` — latest compliance snapshot

## Bootstrap

```bash
PYTHONPATH=src python -m ahc.cli init            # create tables
PYTHONPATH=src python -m ahc.cli stores seed     # upsert all stores
```

To start over in dev: `python -m ahc.cli init --drop`.

## Existing-collection-system mirror

The `products` table has `external_source` (default `"existing"`) and
`external_id` (the existing system's PK). The `AHC_EXISTING_DB_URL`
env var points at a read-only connection to the existing DB; AHC
copies only what it needs (PK, brand, model, colorway, SKU, GTIN) into
its own `products` table on demand. See `docs/integration_spec.md`.

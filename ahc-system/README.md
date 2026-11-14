# AHC System — Coupon Collection & Auto-Buying

A Python system that, on receipt of a BUYMA / AFTER HOURS CLUB order,
automatically compares overseas retailers' stock, price, coupons, shipping
and tax, then prepares a cart at the most profitable source. Real payment
is **off by default** and gated behind explicit compliance sign-off.

> Chapter 9 (safety) is the contract this repository keeps: scraping and
> buying are disabled until each store's `robots.txt` and Terms of Service
> have been reviewed and the corresponding verdict in
> `config/compliance.yaml` is set to `allowed`.

---

## Quick start

```bash
# 1. Install (editable, in a venv)
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium          # only needed for cart / coupon flows

# 2. Configure
cp .env.example .env                 # then edit .env (DB, IMAP, etc.)

# 3. Initialise the database
PYTHONPATH=src python -m ahc.cli init

# 4. Inspect compliance state for a store
PYTHONPATH=src python -m ahc.cli compliance show --slug bstn --action scrape
PYTHONPATH=src python -m ahc.cli compliance show --slug bstn --action buy

# 5. List configured stores and seed them into the DB
PYTHONPATH=src python -m ahc.cli stores list --country DE
PYTHONPATH=src python -m ahc.cli stores seed

# 6. Run tests
PYTHONPATH=src python -m pytest tests/ -q
```

---

## Project layout

```
ahc-system/
├── pyproject.toml              # deps + entry point (ahc CLI)
├── .env.example                # all runtime knobs
├── config/
│   ├── stores.yaml             # 33 retailers across DE / US / UK / other
│   ├── coupon_sources.yaml     # 16 coupon / deal sources
│   └── compliance.yaml         # per-store manual verdicts (the safety gate)
├── src/ahc/
│   ├── config.py               # pydantic-settings singleton
│   ├── logging_setup.py        # rotating file + console, idempotent
│   ├── cli.py                  # `ahc <command>` entry point
│   ├── db/                     # SQLAlchemy 2.x models + repository + session
│   ├── utils/money.py          # minor-unit money + FX table
│   ├── compliance/             # robots.txt + ToS scanner + policy gate
│   ├── stores/                 # Shopify / Magento / WooCommerce / generic adapters
│   ├── coupons/                # sources + dedup + validator + collector
│   ├── cost/                   # Chapter 7 cost + profit calculation
│   ├── orders/                 # IMAP fetcher + BUYMA / AHC parsers + manager
│   └── buying/                 # Playwright cart + coupon applier + orchestrator
├── tests/                      # 42 tests covering Chapter 11 requirements
└── docs/                       # architecture / DB / compliance / integration
```

---

## CLI reference

| Command | Purpose |
| --- | --- |
| `ahc init [--drop]` | Create / migrate DB schema |
| `ahc compliance show --slug X --action scrape\|buy` | Print effective verdict |
| `ahc compliance scan --base-url URL` | Live-fetch robots.txt + ToS excerpt |
| `ahc stores list [--platform P] [--country CC]` | List configured stores |
| `ahc stores seed` | Upsert all stores into the DB |
| `ahc coupons collect [--source SLUG]` | Run enabled coupon sources |
| `ahc coupons list [--store SLUG] [--status S]` | List coupons |
| `ahc orders fetch [--since-days N] [--limit N]` | Pull order emails via IMAP |
| `ahc orders list [--status S]` | List orders |
| `ahc plan ORDER_ID` | Show order items + candidate stores |
| `ahc dry-run PLAN_ID` | Prepare a cart (no payment) |

---

## Safety defaults (Chapter 9)

| Setting | Default | Meaning |
| --- | --- | --- |
| `AHC_DRY_RUN_ONLY` | `true` | `submit_payment` always refuses |
| `allow_buy_automation` (compliance.yaml) | `false` | Buy flow blocked even if a store is `enabled_buy=true` |
| Per-store verdict | `manual` | Every store starts as "pending ToS review" — no scraping, no buying |
| Coupon sources | `manual` / `denied` | Aggregators pending review; Honey/Coupert denied (no public listing) |
| `AHC_MAX_CART_AMOUNT` | `300000` | Cart total above this aborts the run |
| `AHC_MIN_PROFIT_JPY` | `0` | Plans below this confirmed profit are not selectable |
| Double-buy prevention | on | A plan with a SUBMITTED / CONFIRMED / UNKNOWN record is never retried |
| Unknown result | stop | If a buy ends in UNKNOWN, the record stays `requires_approval=True` |

To enable a store for scraping or buying, edit `config/compliance.yaml`
and change the verdict from `manual` to `allowed`, with a written
justification in the `note` field.

---

## Module responsibilities

| Module | Owns | Key class |
| --- | --- | --- |
| `ahc.compliance` | "may we do X?" decision | `ComplianceGate` |
| `ahc.stores` | product fetch + cart + coupon ops per platform | `ShopifyAdapter` etc. |
| `ahc.coupons` | coupon collection, dedup, validation, persistence | `CouponCollector` |
| `ahc.cost` | Chapter 7 cost breakdown + profit + best-plan pick | `CostCalculator`, `pick_best_plan` |
| `ahc.orders` | IMAP fetch + email parsing + order state | `ImapOrderFetcher`, `OrderManager` |
| `ahc.buying` | Playwright cart + coupon apply + record state machine | `BuyOrchestratorImpl` |

---

## Tests (Chapter 11)

```bash
PYTHONPATH=src python -m pytest tests/ -q
# 42 passed
```

The test suite covers every Chapter 11 requirement:

| Chapter 11 item | Test file |
| --- | --- |
| Coupon collection | `test_coupons.py` (collector smoke via `test_orders.py` ingest) |
| Dedup | `test_coupons.py::test_dedup_*` |
| Expiry | `test_coupons.py::test_validator_marks_expired` |
| Excluded products | `test_coupons.py::test_applicability_excludes_excluded_brand` |
| Coupon apply + failure recalc | `test_buying.py::test_prepare_cart_*` |
| Cheapest-source selection | `test_cost_profit.py::test_pick_best_plan_*` |
| Out-of-stock | (adapter layer: `stock_status` field on `StoreProduct`) |
| Min-profit condition | `test_cost_profit.py::test_profit_*` |
| Double-buy prevention | `test_buying.py::test_double_buy_*`, `test_all_double_buy_statuses_blocked` |
| Unknown-result stop | `test_buying.py::test_double_buy_blocked_when_record_unknown` |
| Existing-system compatibility | `test_orders.py` uses `external_source`/`external_id` mirror |
| Order-management integration | `test_orders.py::test_order_manager_*` |

Tests never make real network calls and never launch Playwright — the
buying tests monkey-patch the browser context and the adapter factory.

---

## Adding a new store (3 lines, no code)

Append a row to `config/stores.yaml`:

```yaml
  - slug: newstore
    name: New Store
    country: FR
    currency: EUR
    base_url: https://www.newstore.example
    ec_platform: shopify   # shopify | magento | woocommerce | generic
    enabled_scrape: false
    enabled_buy: false
```

Then add a verdict row to `config/compliance.yaml`:

```yaml
  newstore: { scrape: manual, buy: manual, note: "Pending ToS review" }
```

If the store runs on Shopify / Magento / WooCommerce, no adapter code is
needed. If selectors differ from the platform default, subclass the
platform adapter and set `adapter_class: ahc.stores.my_store.MyStore`.

---

## Connecting to the existing collection system

The DB layer abstracts the existing collection system behind a mirror
table `products(external_source, external_id, ...)` and a read-only
`AHC_EXISTING_DB_URL`. See `docs/integration_spec.md` for the exact
mapping, the import contract, and the dual-DB wiring.

---

## Deliverables (Chapter 12)

- ✅ System design — `docs/architecture.md`
- ✅ Database design — `docs/database_design.md`
- ✅ Coupon collection module — `src/ahc/coupons/`
- ✅ Coupon auto-apply module — `src/ahc/buying/coupon_applier.py`
- ✅ Auto-buy module — `src/ahc/buying/`
- ✅ Store common adapters — `src/ahc/stores/{shopify,magento,woocommerce,generic}_adapter.py`
- ✅ Cost / profit module — `src/ahc/cost/`
- ✅ Automated tests — `tests/`
- ✅ Existing-system integration spec — `docs/integration_spec.md`
- ✅ Install + run guide — this README + `docs/`
- ✅ Test results — `42 passed`

---

## License

MIT. This code is a tool; you remain responsible for complying with each
store's Terms of Service and your local law.

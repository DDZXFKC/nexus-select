# Architecture

## Design goals (from the spec)

1. Don't break the existing collection system — AHC is an *independent
   module* that reads from a mirror of the existing product DB.
2. Adding a store must not require large-scale development — store-specific
   config lives in YAML, platform-specific code lives in one adapter class.
3. Free / open-source stack only.
4. Every network action passes a compliance gate first (Chapter 9).
5. Real purchases are off until explicitly approved (Chapter 9).

## Layered view

```
                ┌───────────────────────────────────────────────┐
                │  CLI (ahc.cli)                                │
                │   init / stores / coupons / orders / plan /   │
                │   compliance / dry-run                        │
                └───────────────┬───────────────────────────────┘
                                │
        ┌───────────────────────┼────────────────────────────────┐
        │                       │                                │
┌───────▼─────────┐  ┌──────────▼──────────┐  ┌─────────────────▼──────┐
│ orders          │  │ buying              │  │ coupons                │
│  IMAP fetcher   │  │  CartBuilder        │  │  sources (16)          │
│  parsers        │  │  CouponApplier      │  │  dedup                 │
│  OrderManager   │  │  BuyOrchestrator    │  │  validator             │
└───────┬─────────┘  └──────────┬──────────┘  └─────────────────┬──────┘
        │                       │                                │
        └───────────┬───────────┴────────────┬───────────────────┘
                    │                        │
          ┌─────────▼──────────┐  ┌──────────▼───────────────┐
          │ cost               │  │ stores                   │
          │  CostCalculator    │  │  Shopify / Magento /     │
          │  profit + picker   │  │  WooCommerce / Generic   │
          └─────────┬──────────┘  │  + http + browser        │
                    │             └──────────┬───────────────┘
                    │                        │
          ┌─────────▼──────────┐  ┌──────────▼───────────────┐
          │ utils.money        │  │ compliance               │
          │  minor-unit money  │  │  robots.txt + ToS        │
          │  + FX table        │  │  ComplianceGate (policy) │
          └────────────────────┘  └──────────┬───────────────┘
                                              │
                                       ┌──────▼──────┐
                                       │ config.yaml │
                                       │ (verdicts)  │
                                       └─────────────┘
                    │
          ┌─────────▼──────────────────────────────┐
          │ db (SQLAlchemy 2.x)                    │
          │  Base / models / session / repository  │
          │  SQLite (default) | Postgres | MySQL   │
          └────────────────────────────────────────┘
```

## Cross-cutting contracts

### Money

All amounts are integers in the minor unit of their currency (`1999` =
19.99 EUR, `250000` = 2500.00 JPY). Conversion happens in exactly one
place: `ahc.utils.money`. Every other module passes minor units around.

### Compliance gate

Every store adapter and coupon source consults the gate before any
network call. The gate is a single decision point: `allow_scrape(slug)`
or `allow_buy(slug)` returns a `Verdict(allowed, reason, source,
requires_human)`. The verdict is deterministic and config-driven; no
machine learning, no probabilistic checks.

### Adapter pattern

`AbstractStoreAdapter` defines the contract. Platform adapters
(Shopify / Magento / WooCommerce / Generic) implement most of it; a
store-specific subclass only overrides selectors that differ. The
registry (`stores.registry.adapter_for`) resolves the right class from
`ec_platform` or an explicit `adapter_class` override in YAML.

### Repository pattern

`ahc.db.repository.Repository[T]` is a thin CRUD layer over SQLAlchemy.
It keeps call sites off `Session` so we can later swap SQLite for
Postgres / Supabase without touching business logic. The
`upsert_by(filters, defaults)` method is the workhorse for idempotent
ingestion (coupons, orders, store master).

### State machine

`PurchaseRecord` is the heart of the buy flow. Status transitions:

```
PLANNED → CART_PREPARED → AWAITING_APPROVAL → (human approves) → SUBMITTED
                                │                                   │
                                └─► FAILED                         CONFIRMED
                                                                    │
                                                                    └─► UNKNOWN  (no auto-retry)
```

A `UniqueConstraint(plan_id)` ensures at most one record per plan.
`_DOUBLE_BUY_STATUSES = {submitted, confirmed, unknown}` is the set that
blocks new attempts — Chapter 9.

## Failure isolation (Chapter 10)

- Coupon collector wraps each `source.fetch()` in try/except — one dead
  source does not stop the others.
- IMAP fetcher returns what it has so far on any per-message error.
- Buying orchestrator catches `StoreAdapterError` separately from
  generic `Exception` so adapter bugs become `FAILED` records, not
  crashes.
- Tests run in an in-memory SQLite that is dropped between cases.

## Resume-from-diff (Chapter 10)

- `orders.status` is the cursor: `received → planned → buying → bought`.
- `purchase_records.status` is the cursor per plan.
- `coupon_attempts` records every apply (incl. failures) so we don't
  retry a known-bad code against the same store.
- Re-running `ahc coupons collect` is safe — `upsert_by` makes it
  idempotent.

## What is intentionally NOT here

- **Payment adapters.** `submit_payment` raises `BuyError` even when
  the dry-run guard and approval token pass. Per-store checkout needs
  its own compliance sign-off and a dedicated adapter — Chapter 14
  says "real purchases only after the necessary approvals".
- **A UI.** The spec did not ask for one. The CLI is the surface.
- **A scheduler.** Run via cron / systemd; the system itself is
  stateless between runs (DB is the state).
- **An FX service.** `FxTable` is in-memory; the buying module marks
  non-JPY cost lines as `is_estimate=True` with `note="FX pending"`
  rather than inventing a rate. Chapter 7 forbids guessing.

# Existing-system integration spec

The existing Python product-collection system is **external** to this
session — its source is not visible here. This document specifies the
contract AHC needs from it, and the exact points where the two systems
meet.

> The spec is filled in with **defaults AHC chose** where the existing
> system's details are unknown. When the existing system is shared,
> overwrite these defaults; the AHC side does not need code changes
> because every external dependency is behind an interface.

## Principle: read-only mirror, not a rewrite

Chapter 2 requires:
- Do not rewrite the existing system.
- Do not stop the running collection.
- Develop as an independent module.
- Reuse the existing product DB.

AHC achieves this by maintaining a small **mirror** of the existing
system's product table inside its own DB, refreshed on demand. The
existing system continues to own writes; AHC only reads (and copies
the minimal columns it needs).

## Integration points

### 1. Product lookup (`ahc.db.models.Product`)

AHC's `products` table has two columns that make the mirror explicit:

| Column | Purpose |
| --- | --- |
| `external_source` | Constant `"existing"` for rows mirrored from the existing system |
| `external_id` | The existing system's primary key (string, to tolerate any PK type) |

When AHC needs product info (brand, model, colorway, SKU, GTIN), it
joins on `(external_source, external_id)`. If a row is missing, AHC
calls the **Product Fetcher** interface (below) to populate it.

### 2. Product Fetcher interface (to be implemented per existing system)

```python
# src/ahc/integration/existing_products.py  (NOT YET WRITTEN)
from typing import Iterable, Optional
from ahc.db.models import Product

class ExistingProductFetcher:
    """Read-only adapter to the existing collection system's product DB."""

    def get_by_external_id(self, external_id: str) -> Optional[Product]: ...
    def search(self, *, brand: str | None, model: str | None,
               colorway: str | None, sku: str | None,
               gtin: str | None) -> Iterable[Product]: ...
    def list_recently_updated(self, since_hours: int = 24) -> Iterable[Product]: ...
```

Two implementations are supported:
- **SQLAlchemy cross-DB**: set `AHC_EXISTING_DB_URL` to the existing
  system's DB URL. The fetcher opens a second engine and maps the
  existing `products` table via a `declarative_base` that mirrors the
  columns AHC needs.
- **Python import**: if the existing system exposes a Python API
  (`from existing_scraper.products import get_product`), the fetcher
  delegates to it.

The choice is made in `ahc.integration.__init__` based on which env
var / config flag is set. Until then, AHC falls back to its own
`products` table only.

### 3. Store-product linkage

The existing collection system already scrapes per-store prices and
stock. AHC's `store_products` table is the **same shape** as the
existing system's per-store listing table (SKU, URL, price_minor,
currency, stock_status, sizes_available, last_checked_at).

Two options:
- **AHC reads the existing system's table directly** (cross-DB) — set
  `AHC_EXISTING_DB_URL`. AHC's `store_products` becomes a thin view
  over the existing table.
- **AHC ingests deltas** via a periodic job that copies new/updated
  rows from the existing system into AHC's `store_products`. This is
  the default; safer because it isolates AHC from the existing
  system's schema changes.

### 4. Order intake (BUYMA / After Hours Club)

AHC receives orders via IMAP (`ahc.orders.ImapOrderFetcher`). The
existing system is not involved in order intake.

If the existing system already has a BUYMA / AHC order table, AHC can
read from it instead — set `AHC_EXISTING_DB_URL` and implement an
`ExistingOrderFetcher` analogous to the product fetcher. Until then,
IMAP is the source.

## Information AHC needs from the existing system

To wire the integration, please share (any format; the closer to this
the less adapter code):

```yaml
existing_system:
  language: python 3.?
  package_manager: pip | poetry | uv | pipenv
  db:
    type: postgres | mysql | sqlite | other
    host: ...
    port: ...
    db_name: ...
    # Connection string format only (no credentials in writing):
    # e.g. postgresql+psycopg2://{user}:{pass}@{host}:{port}/{db}
    connection_string_format: postgresql+psycopg2://...

  product_table:
    name: products           # or whatever the existing system calls it
    primary_key: id          # column name
    columns:
      id: int | str | uuid
      brand: str
      model: str             # silhouette
      colorway: str
      sku: str
      gtin: str              # EAN / UPC for cross-store matching
      gender: str
      release_date: date
      image_url: str

  store_product_table:
    name: store_products
    primary_key: id
    foreign_keys:
      product_id: products.id
      store_id: stores.id
    columns:
      store_sku: str
      url: str
      price_minor: int       # or price_major float? please specify
      currency: str
      stock_status: str
      sizes_available: str   # JSON array? comma-separated?
      last_checked_at: datetime

  store_table:
    name: stores
    columns:
      slug: str
      name: str
      country: str
      currency: str
      base_url: str

  python_api:                 # if the existing system exposes one
    package: existing_scraper
    product_lookup: "existing_scraper.products.get_by_id"
    store_product_lookup: "existing_scraper.listings.get_by_product"
```

## What AHC does NOT need

- The existing system's scraping code (AHC has its own store adapters).
- The existing system's secrets / credentials (AHC uses its own
  settings; the existing DB connection is the only shared credential).
- A running copy of the existing system alongside AHC (the mirror is
  enough).

## Test plan for the integration

Once the existing system's spec is shared:

1. Add `src/ahc/integration/existing_products.py` implementing
   `ExistingProductFetcher` against the real schema.
2. Add `tests/test_integration.py` (marked `@pytest.mark.integration`)
   that runs against a fixture DB populated from a sample of the
   existing system's rows.
3. Update `ahc.cli` with a `sync-products` command that pulls recent
   updates from the existing system into AHC's mirror.
4. The existing collection system's cron job stays untouched.

## Backward compatibility

- AHC never writes to the existing DB.
- AHC's `products.external_source` defaults to `"existing"`, so any
  existing product row AHC ingests is traceable back to its origin.
- If the existing system's schema changes, only the
  `ExistingProductFetcher` mapping needs to update — the rest of AHC
  is insulated behind the interface.

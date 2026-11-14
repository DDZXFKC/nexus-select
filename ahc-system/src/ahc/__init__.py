"""AHC system package.

Modules:
  - ahc.config: settings
  - ahc.logging_setup: structured logging
  - ahc.db: SQLAlchemy models + repository
  - ahc.compliance: robots.txt / ToS policy gate
  - ahc.stores: store adapters (Shopify / Magento / WooCommerce / generic)
  - ahc.coupons: coupon collection, dedup, validation
  - ahc.cost: total cost + profit calculation
  - ahc.orders: order intake (IMAP) + BUYMA / AHC parsers
  - ahc.buying: Playwright cart preparation (no payment by default)
"""

__version__ = "0.1.0"

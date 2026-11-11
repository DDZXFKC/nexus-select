# Collector release status

Local package v3: 65 offline tests passed, with currency re-observation fix and read-only `readiness.py` gate audit. This GitHub branch currently contains the earlier standalone offline JSON-LD parser, **not the entire v3 integrated package**. The ZIP shared in ChatGPT is the full integrated artifact.

Production readiness: **NO-GO**. Merchant live fetching, size-specific inventory verification, shipping/tax/VAT/FX verification, Google Sheets, BUYMA sales, WooCommerce order sync and partner dispatch are not complete. No automated listings or purchases.

Do not assume this public repository has been granted Grok write access. Never commit supplier confidential pricing, partner details, order data or credentials.

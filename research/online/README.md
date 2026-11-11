# NEXUS SELECT online merchant collector — offline-first

Run: `python collector.py --html saved_product.html --url https://www.bstn.com/example --output candidates.csv`

Tests: `python -m unittest -v test_collector.py` (from this directory).

This module **does not fetch websites**. It parses manually supplied product-page HTML containing schema.org Product JSON-LD. It does not validate real BSTN/Foot Locker/Zalando DOMs, selectable sizes, shipping to Japan, VAT eligibility, live stock, or margins. All records are HOLD; no auto publishing or purchasing. Site names are candidate allowlist entries, not confirmed integrations. Only publish after explicit independent verification. No customer/partner/private data in this public repo.

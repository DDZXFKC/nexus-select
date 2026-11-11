# BSTN real evidence integration

The iMac evidence file is `results/imac-2026-11-12/candidates.csv`. It contains 13 sizes, a merchant SKU (0009238), and no confirmed manufacturer style code or color. It must NOT be passed to a product master as a verified manufacturer SKU.

Run from `research/online`:

```bash
python3 bstn_integration.py --csv results/imac-2026-11-12/candidates.csv --db bstn_evidence.db
```

This stages all rows, including missing color, in `merchant_evidence` with decision HOLD and UNVERIFIED state. Reimport resets prior verification. Do not commit .db files.

Remaining production gates: manufacturer style code and color verification; live size-selection inventory verification; Japan checkout shipping, VAT/taxes, FX and fees; Google Sheets and orders integration. No automatic listing or purchasing.

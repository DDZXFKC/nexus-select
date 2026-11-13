# Expansion bridge handoff
Use a separate copy of the package at c4192620 or later (201 tests passed at d231f4ba). Do not modify active collection. Python 3.9+.
1. Run existing regression suite and compile expansion/stage3_bridge.py.
2. Run offline with fresh output directory and DB:
```sh
python3 expansion/stage3_bridge.py --package "$PKG" --manifest "$PKG/input_pages_multi/manifest.csv" --manifest "$PKG/input_pages_multi/manifest_bstn2.csv" --db expansion-offline.sqlite --out expansion-offline
```
Use actual manifest paths if stored elsewhere. Expected BSTN 14, Notre 26, Patta 12; all complete, 52 rows, no import/publication. Inspect acceptance.json and per-host reports. If a manifest URL uses a noncanonical hostname, preserve evidence and report any extraction discrepancy; do not rewrite raw HTML.
3. Only after offline pass, prepare JSON config for BSTN only. Notre and Patta are offline-fixture-only under current policy; do not issue live requests. Before the offline acceptance run, verify the new live host guard rejects both hosts with zero network calls (mock stage3_catalog.Fetch and policy; assert neither is called). Use fresh output and DB paths; neither should be created for rejected hosts. Run the full 201-test regression suite plus these two guard cases. Recheck current terms and robots; no access if prohibited or uncertain. Existing stage3 policy requires enabled=true, permission_reference, reviewer, reviewed_at (UTC within 24h), interval_seconds>=5, request_budget<=10 for pilot, host, product_path_regex, sitemap_seeds (approved), pilot_product_urls (explicit approved URLs, initially one). Do not fabricate permission or timestamps. Use actual approved URLs from sourcing records. No Foot Locker or Zalando. No image copying/publication. Do not use media.bstn.com while robots access remains unverified. No bypass, no retries after fatal failure.
```sh
python3 expansion/stage3_bridge.py --package "$PKG" --config "$CFG" --db "$NEW_DB" --out "$NEW_OUT" --limit 1
```
Each pilot uses a fresh DB and output; do not repeat failed requests automatically. Stop affected host on policy/network/response error, continue independent approved hosts. No concurrent traffic to a host already being collected; defer that host until existing batch finishes. Report exact counts, exit codes, request counts, permission references, and HOLD status to docs/expansion-bridge-execution.md on integration/grok-review. No raw HTML, credentials or customer data in GitHub.
Acceptance: existing 201 tests pass, offline 52/52 and per-host counts match, each permitted pilot completes with valid evidence and zero publication/import. Live execution and actual fixture verification remain executor tasks; this is not approval to publish.

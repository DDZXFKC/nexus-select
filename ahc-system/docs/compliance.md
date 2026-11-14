# Compliance gate

The compliance gate is the **single source of truth** for "may we do X
to store/source Y?". Every store adapter and coupon source consults it
before any network operation. Chapter 9 (safety) and Chapter 4
(per-source terms) require this.

## File layout

- `src/ahc/compliance/policy.py` — `ComplianceGate`, `Verdict`
- `src/ahc/compliance/robots.py` — `fetch_robots_txt`, `RobotsRules`
- `src/ahc/compliance/tos.py` — `extract_tos_excerpt`, `TosPolicy`
- `config/compliance.yaml` — manual verdicts + defaults

## Decision order (first wins)

1. **Manual verdict** in `config/compliance.yaml` overrides everything
   (when not `unknown`).
2. **robots.txt** scan denies paths Disallowed for our UA.
3. **ToS excerpt** scan denies if the ToS explicitly prohibits bots.
4. If neither robots nor ToS can be fetched, fall back to
   `defaults.unreachable_action` (default: `manual`).
5. Buy automation is additionally gated by
   `defaults.allow_buy_automation` (default: `false`) AND the per-store
   `enabled_buy` flag in `stores.yaml`.

A verdict is a small immutable dataclass:

```python
@dataclass(frozen=True)
class Verdict:
    allowed: bool
    reason: str
    source: str = ""        # "manual" | "robots" | "tos" | "default" | "config"
    requires_human: bool = False
```

The gate never raises on a denial — it returns a denied verdict — so
callers branch cleanly instead of `try/except`.

## Verdict values

| Value | Meaning |
| --- | --- |
| `allowed` | Yes — proceed |
| `denied` | No — never proceed (e.g. Honey/Coupert have no public listing) |
| `manual` | Pending human review — block until reviewed |
| `unknown` | No verdict recorded yet — fall through to robots/ToS scan |

## Initial state

Every store and coupon source ships with `verdict: manual` (or `denied`
for Honey / Coupert, which are browser extensions with no public
listing). This is intentional: nothing scrapes or buys until a human
has read the ToS and explicitly approved.

## How to approve a store

Edit `config/compliance.yaml`:

```yaml
stores:
  bstn:
    scrape: allowed
    buy: allowed       # only effective if defaults.allow_buy_automation is also true
    note: "ToS reviewed 2026-11-14; allows bots for product pages; cart requires login"
```

Then re-run the gate. No code changes, no restart of the existing
collection system (the gate is read fresh from YAML on every
`ComplianceGate.from_config_file()` call).

## How to enable buy automation globally

```yaml
defaults:
  allow_buy_automation: true   # default false
```

This unlocks `allow_buy()` for stores whose verdict is `allowed`. It
does NOT bypass the per-store verdict, the dry-run guard, the approval
token, or the `submit_payment` implementation gap.

## robots.txt scan

`fetch_robots_txt(base_url)` returns a `RobotsRules` object whose
`can_fetch(url, ua)` answers path-level questions. On any fetch or
parse error, it returns an empty ruleset that **denies everything** —
when in doubt, deny.

Crawl-delay is read and stored; the HTTP session factory
(`ahc.stores.http.new_http_session`) honours a global
`AHC_REQUEST_RATE_LIMIT_RPS` default of 1.0 req/s.

## ToS excerpt scan

`extract_tos_excerpt(base_url)` fetches the homepage, follows the
first ToS-looking link in the footer, scans the text for explicit
phrases:

- **Negative** (sets `allowed=False`):
  "no automated access", "prohibited bots / robots / spiders /
  scrapers", "may not use any automated", "scraping prohibited",
  "no spider / crawler / scraper / bot".
- **Positive** (sets `allowed=True` if no negative matched):
  "allows automated access", "public API".

If neither matches, `allowed=None` (unknown) and the gate falls back
to the `unreachable_action` default. This is a **triage signal**, not
a legal determination — the manual verdict is the final word.

## Recording snapshots

`ComplianceGate.record_snapshot(store_id, snapshot)` writes a new row
to `compliance_records`. The schema is append-only so we keep a
history of every ToS / robots observation. The recorder is optional
(passed via the `recorder` constructor arg); the CLI does not yet
wire it — call it from your scheduler if you want history.

## Verifying from the CLI

```bash
# Effective verdict for a store
ahc compliance show --slug bstn --action scrape
ahc compliance show --slug bstn --action buy

# Live scan (fetches robots.txt + ToS)
ahc compliance scan --base-url https://www.bstn.com
```

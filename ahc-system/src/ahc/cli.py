"""AHC CLI.

Entry point: `ahc <command> [options]`. Install with `pip install -e .`
(see pyproject `[project.scripts]`), or run directly:
    PYTHONPATH=src python -m ahc.cli ...

Commands:
  init              Create / migrate the database schema.
  compliance show   Show the effective verdict for a store or source.
  compliance scan   Fetch robots.txt + ToS snapshot for a store.
  stores list       List configured stores.
  coupons collect   Run all enabled coupon sources.
  coupons list      List coupons for a store.
  orders fetch      Pull new order emails via IMAP and parse them.
  orders list       List pending orders.
  plan <order_id>   Build candidate purchase plans for an order.
  dry-run <plan_id> Prepare a cart for a plan (no payment).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import click
import yaml

from .config import settings
from .logging_setup import configure, get_logger

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_yaml(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _stores_config() -> dict:
    return _load_yaml(settings.stores_config)


def _sources_config() -> dict:
    return _load_yaml(settings.coupon_sources_config)


# ---------------------------------------------------------------------------
# Root group
# ---------------------------------------------------------------------------

@click.group(help="AHC coupon collection & auto-buying system.")
@click.option("--log-level", default=None, help="Override AHC_LOG_LEVEL.")
@click.option("--log-file", default=None, help="Override AHC_LOG_FILE.")
@click.version_option(message="ahc %(version)s")
def main(log_level: Optional[str], log_file: Optional[str]) -> None:
    configure(level=log_level, log_file=log_file)


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------

@main.command("init", help="Create / migrate the database schema.")
@click.option("--drop", is_flag=True, help="Drop existing tables first (destructive).")
def cmd_init(drop: bool) -> None:
    from .db import init_db
    init_db(drop=drop)
    click.echo(f"Database ready at {settings.db_url}")


# ---------------------------------------------------------------------------
# compliance
# ---------------------------------------------------------------------------

@main.group("compliance", help="Inspect / refresh compliance state.")
def grp_compliance() -> None:
    pass


@grp_compliance.command("show")
@click.option("--slug", required=True, help="Store or coupon-source slug.")
@click.option("--action", type=click.Choice(["scrape", "buy"]), default="scrape")
def cmd_compliance_show(slug: str, action: str) -> None:
    from .compliance import ComplianceGate
    gate = ComplianceGate.from_config_file()
    if action == "buy":
        v = gate.allow_buy(slug)
    else:
        v = gate.allow_scrape(slug)
    click.echo(json.dumps({
        "slug": slug, "action": action,
        "allowed": v.allowed, "reason": v.reason, "source": v.source,
        "requires_human": v.requires_human,
    }, indent=2))


@grp_compliance.command("scan")
@click.option("--base-url", required=True, help="Store base URL.")
def cmd_compliance_scan(base_url: str) -> None:
    from .compliance import fetch_robots_txt, extract_tos_excerpt
    from .stores.http import new_http_session
    sess = new_http_session()
    robots = fetch_robots_txt(base_url)
    tos = extract_tos_excerpt(base_url, http_session=sess)
    click.echo(json.dumps({
        "base_url": base_url,
        "robots": {
            "raw_len": len(robots.raw),
            "crawl_delay": robots.crawl_delay,
            "sample_path_allowed": robots.can_fetch("/", settings.user_agent),
        },
        "tos": {
            "url": tos.url,
            "allowed": tos.allowed,
            "matched_phrases": tos.matched_phrases,
            "excerpt": tos.excerpt[:300],
        },
    }, indent=2))


# ---------------------------------------------------------------------------
# stores
# ---------------------------------------------------------------------------

@main.group("stores", help="List / inspect configured stores.")
def grp_stores() -> None:
    pass


@grp_stores.command("list")
@click.option("--platform", help="Filter by ec_platform.")
@click.option("--country", help="Filter by country code.")
def cmd_stores_list(platform: Optional[str], country: Optional[str]) -> None:
    cfg = _stores_config()
    rows = cfg.get("stores", [])
    if platform:
        rows = [r for r in rows if r.get("ec_platform") == platform]
    if country:
        rows = [r for r in rows if r.get("country") == country.upper()]
    click.echo(f"{len(rows)} stores")
    for r in rows:
        click.echo(
            f"  {r['slug']:<18} {r['country']} {r['currency']} "
            f"{r['ec_platform']:<12} scrape={r.get('enabled_scrape')} "
            f"buy={r.get('enabled_buy')}"
        )


@grp_stores.command("seed")
@click.option("--dry-run", "dry_run_flag", is_flag=True, help="Print only; do not write.")
def cmd_stores_seed(dry_run_flag: bool) -> None:
    """Upsert all configured stores into the DB."""
    from .db import Store
    from .db.repository import Repository
    cfg = _stores_config()
    repo = Repository(Store)
    n = 0
    for r in cfg.get("stores", []):
        if dry_run_flag:
            click.echo(f"would upsert {r['slug']}")
            continue
        repo.upsert_by(
            {"slug": r["slug"]},
            {
                "name": r["name"],
                "country": r["country"],
                "currency": r["currency"],
                "base_url": r["base_url"],
                "ec_platform": r.get("ec_platform", "generic"),
                "enabled_scrape": bool(r.get("enabled_scrape", False)),
                "enabled_buy": bool(r.get("enabled_buy", False)),
            },
        )
        n += 1
    click.echo(f"seeded {n} stores")


# ---------------------------------------------------------------------------
# coupons
# ---------------------------------------------------------------------------

@main.group("coupons", help="Coupon collection.")
def grp_coupons() -> None:
    pass


@grp_coupons.command("collect")
@click.option("--source", help="Only run this source slug.")
def cmd_coupons_collect(source: Optional[str]) -> None:
    from .compliance import ComplianceGate
    from .coupons import CouponCollector
    from .coupons.base import AbstractCouponSource
    from .db import CouponSource, init_db
    from .db.repository import Repository
    from .stores.http import new_http_session
    import importlib

    init_db()
    cfg = _sources_config()
    gate = ComplianceGate.from_config_file()
    sess = new_http_session()

    sources = []
    for s in cfg.get("sources", []):
        if source and s["slug"] != source:
            continue
        if not s.get("enabled", False):
            log.info("skip disabled source %s", s["slug"])
            continue
        cls_path = s.get("adapter_class")
        if not cls_path:
            log.warning("skip source %s: no adapter_class", s["slug"])
            continue
        mod_path, _, cls_name = cls_path.rpartition(".")
        try:
            cls = getattr(importlib.import_module(mod_path), cls_name)
        except Exception as e:
            log.error("failed to import %s: %s", cls_path, e)
            continue
        sources.append(cls(s, http_session=sess, compliance=gate))

    if not sources:
        click.echo("no enabled sources with adapters; nothing to do")
        return

    collector = CouponCollector(sources)
    summary = collector.run()
    click.echo(json.dumps(summary, indent=2, default=str))


@grp_coupons.command("list")
@click.option("--store", help="Filter by store slug.")
@click.option("--status", help="Filter by status.")
def cmd_coupons_list(store: Optional[str], status: Optional[str]) -> None:
    from .db import Coupon, Store
    from .db.repository import Repository
    from .db.session import session_scope
    from sqlalchemy import select

    with session_scope() as s:
        stmt = select(Coupon)
        if status:
            stmt = stmt.where(Coupon.status == status)
        if store:
            stmt = stmt.join(Coupon.store).where(Store.slug == store)
        rows = s.execute(stmt).scalars().all()
    click.echo(f"{len(rows)} coupons")
    for c in rows[:50]:
        click.echo(
            f"  id={c.id} code={c.code!r:<25} type={c.discount_type} "
            f"value={c.discount_value} status={c.status} "
            f"until={c.valid_until}"
        )


# ---------------------------------------------------------------------------
# orders
# ---------------------------------------------------------------------------

@main.group("orders", help="Order intake + management.")
def grp_orders() -> None:
    pass


@grp_orders.command("fetch")
@click.option("--since-days", default=7, show_default=True)
@click.option("--limit", default=50, show_default=True)
def cmd_orders_fetch(since_days: int, limit: int) -> None:
    from .orders import ImapOrderFetcher, parse_email
    from .orders.manager import OrderManager

    fetcher = ImapOrderFetcher.from_settings()
    mgr = OrderManager()
    n_msgs = 0
    n_orders = 0
    try:
        for raw, path in fetcher.fetch_new(since_days=since_days, limit=limit):
            n_msgs += 1
            parsed = parse_email(raw)
            if parsed is None:
                log.info("no parser matched: %s", path)
                continue
            order = mgr.ingest(parsed)
            n_orders += 1
            log.info("ingested order %s (id=%s)", parsed.external_order_id, order.id)
    except Exception as e:
        log.error("orders fetch failed: %s", e)
    click.echo(json.dumps({"messages_fetched": n_msgs, "orders_ingested": n_orders}))


@grp_orders.command("list")
@click.option("--status", default=None, help="Filter by status.")
def cmd_orders_list(status: Optional[str]) -> None:
    from .db import Order
    from .db.session import session_scope
    from sqlalchemy import select

    with session_scope() as s:
        stmt = select(Order)
        if status:
            stmt = stmt.where(Order.status == status)
        rows = s.execute(stmt).scalars().all()
    click.echo(f"{len(rows)} orders")
    for o in rows[:50]:
        click.echo(
            f"  id={o.id} src={o.source} ext={o.external_order_id} "
            f"status={o.status} buyer={o.buyer_name!r}"
        )


# ---------------------------------------------------------------------------
# plan + dry-run
# ---------------------------------------------------------------------------

@main.command("plan", help="Build candidate purchase plans for an order.")
@click.argument("order_id", type=int)
@click.option("--apply", "apply_flag", is_flag=True,
              help="Also persist the selected plan (status=planned).")
def cmd_plan(order_id: int, apply_flag: bool) -> None:
    """For each order item, look up matching store_products and build plans.

    NOTE: full plan generation needs the existing collection DB to be wired
    in. This command currently lists order items and their candidate stores.
    """
    from .db import Order, OrderItem, StoreProduct, Store
    from .db.session import session_scope
    from sqlalchemy import select
    from sqlalchemy.orm import joinedload

    with session_scope() as s:
        order = s.get(Order, order_id)
        if order is None:
            click.echo(f"order {order_id} not found", err=True)
            sys.exit(1)
        items = s.execute(
            select(OrderItem).where(OrderItem.order_id == order_id)
        ).scalars().all()
        click.echo(f"order {order_id} ({order.source}/{order.external_order_id})")
        click.echo(f"  status={order.status}  items={len(items)}")
        for it in items:
            click.echo(
                f"  item id={it.id} brand={it.requested_brand} "
                f"model={it.requested_model} size={it.requested_size} qty={it.quantity}"
            )


@main.command("dry-run", help="Prepare a cart for a plan (no payment).")
@click.argument("plan_id", type=int)
def cmd_dry_run(plan_id: int) -> None:
    from .buying import build_orchestrator
    orch = build_orchestrator()
    result = orch.prepare_cart(plan_id)
    click.echo(json.dumps({
        "plan_id": result.plan_id,
        "store_slug": result.store_slug,
        "status": result.status.value if hasattr(result.status, "value") else str(result.status),
        "cart_total_minor": result.cart.total_minor if result.cart else None,
        "currency": result.currency,
        "screenshot_path": result.screenshot_path,
        "requires_approval": result.requires_approval,
        "error": result.error_message,
        "notes": result.notes,
    }, indent=2))


if __name__ == "__main__":
    main()

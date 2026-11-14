"""Shared pytest fixtures.

Tests never make real network calls or real purchases. We use SQLite in
memory, stubbed HTTP sessions, and the compliance gate is always loaded
from the bundled config.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
import yaml

# Make `src/` importable when running from the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Force test defaults BEFORE importing ahc.* (settings is a singleton).
os.environ.setdefault("AHC_DB_URL", "sqlite:///:memory:")
os.environ.setdefault("AHC_DRY_RUN_ONLY", "true")
os.environ.setdefault("AHC_LOG_LEVEL", "WARNING")
os.environ.setdefault("AHC_LOG_FILE", "/tmp/ahc-test.log")
os.environ.setdefault("AHC_MIN_PROFIT_JPY", "0")

from ahc.db import Base, init_db, SessionLocal  # noqa: E402
from ahc.db.session import engine  # noqa: E402
from ahc.utils.money import FxRate, FxTable  # noqa: E402


@pytest.fixture
def fx_table() -> FxTable:
    """Stable FX rates for tests. 1 EUR=160 JPY, 1 USD=150 JPY, 1 GBP=190 JPY."""
    return FxTable([
        FxRate("EUR", 160.0, "2026-11-14"),
        FxRate("USD", 150.0, "2026-11-14"),
        FxRate("GBP", 190.0, "2026-11-14"),
        FxRate("CAD", 110.0, "2026-11-14"),
    ])


@pytest.fixture(autouse=True)
def fresh_db():
    """Drop + recreate all tables before every test, in the shared in-memory engine."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def session():
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


@pytest.fixture
def compliance_gate():
    from ahc.compliance import ComplianceGate
    return ComplianceGate.from_config_file()


@pytest.fixture
def stores_config():
    with open(PROJECT_ROOT / "config" / "stores.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture
def sources_config():
    with open(PROJECT_ROOT / "config" / "coupon_sources.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture
def sample_raw_coupons():
    """Two RawCoupon instances for dedup tests."""
    from datetime import date
    from ahc.coupons.base import RawCoupon
    return [
        RawCoupon(
            store_slug="bstn",
            code="SUMMER10",
            title="10% off",
            discount_type="percent",
            discount_value=10.0,
            valid_until=date(2026, 12, 31),
            source_slug="retailmenot",
            source_url="https://example.com/r/1",
        ),
        # duplicate of #1 but newer seen_at
        RawCoupon(
            store_slug="bstn",
            code="summer10",  # case-different
            title="10% off sitewide",
            discount_type="percent",
            discount_value=10.0,
            valid_until=date(2026, 12, 31),
            source_slug="retailmenot",
            source_url="https://example.com/r/2",
        ),
        # distinct
        RawCoupon(
            store_slug="bstn",
            code="FREESHIP",
            discount_type="free_shipping",
            source_slug="mydealz",
            source_url="https://example.com/m/1",
        ),
    ]

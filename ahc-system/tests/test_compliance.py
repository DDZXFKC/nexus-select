"""Chapter 11 tests: compliance gate behaviour."""
from __future__ import annotations

from ahc.compliance import ComplianceGate


def test_unknown_store_denied_by_default(compliance_gate):
    v = compliance_gate.allow_scrape("nonexistent-store")
    # Default unreachable_action=manual -> denied + requires_human
    assert v.allowed is False
    assert v.requires_human is True


def test_manual_allowed_verdict_overrides(compliance_gate):
    # We temporarily monkey-patch the gate's store map.
    compliance_gate._stores["bstn"] = {"scrape": "allowed", "buy": "manual"}
    v = compliance_gate.allow_scrape("bstn")
    assert v.allowed is True
    assert v.source == "manual"


def test_manual_denied_verdict_overrides(compliance_gate):
    compliance_gate._stores["bstn"] = {"scrape": "denied", "buy": "manual"}
    v = compliance_gate.allow_scrape("bstn")
    assert v.allowed is False
    assert v.source == "manual"
    assert v.requires_human is False


def test_buy_automation_disabled_globally(compliance_gate):
    # allow_buy_automation defaults to False in config/compliance.yaml
    compliance_gate._stores["bstn"] = {"scrape": "allowed", "buy": "allowed"}
    v = compliance_gate.allow_buy("bstn")
    assert v.allowed is False
    assert "global default" in v.reason


def test_coupon_source_manual_verdict(compliance_gate):
    # mydealz has scrape=manual in compliance.yaml
    v = compliance_gate.allow_scrape("mydealz")
    assert v.allowed is False
    assert v.requires_human is True


def test_extension_sources_denied(compliance_gate):
    # honey and coupert are scrape=denied in compliance.yaml
    for slug in ("honey", "coupert"):
        v = compliance_gate.allow_scrape(slug)
        assert v.allowed is False
        assert v.source == "manual"

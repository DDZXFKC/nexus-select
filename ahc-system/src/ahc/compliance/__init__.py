"""Compliance package: robots.txt + ToS gate.

Every store / coupon source goes through this gate before any network
operation. The gate is the single source of truth for "may we scrape
this store?", "may we automate buying?", etc.

Public API:
    from ahc.compliance import ComplianceGate, Verdict, ComplianceDecision
    gate = ComplianceGate.from_config(...)
    verdict = gate.allow_scrape("bstn")
    if not verdict.allowed: ...
"""
from .policy import ComplianceGate, Verdict, ComplianceDecision
from .robots import fetch_robots_txt, RobotsRules, is_path_allowed
from .tos import extract_tos_excerpt, TosPolicy

__all__ = [
    "ComplianceGate",
    "Verdict",
    "ComplianceDecision",
    "fetch_robots_txt",
    "RobotsRules",
    "is_path_allowed",
    "extract_tos_excerpt",
    "TosPolicy",
]

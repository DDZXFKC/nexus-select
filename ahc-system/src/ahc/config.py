"""Centralised settings loaded from environment / .env.

All other modules import `settings` from here. Keep it free of side effects
(no network, no DB) so it can be imported from anywhere, including tests.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # download/ahc-system


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AHC_",
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Database
    db_url: str = "sqlite:///./data/ahc.db"
    existing_db_url: str = ""  # read-only mirror of the existing collection DB

    # Email / order intake
    imap_host: str = ""
    imap_port: int = 993
    imap_user: str = ""
    imap_password: str = ""
    imap_ssl: bool = True
    order_senders: str = "buyma.com,afterhoursclub"

    # Playwright / buying guardrails
    playwright_headless: bool = True
    max_cart_amount: float = 300_000.0  # in store currency
    min_profit_jpy: float = 0.0
    dry_run_only: bool = True  # CHAPTER 9: real purchase disabled by default

    # Network politeness
    request_timeout: int = 20
    request_rate_limit_rps: float = 1.0
    user_agent: str = (
        "Mozilla/5.0 (compatible; AHC-compliance-bot/0.1; +contact: ops)"
    )

    # Logging
    log_level: str = "INFO"
    log_file: str = str(PROJECT_ROOT / "data" / "ahc.log")

    # Config files
    stores_config: str = str(PROJECT_ROOT / "config" / "stores.yaml")
    coupon_sources_config: str = str(
        PROJECT_ROOT / "config" / "coupon_sources.yaml"
    )
    compliance_config: str = str(PROJECT_ROOT / "config" / "compliance.yaml")

    @field_validator("order_senders")
    @classmethod
    def _normalise_senders(cls, v: str) -> str:
        return ",".join(s.strip().lower() for s in v.split(",") if s.strip())

    @property
    def order_sender_list(self) -> List[str]:
        return self.order_senders.split(",")

    @property
    def data_dir(self) -> Path:
        p = PROJECT_ROOT / "data"
        p.mkdir(parents=True, exist_ok=True)
        return p


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


# Module-level singleton, import-friendly.
settings = get_settings()

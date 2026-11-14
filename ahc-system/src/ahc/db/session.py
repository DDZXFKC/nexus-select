"""Engine, session factory, and schema bootstrap.

Supports SQLite (default), PostgreSQL, MySQL, and Supabase (via postgres URL)
without code changes - just set AHC_DB_URL.
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from ..config import settings
from ..logging_setup import get_logger
from .base import Base
from . import models  # noqa: F401  - register tables on Base.metadata

log = get_logger(__name__)


def _build_engine(url: str) -> Engine:
    connect_args: dict = {}
    if url.startswith("sqlite"):
        # Make sure the file directory exists for sqlite.
        if ":///" in url:
            path_part = url.split(":///", 1)[1]
            # Strip query string if any
            path_part = path_part.split("?", 1)[0]
            Path(path_part).parent.mkdir(parents=True, exist_ok=True)
        connect_args["check_same_thread"] = False
    return create_engine(
        url,
        future=True,
        connect_args=connect_args,
        pool_pre_ping=True,
    )


engine: Engine = _build_engine(settings.db_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _record):  # pragma: no cover - thin shim
    try:
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute("PRAGMA foreign_keys=ON;")
        cur.close()
    except Exception:
        # Not a sqlite connection - ignore.
        pass


def init_db(drop: bool = False) -> None:
    """Create all tables. If drop=True, drop first (used in tests)."""
    if drop:
        log.warning("Dropping all tables (init_db drop=True)")
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    log.info("Database initialised at %s", settings.db_url)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Transactional scope around a series of operations."""
    s = SessionLocal()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()

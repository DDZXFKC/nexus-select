"""Structured logging for AHC.

One logger per module; a single handler at the root. Call `configure()`
exactly once at process start (CLI does this). Tests call `configure()`
with a tmp log file.
"""
from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path

from .config import settings

_CONFIGURED = False


def configure(level: str | None = None, log_file: str | None = None) -> None:
    """Idempotent root-logger configuration.

    - Console: INFO and above, concise format.
    - File:    DEBUG and above, rotating, detailed format.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    lvl = (level or settings.log_level).upper()
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)  # handlers filter; root keeps everything

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(lvl)
    console.setFormatter(fmt)
    root.addHandler(console)

    path = Path(log_file or settings.log_file)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            path, maxBytes=5_000_000, backupCount=5, encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(fmt)
        root.addHandler(file_handler)
    except OSError:
        # Read-only filesystem (e.g. tests in tmp): skip file handler.
        pass

    # Tame noisy libraries.
    for noisy in ("urllib3", "playwright", "asyncio", "charset_normalizer"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    if not _CONFIGURED:
        configure()
    return logging.getLogger(name)

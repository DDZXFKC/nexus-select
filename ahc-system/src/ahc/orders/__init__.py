"""Order intake package.

Public API:
    ImapOrderFetcher   - pull new order emails over IMAP
    OrderParser        - abstract parser contract
    ParsedOrder        - parsed order dataclass
    parse_email        - dispatch a raw email to the first matching parser
    register_parser    - decorator that adds a parser to the registry
    parsers            - {source_slug: OrderParser instance} registry

Importing this package also imports ``parsers.buyma`` and
``parsers.afterhours`` so their ``@register_parser`` decorators fire and the
``parsers`` dict is populated.
"""
from __future__ import annotations

from typing import Optional

from .base import OrderParser, register_parser
from .imap_client import ImapOrderFetcher
from .models import ParsedOrder, ParsedOrderItem

# Importing the parser modules triggers their @register_parser side effect,
# populating the registry dict in `ahc.orders.base`. NOTE: importing the
# `parsers` subpackage sets the `parsers` attribute on *this* package to the
# subpackage module, shadowing the registry dict - so we re-bind the dict
# from base afterwards (the last write to the package namespace wins).
from .parsers import afterhours as _afterhours  # noqa: F401
from .parsers import buyma as _buyma  # noqa: F401

from .base import parsers  # noqa: E402,F811  - registry dict; re-bound last


def parse_email(raw_bytes: bytes) -> Optional[ParsedOrder]:
    """Dispatch ``raw_bytes`` across registered parsers.

    Walks ``parsers`` in insertion order and returns the first non-None
    ``ParsedOrder``. Each parser is wrapped in a try/except so a bug in one
    parser never blocks another. Returns ``None`` if no parser claims the
    email (caller should skip / log it).
    """
    for parser in parsers.values():
        try:
            result = parser.parse(raw_bytes)
        except Exception:
            # Defensive: a parser bug must not break the dispatch loop.
            result = None
        if result is not None:
            return result
    return None


__all__ = [
    "ImapOrderFetcher",
    "OrderParser",
    "ParsedOrder",
    "ParsedOrderItem",
    "parse_email",
    "register_parser",
    "parsers",
]

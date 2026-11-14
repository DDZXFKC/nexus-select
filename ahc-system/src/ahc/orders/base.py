"""Abstract parser contract + registry.

Each platform (BUYMA, After Hours Club, ...) ships its own
``OrderParser`` subclass in ``ahc.orders.parsers``. The subclass decorates
itself with ``@register_parser``, which drops an *instance* into the
``parsers`` dict keyed by the class's ``source`` slug. ``parse_email`` then
walks that dict in insertion order and returns the first parser that
claims the email.

Keeping the registry instance-based (not class-based) means a parser can
hold lightweight compiled-regex state on the instance without recompiling
per call.
"""
from __future__ import annotations

import abc
from typing import Dict, Optional, Type

from .models import ParsedOrder


parsers: Dict[str, "OrderParser"] = {}


class OrderParser(abc.ABC):
    """Contract for a platform-specific email -> ParsedOrder converter.

    Implementations MUST be defensive: a regex miss yields ``None`` for the
    affected field, and ``parse`` returns ``None`` (rather than raising)
    when the email does not look like one of this parser's orders, so the
    caller can fall through to the next parser.
    """

    #: Platform slug; must match ``OrderSource`` enum values.
    source: str = ""

    @abc.abstractmethod
    def parse(self, raw_bytes: bytes) -> Optional[ParsedOrder]:
        """Return a ``ParsedOrder`` if this email belongs to this parser's
        platform, otherwise ``None``."""
        raise NotImplementedError


def register_parser(cls: Type[OrderParser]) -> Type[OrderParser]:
    """Class decorator: register an instance of ``cls`` under ``cls.source``.

    Returns ``cls`` unchanged so the decorated name still refers to the
    class (callers want the class for typing / subclassing, the registry
    holds a ready-to-use instance).
    """
    if not cls.source:
        raise ValueError(f"{cls.__name__}: empty `source` slug; cannot register")
    instance = cls()
    parsers[cls.source] = instance
    return cls

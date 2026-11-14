"""BUYMA order-confirmation email parser.

BUYMA (a Japanese luxury-resale marketplace) sends bilingual order emails
whose exact template has shifted over time. Every regex below is therefore
*best-effort*: a miss yields ``None`` for that field rather than raising,
and ``parse`` returns ``None`` entirely if no BUYMA order id is found so the
caller can fall through to the next parser.

Body extraction prefers the ``mail-parser`` package (a declared dependency)
when it is importable, and falls back to stdlib ``email`` otherwise so this
module remains usable even if the optional dep is absent at runtime.
"""
from __future__ import annotations

import re
from datetime import datetime
from email.header import decode_header, make_header
from typing import List, Optional, Tuple

from ..base import OrderParser, register_parser
from ..models import ParsedOrder, ParsedOrderItem

try:  # mail-parser is a declared dependency but may be absent in stripped envs.
    import mailparser  # type: ignore
    _HAS_MAILPARSER = True
except ImportError:  # pragma: no cover
    mailparser = None
    _HAS_MAILPARSER = False


# ---------------------------------------------------------------------------
# Field patterns (English label | Japanese label). Order matters: the first
# pattern that matches wins. Labels accept both ASCII ':' and full-width '：'.
# ---------------------------------------------------------------------------
_ORDER_ID_PATTERNS: Tuple[re.Pattern, ...] = (
    re.compile(r"Order\s*ID\s*[:：]\s*([A-Za-z0-9_\-]+)", re.IGNORECASE),
    re.compile(r"注文番号\s*[:：]\s*([A-Za-z0-9_\-]+)"),
)
_BUYER_NAME_PATTERNS: Tuple[re.Pattern, ...] = (
    re.compile(r"Buyer(?:\s*Name)?\s*[:：]\s*([^\r\n]+)", re.IGNORECASE),
    re.compile(r"お名前\s*[:：]\s*([^\r\n]+)"),
)
_BUYER_EMAIL_PATTERNS: Tuple[re.Pattern, ...] = (
    re.compile(r"Buyer\s*Email\s*[:：]\s*([^\r\n]+)", re.IGNORECASE),
    re.compile(r"メール(?:アドレス)?\s*[:：]\s*([^\r\n]+)"),
    re.compile(r"([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})"),
)
_SHIP_COUNTRY_PATTERNS: Tuple[re.Pattern, ...] = (
    re.compile(r"Ship(?:ping)?\s*Country\s*[:：]\s*([A-Za-z]{2})", re.IGNORECASE),
    re.compile(r"配送先国\s*[:：]\s*([A-Za-z]{2})"),
)
_SHIP_ADDRESS_PATTERNS: Tuple[re.Pattern, ...] = (
    re.compile(r"Ship(?:ping)?\s*Address\s*[:：]\s*([^\r\n]+)", re.IGNORECASE),
    re.compile(r"配送先住所\s*[:：]\s*([^\r\n]+)"),
)
# Total: "<CUR> <amount>" e.g. "JPY 49,800" or "EUR 1,234.50".
_SALE_PRICE_PATTERNS: Tuple[re.Pattern, ...] = (
    re.compile(r"Total\s*[:：]\s*([A-Z]{3})\s*([\d,]+(?:\.\d+)?)", re.IGNORECASE),
    re.compile(r"合計\s*[:：]\s*([A-Z]{3})\s*([\d,]+(?:\.\d+)?)"),
)
_PLACED_AT_PATTERNS: Tuple[re.Pattern, ...] = (
    re.compile(r"Order\s*Date\s*[:：]\s*(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2})", re.IGNORECASE),
    re.compile(r"注文日時\s*[:：]\s*(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2})"),
)

# Item-level labels. Each may appear multiple times in a multi-item email.
_ITEM_BRAND = re.compile(
    r"Brand\s*[:：]\s*([^\r\n]+)|ブランド\s*[:：]\s*([^\r\n]+)", re.IGNORECASE
)
_ITEM_MODEL = re.compile(
    r"Model\s*[:：]\s*([^\r\n]+)|モデル\s*[:：]\s*([^\r\n]+)", re.IGNORECASE
)
_ITEM_COLORWAY = re.compile(
    r"Color(?:way)?\s*[:：]\s*([^\r\n]+)|カラー\s*[:：]\s*([^\r\n]+)", re.IGNORECASE
)
_ITEM_SIZE = re.compile(
    r"Size\s*[:：]\s*([^\r\n]+)|サイズ\s*[:：]\s*([^\r\n]+)", re.IGNORECASE
)
_ITEM_QTY = re.compile(
    r"Qty\s*[:：]\s*(\d+)|数量\s*[:：]\s*(\d+)", re.IGNORECASE
)
# Per-item price: "Price: <CUR> <amount>".
_ITEM_PRICE = re.compile(
    r"Price\s*[:：]\s*([A-Z]{3})\s*([\d,]+(?:\.\d+)?)"
    r"|価格\s*[:：]\s*([A-Z]{3})\s*([\d,]+(?:\.\d+)?)",
    re.IGNORECASE,
)

# Currencies whose minor unit is 1 (no fractional cents).
_ZERO_DECIMAL_CURRENCIES = frozenset({"JPY", "KRW", "VND", "CLP", "ISK"})


def _first_match(patterns: Tuple[re.Pattern, ...], text: str) -> Optional[str]:
    for p in patterns:
        m = p.search(text)
        if m:
            return m.group(1).strip()
    return None


def _decode_header_value(raw: Optional[str]) -> str:
    if not raw:
        return ""
    try:
        return str(make_header(decode_header(raw)))
    except Exception:
        return str(raw)


def _money_to_minor(currency: Optional[str], amount_str: Optional[str]) -> Optional[int]:
    """Convert a decimal amount string into minor units (int)."""
    if not currency or not amount_str:
        return None
    try:
        cleaned = amount_str.replace(",", "").strip()
        value = float(cleaned)
    except (ValueError, TypeError):
        return None
    if currency.upper() in _ZERO_DECIMAL_CURRENCIES:
        return int(round(value))
    return int(round(value * 100))


def _flatten_groups(matches) -> List[Optional[str]]:
    """Turn findall tuple-captures into a flat list of non-empty strings."""
    out: List[Optional[str]] = []
    for m in matches:
        if isinstance(m, tuple):
            out.append(next((g for g in m if g), None))
        else:
            out.append(m if m else None)
    return out


def _extract_body(raw_bytes: bytes) -> Tuple[str, str]:
    """Return ``(combined_text, from_header)`` from raw email bytes.

    Combined text joins the plain-text and HTML parts so regexes can run
    against one blob. HTML tags are left in place; the patterns above match
    plain labels that survive in the HTML source too.
    """
    plain = ""
    html = ""
    from_value = ""

    if _HAS_MAILPARSER:
        try:
            mp = mailparser.parse_from_bytes(raw_bytes)
            from_value = mp.from_ or ""
            body = mp.body
            if isinstance(body, str):
                plain = body
            html_text = getattr(mp, "text_html", None)
            if isinstance(html_text, list):
                html = "\n".join(html_text)
            elif isinstance(html_text, str):
                html = html_text
        except Exception:
            # Fall through to stdlib parsing below.
            pass

    # Stdlib parse: always run as a supplement / fallback so a missing or
    # buggy mail-parser never leaves us without a body.
    import email as _email

    msg = _email.message_from_bytes(raw_bytes)
    if not from_value:
        from_value = _decode_header_value(msg.get("From", ""))
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/plain" and not plain:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    plain = payload.decode(charset, errors="replace")
            elif ctype == "text/html" and not html:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    html = payload.decode(charset, errors="replace")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            plain = payload.decode(charset, errors="replace")

    combined = (plain or "") + "\n" + (html or "")
    return combined, from_value


@register_parser
class BuymaParser(OrderParser):
    source = "buyma"

    def parse(self, raw_bytes: bytes) -> Optional[ParsedOrder]:
        try:
            text, _from_value = _extract_body(raw_bytes)
        except Exception:
            # Body extraction itself must never crash the dispatch loop;
            # `parse_email` already wraps us, but be doubly safe.
            return None
        if not text:
            return None

        order_id = _first_match(_ORDER_ID_PATTERNS, text)
        if not order_id:
            # Not a BUYMA order confirmation - let the next parser try.
            return None

        buyer_name = _first_match(_BUYER_NAME_PATTERNS, text)
        buyer_email = _first_match(_BUYER_EMAIL_PATTERNS, text)
        ship_country = _first_match(_SHIP_COUNTRY_PATTERNS, text)
        ship_address = _first_match(_SHIP_ADDRESS_PATTERNS, text)

        sale_currency: Optional[str] = None
        sale_minor: Optional[int] = None
        for p in _SALE_PRICE_PATTERNS:
            m = p.search(text)
            if m:
                sale_currency = (m.group(1) or "").upper() or None
                sale_minor = _money_to_minor(sale_currency, m.group(2))
                break

        placed_at: Optional[datetime] = None
        for p in _PLACED_AT_PATTERNS:
            m = p.search(text)
            if m:
                try:
                    placed_at = datetime.fromisoformat(
                        m.group(1).replace(" ", "T")
                    )
                except ValueError:
                    placed_at = None
                break

        items = self._parse_items(text)

        return ParsedOrder(
            source=self.source,
            external_order_id=order_id,
            buyer_name=buyer_name,
            buyer_email=buyer_email,
            ship_country=ship_country,
            ship_address=ship_address,
            sale_price_minor=sale_minor,
            sale_currency=sale_currency,
            placed_at=placed_at,
            items=items,
            raw_email_path=None,
        )

    @staticmethod
    def _parse_items(text: str) -> List[ParsedOrderItem]:
        """Best-effort item extraction.

        Collects every brand / model / colorway / size / qty / price label
        in document order and zips them by index into items. If the email
        has no item labels at all, returns a single best-effort item with
        every field ``None`` (and quantity 1) so downstream code always has
        at least one ``OrderItem`` row to plan against.
        """
        brands = _flatten_groups(_ITEM_BRAND.findall(text))
        models = _flatten_groups(_ITEM_MODEL.findall(text))
        colorways = _flatten_groups(_ITEM_COLORWAY.findall(text))
        sizes = _flatten_groups(_ITEM_SIZE.findall(text))

        qty_matches = _ITEM_QTY.findall(text)
        qtys: List[int] = []
        for m in qty_matches:
            if isinstance(m, tuple):
                g = next((g for g in m if g), None)
                qtys.append(int(g) if g else 1)
            else:
                qtys.append(int(m) if m else 1)

        price_matches = _ITEM_PRICE.findall(text)
        prices: List[Tuple[Optional[str], Optional[str]]] = []
        for m in price_matches:
            if isinstance(m, tuple):
                # Two alternative groups: (cur1, amt1, cur2, amt2).
                cur = next((g for g in (m[0], m[2]) if g), None)
                amt = next((g for g in (m[1], m[3]) if g), None)
                prices.append((cur, amt))
            else:
                prices.append((None, m))

        max_len = max(
            len(brands), len(models), len(colorways), len(sizes), len(qtys), len(prices)
        )
        if max_len == 0:
            # No item labels found - one best-effort placeholder item.
            return [
                ParsedOrderItem(
                    requested_brand=None,
                    requested_model=None,
                    requested_colorway=None,
                    requested_size=None,
                    quantity=1,
                    sale_price_minor=None,
                    sale_currency=None,
                )
            ]

        items: List[ParsedOrderItem] = []
        for i in range(max_len):
            cur, amt = prices[i] if i < len(prices) else (None, None)
            currency = cur.upper() if cur else None
            items.append(
                ParsedOrderItem(
                    requested_brand=brands[i].strip() if i < len(brands) and brands[i] else None,
                    requested_model=models[i].strip() if i < len(models) and models[i] else None,
                    requested_colorway=colorways[i].strip() if i < len(colorways) and colorways[i] else None,
                    requested_size=sizes[i].strip() if i < len(sizes) and sizes[i] else None,
                    quantity=qtys[i] if i < len(qtys) else 1,
                    sale_price_minor=_money_to_minor(currency, amt),
                    sale_currency=currency,
                )
            )
        return items

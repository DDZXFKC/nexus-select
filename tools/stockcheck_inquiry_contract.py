"""Validate the inbound stock enquiry contract before calling StockChecker.

Size/color are supplied by WordPress's server-resolved selected variation,
NEVER scraped from the user's free-text message.
"""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class StockInquiry:
    receipt_id: str
    name: str
    email: str
    product_id: int
    variation_id: int
    size: str
    color: str
    message: str = ""


def parse_inquiry(payload):
    if not isinstance(payload, dict):
        raise ValueError("inquiry must be a dictionary")
    name = payload.get("name", "")
    email = payload.get("email", "")
    receipt_id = payload.get("receipt_id", "")
    message = payload.get("message") or ""
    if not isinstance(name, str) or not name.strip() or len(name) > 100:
        raise ValueError("name required (max 100 characters)")
    if not isinstance(email, str) or not re.fullmatch(
            r"[^\s@]+@[^\s@]+\.[^\s@]+", email.strip()):
        raise ValueError("valid email required")
    if not isinstance(receipt_id, str) or not receipt_id.strip():
        raise ValueError("receipt_id required")
    if not isinstance(message, str) or len(message) > 1000:
        raise ValueError("optional message exceeds 1000 characters")
    if type(payload.get("product_id")) is not int or payload["product_id"] <= 0:
        raise ValueError("product ID required")
    if type(payload.get("variation_id")) is not int or payload["variation_id"] <= 0:
        raise ValueError("server-resolved variation ID required")
    selected = payload.get("selected_variation")
    if not isinstance(selected, dict):
        raise ValueError("server-resolved selected variation required")
    size, color = selected.get("size"), selected.get("color", "")
    if not isinstance(size, str) or not size.strip():
        raise ValueError("selected size is required; do not infer from message")
    if not isinstance(color, str):
        raise ValueError("selected color must be text")
    if payload.get("size") is not None or payload.get("color") is not None:
        raise ValueError("do not accept redundant client or message size/color fields")
    return StockInquiry(receipt_id.strip(), name.strip(), email.strip(),
                        payload["product_id"], payload["variation_id"],
                        size.strip(), color.strip(), message)

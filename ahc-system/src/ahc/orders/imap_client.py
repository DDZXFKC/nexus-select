"""IMAP fetcher for order-confirmation emails.

Connects lazily (never at import time), pulls UNSEEN messages from the last
``since_days``, filters by sender, writes each raw RFC822 blob to
``mail_dir/<uid>.eml`` and marks it seen.

Chapter 10 (error containment): any IMAP-level failure is logged and the
run returns whatever was already fetched in this batch - a flaky mailbox
must never abort the whole intake. Per-message fetch errors are likewise
swallowed so one bad message does not poison the rest.
"""
from __future__ import annotations

import email as email_lib
import imaplib
from datetime import datetime, timedelta, timezone
from email.header import decode_header, make_header
from pathlib import Path
from typing import List, Optional, Tuple

from ..logging_setup import get_logger

log = get_logger(__name__)


class ImapOrderFetcher:
    """Fetch new order emails over IMAP and persist their raw bytes."""

    def __init__(
        self,
        *,
        host: str,
        port: int,
        user: str,
        password: str,
        ssl: bool,
        allowed_senders: List[str],
        mail_dir: str,
    ) -> None:
        # Store config only - no connection here (constraint: never connect
        # at construction / import time).
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.ssl = ssl
        self.allowed_senders = [s.lower() for s in (allowed_senders or []) if s]
        self.mail_dir = Path(mail_dir)
        self.mail_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_settings(cls) -> "ImapOrderFetcher":
        """Build a fetcher from the global `settings` singleton."""
        # Imported lazily so importing this module never triggers config load
        # side effects in environments without a .env.
        from ..config import settings

        mail_dir = Path(settings.data_dir) / "orders_mail"
        return cls(
            host=settings.imap_host,
            port=settings.imap_port,
            user=settings.imap_user,
            password=settings.imap_password,
            ssl=settings.imap_ssl,
            allowed_senders=settings.order_sender_list,
            mail_dir=str(mail_dir),
        )

    # ------------------------------------------------------------------
    # connection
    # ------------------------------------------------------------------
    def _connect(self):
        """Open + login + select INBOX. Raises on IMAP-level failure."""
        if self.ssl:
            conn = imaplib.IMAP4_SSL(self.host, self.port)
        else:
            conn = imaplib.IMAP4(self.host, self.port)
        if self.user:
            conn.login(self.user, self.password)
        # Read-write so \\Seen flags stick.
        conn.select("INBOX")
        return conn

    @staticmethod
    def _decode_header_value(raw: Optional[str]) -> str:
        if not raw:
            return ""
        try:
            return str(make_header(decode_header(raw)))
        except Exception:
            return str(raw)

    def _matches_allowed(self, from_value: str) -> bool:
        """True if any allowed-sender substring appears in the From header."""
        if not self.allowed_senders:
            # No filter configured -> accept everything.
            return True
        lowered = from_value.lower()
        return any(s in lowered for s in self.allowed_senders)

    # ------------------------------------------------------------------
    # fetch
    # ------------------------------------------------------------------
    def fetch_new(
        self, *, since_days: int = 7, limit: int = 50
    ) -> List[Tuple[bytes, str]]:
        """Return up to ``limit`` ``(raw_bytes, saved_path)`` tuples.

        Each tuple is a fresh UNSEEN message from the last ``since_days``
        whose From header matches an allowed sender, persisted to
        ``mail_dir/<uid>.eml`` and marked \\Seen.
        """
        results: List[Tuple[bytes, str]] = []
        conn = None
        try:
            conn = self._connect()
            since_date = (
                datetime.now(timezone.utc) - timedelta(days=since_days)
            ).strftime("%d-%b-%Y")
            typ, data = conn.search(None, "UNSEEN", "SINCE", since_date)
            if typ != "OK":
                log.warning("IMAP SEARCH returned %s; no messages to fetch", typ)
                return results

            uids: List[bytes] = []
            for blob in data or []:
                if isinstance(blob, (bytes, bytearray)) and blob.strip():
                    uids.extend(b for b in blob.split() if b)
            log.info(
                "IMAP SEARCH returned %d unseen UID(s) since %s", len(uids), since_date
            )

            for uid in uids[:limit]:
                try:
                    fetched = self._fetch_one(conn, uid)
                except Exception as exc:  # Chapter 10: per-message isolation
                    log.warning("IMAP fetch failed for uid=%s: %s", uid, exc)
                    continue
                if fetched is not None:
                    results.append(fetched)
        except Exception as exc:
            # Chapter 10: never raise from a flaky mailbox - return partial.
            log.error(
                "IMAP fetch_new aborted after %d message(s): %s", len(results), exc
            )
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
                try:
                    conn.logout()
                except Exception:
                    pass
        return results

    def _fetch_one(
        self, conn, uid: bytes
    ) -> Optional[Tuple[bytes, str]]:
        """Fetch one UID, filter by sender, save bytes, mark seen.

        Returns ``(raw_bytes, saved_path)`` or ``None`` if the message is
        not from an allowed sender (or has no RFC822 body).
        """
        typ, data = conn.fetch(uid, "(RFC822)")
        if typ != "OK" or not data:
            return None

        raw_bytes = b""
        for item in data:
            if isinstance(item, tuple) and len(item) >= 2 and isinstance(
                item[1], (bytes, bytearray)
            ):
                raw_bytes = bytes(item[1])
                break
        if not raw_bytes:
            return None

        msg = email_lib.message_from_bytes(raw_bytes)
        from_value = self._decode_header_value(msg.get("From", ""))
        if not self._matches_allowed(from_value):
            log.debug(
                "Skipping uid=%s: From=%r not in allowed senders %r",
                uid,
                from_value,
                self.allowed_senders,
            )
            return None

        safe_uid = uid.decode("ascii", errors="replace") if isinstance(
            uid, (bytes, bytearray)
        ) else str(uid)
        path = self.mail_dir / f"{safe_uid}.eml"
        path.write_bytes(raw_bytes)

        # Fetching RFC822 already sets \\Seen in most servers; store again
        # to be explicit and idempotent across implementations.
        try:
            conn.store(uid, "+FLAGS", "\\Seen")
        except Exception as exc:
            log.warning("IMAP STORE \\Seen failed uid=%s: %s", uid, exc)

        return raw_bytes, str(path)

"""Read-only Shoe Palace live Shopify SKU evidence probe.

Not stock authorization. Stops on robots/HTTP restriction; never guesses
variant IDs, sizes, prices, or product identities. No bypass or retries.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

ROOT = Path(__file__).resolve().parents[1]
URLS = ROOT / "data/xserver-export/sp158-source-urls-from-sheet-2026-11-21.csv"
WOO = ROOT / "data/xserver-export/sp-variation-skus-2026-11-21.csv"
USER_AGENT = "AfterHoursClubSKUVerification/1.0 (single-product identity verification; no inventory assertions)"
FIELDS = ["product_id", "parent_sku", "variation_id", "variation_sku",
          "supplier_product_id", "supplier_variant_id", "supplier_variant_sku",
          "source_url", "observed_at_utc", "status", "reason", "source_sha256"]


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def valid_url(value):
    p = urlsplit(value)
    return (p.scheme == "https" and p.netloc == "www.shoepalace.com"
            and re.fullmatch(r"/products/[A-Za-z0-9_-]+/?", p.path) is not None
            and not p.query and not p.fragment and not p.username and not p.password
            and p.port is None)


def fetch(url):
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=12) as response:
        if response.status != 200:
            raise ValueError("HTTP_" + str(response.status))
        payload = response.read(1_000_001)
        if len(payload) > 1_000_000:
            raise ValueError("BODY_TOO_LARGE")
        return payload


def robots_allows(robots_body, product_url):
    robot = RobotFileParser()
    robot.parse(robots_body.decode("utf-8", errors="replace").splitlines())
    return robot.can_fetch(USER_AGENT, product_url)


def probe(product_id, source_url, rows, *, getter=fetch, robots_body=None):
    supplier_id = rows[0]["parent_sku"][3:]
    output = []
    def hold(reason):
        return [dict(product_id=product_id, parent_sku=r["parent_sku"],
                     variation_id=r["variation_id"], variation_sku=r["variation_sku"],
                     supplier_product_id=supplier_id, supplier_variant_id="",
                     supplier_variant_sku="", source_url=source_url,
                     observed_at_utc="", status="HOLD", reason=reason, source_sha256="")
                for r in rows]
    if not valid_url(source_url):
        return hold("INVALID_SOURCE_URL")
    if robots_body is None or not robots_allows(robots_body, source_url + ".js"):
        return hold("ROBOTS_NOT_VERIFIED")
    try:
        body = getter(source_url.rstrip("/") + ".js")
        data = json.loads(body)
        if not isinstance(data, dict) or str(data.get("id", "")) != supplier_id:
            return hold("SUPPLIER_PRODUCT_ID_MISMATCH")
        if not isinstance(data.get("variants"), list):
            return hold("VARIANT_LIST_MISSING")
        variants = data["variants"]
        skus = {}
        for v in variants:
            if not isinstance(v, dict):
                continue
            sku = v.get("sku")
            sid = v.get("id")
            if not isinstance(sku, str) or not sku or not isinstance(sid, int) or sid <= 0:
                continue
            skus.setdefault(sku, []).append(v)
        timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        evidence_hash = hashlib.sha256(body).hexdigest()
        for r in rows:
            match = skus.get(r["variation_sku"], [])
            good = len(match) == 1
            v = match[0] if good else {}
            output.append(dict(
                product_id=product_id, parent_sku=r["parent_sku"],
                variation_id=r["variation_id"], variation_sku=r["variation_sku"],
                supplier_product_id=supplier_id,
                supplier_variant_id=str(v["id"]) if good else "",
                supplier_variant_sku=v["sku"] if good else "",
                source_url=source_url, observed_at_utc=timestamp,
                status="PASS" if good else "HOLD",
                reason="EXACT_INDEPENDENT_SHOPIFY_VARIANT_SKU" if good else
                       ("SUPPLIER_SKU_AMBIGUOUS" if match else "SUPPLIER_SKU_MISSING"),
                source_sha256=evidence_hash
            ))
        return output
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as err:
        if isinstance(err, HTTPError):
            reason = "HTTP_" + str(err.code)
        elif isinstance(err, (URLError, TimeoutError, OSError)):
            reason = "SUPPLIER_UNREACHABLE"
        else:
            reason = "SUPPLIER_RESPONSE_INVALID"
        return hold(reason)


def run(max_products, output_path, *, getter=fetch, robots_getter=fetch):
    if not (1 <= max_products <= 158):
        raise ValueError("max_products outside allowed range")
    source_rows = read_csv(URLS)
    woo_rows = read_csv(WOO)
    url_map = {}
    for record in source_rows:
        sid = record["supplier_product_id"]
        url = record["source_url"]
        if not sid.isdecimal() or not valid_url(url) or sid in url_map:
            raise ValueError("Invalid or duplicate approved URL mapping")
        url_map[sid] = url
    groups = {}
    for record in woo_rows:
        sku = record["parent_sku"]
        if not re.fullmatch(r"SP-[0-9]+", sku):
            raise ValueError("Malformed parent SKU")
        if not record["variation_id"].isdigit() or not record["variation_sku"]:
            raise ValueError("Missing Woo IDs or SKU")
        groups.setdefault((record["product_id"], sku), []).append(record)
    if len(groups) != 158:
        raise ValueError(f"Expected 158 Woo parents, got {len(groups)}")
    if len(woo_rows) != 1713:
        raise ValueError(f"Expected 1713 Woo variations, got {len(woo_rows)}")

    # Read robots once. Any error halts all live supplier requests.
    try:
        robots_body = robots_getter("https://www.shoepalace.com/robots.txt")
    except (HTTPError, URLError, TimeoutError, OSError, ValueError):
        robots_body = None
    selected = list(groups.items())[:max_products]
    results = []
    for index, ((product_id, parent_sku), variants) in enumerate(selected):
        url = url_map.get(parent_sku[3:])
        if not url:
            raise ValueError("Missing approved URL: " + parent_sku)
        results.extend(probe(product_id, url, variants, getter=getter, robots_body=robots_body))
        # Maximum one request per product, no retry, with a polite gap.
        if index + 1 < len(selected):
            time.sleep(5)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(results)
    print("Products", len(selected), "Variations", len(results),
          "PASS", sum(r["status"] == "PASS" for r in results),
          "HOLD", sum(r["status"] == "HOLD" for r in results))
    print("Reasons", sorted(set(r["reason"] for r in results)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-products", type=int, default=1)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run(args.max_products, args.output)

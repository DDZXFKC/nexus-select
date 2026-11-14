"""Quarantine GLM CSV/JSON claims; use the existing offline sourcing gate.
No network, production database, WooCommerce or publishing code.
The older pilot_report_import.py remains the DOCX-only importer.
"""
import argparse
import csv
import hashlib
import io
import json
import re
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from sourcing_gate import run

FIELDS = set('id brand model sku colorway category buy_source buy_url buy_price buy_currency buy_price_jpy fx_rate fx_date overseas_stock domestic_status selection_reason signal_type verification_status references sources confirmed_at'.split())
NUMBERS = {'buy_price', 'buy_price_jpy', 'fx_rate'}
REF_FIELDS = set('site product_name price_jpy size url status seller observed_at'.split())
CLAIM_STATUS = 'UNVERIFIED_GLM_CLAIM'
FILES = ('candidates.csv', 'candidates.json', 'discover_test.json')


def unique_object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError('duplicate JSON key: ' + key)
        out[key] = value
    return out


def reject_constant(value):
    raise ValueError('invalid JSON number: ' + value)


def load_json(text):
    return json.loads(text, object_pairs_hook=unique_object, parse_constant=reject_constant)


def decimal_value(value):
    if isinstance(value, bool):
        raise ValueError('boolean is not a number')
    try:
        v = Decimal(str(value))
        if not v.is_finite() or v < 0:
            raise ValueError('invalid numeric claim')
        return v
    except (InvalidOperation, TypeError) as exc:
        raise ValueError('invalid numeric claim') from exc


def validate(rows):
    if not isinstance(rows, list) or not rows:
        raise ValueError('candidate array required')
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != FIELDS:
            raise ValueError('unexpected candidate schema')
        if any(not isinstance(row[k], str) for k in FIELDS - NUMBERS - {'references', 'sources'}):
            raise ValueError('invalid candidate text field')
        key = row['id']
        if not re.fullmatch(r'AHC-\d+', key) or key in seen:
            raise ValueError('invalid or duplicate candidate ID')
        seen.add(key)
        if not row['brand'].strip() or not row['model'].strip():
            raise ValueError('missing candidate name or brand')
        for key in NUMBERS:
            if row[key] is not None:
                if not isinstance(row[key], (int, float)):
                    raise ValueError('unexpected numeric type')
                decimal_value(row[key])
        if not isinstance(row['sources'], list) or any(not isinstance(s, str) for s in row['sources']):
            raise ValueError('invalid sources')
        if not isinstance(row['references'], list):
            raise ValueError('invalid reference list')
        for ref in row['references']:
            if not isinstance(ref, dict) or set(ref) != REF_FIELDS:
                raise ValueError('unexpected reference schema')
            if any(not isinstance(ref[k], str) for k in REF_FIELDS - {'price_jpy'}):
                raise ValueError('invalid reference text field')
            if ref['price_jpy'] is not None:
                if not isinstance(ref['price_jpy'], (int, float)):
                    raise ValueError('unexpected reference price type')
                decimal_value(ref['price_jpy'])
    return rows


def compare_csv(text, rows):
    reader = csv.DictReader(io.StringIO(text, newline=''), strict=True)
    if not reader.fieldnames or len(reader.fieldnames) != len(FIELDS) or set(reader.fieldnames) != FIELDS:
        raise ValueError('unexpected CSV header')
    csv_rows = list(reader)
    if len(csv_rows) != len(rows):
        raise ValueError('CSV/JSON candidate count mismatch')
    for csv_row, row in zip(csv_rows, rows):
        if None in csv_row or any(v is None for v in csv_row.values()):
            raise ValueError('invalid CSV row width')
        for k in FIELDS:
            value = row[k]
            cell = csv_row[k]
            if k == 'references':
                equal = (json.dumps(load_json(cell), sort_keys=True, ensure_ascii=False)
                         == json.dumps(value, sort_keys=True, ensure_ascii=False))
            elif k == 'sources':
                equal = cell == ' | '.join(value)
            elif k in NUMBERS:
                equal = (cell == '') if value is None else decimal_value(cell) == decimal_value(value)
            else:
                equal = cell == value
            if not equal:
                raise ValueError('CSV/JSON mismatch: ' + row['id'] + ' / ' + k)
    return len(csv_rows)


def quarantine(rows, source, sha):
    return [
        {'candidate': {'candidate_id': row['id'], 'brand': row['brand'],
                       'name': row['model'], 'reported_style_code': row['sku']},
         'offers': [], 'references': [], 'cost_inputs': {},
         'report_claims': {'source_file': source, 'source_sha256': sha,
                           'status': CLAIM_STATUS,
                           'raw_candidate': {k: v for k, v in row.items() if k != 'references'},
                           'references': [{'reference_index': i, 'status': CLAIM_STATUS, 'raw_reference': ref}
                                          for i, ref in enumerate(row['references'], 1)]}}
        for row in rows
    ]


def decide(claims):
    results = run(claims, datetime.now(timezone.utc))
    if [r.get('candidate_id') for r in results] != [x['candidate']['candidate_id'] for x in claims]:
        raise ValueError('gate output candidate mismatch')
    for r in results:
        if ('error' in r or r.get('decision') != 'HOLD' or r.get('review_ready') is not False
                or r.get('approved_for_import') is not False
                or any(r.get(k) is not None for k in ('buy_price', 'profit_jpy', 'market_median_jpy', 'ask_median_jpy'))
                or r.get('matched_sales') != 0 or r.get('matched_asks') != 0):
            raise ValueError('unsafe GLM claim import')
    return results


def summarize(rows, decisions):
    refs = [r for row in rows for r in row['references']]
    buyma_keys = [{(r['product_name'], r['price_jpy'], r['url']) for r in row['references']
                   if r['site'] == 'BUYMA' and r['product_name'] and r['price_jpy'] is not None}
                  for row in rows]
    common = set.intersection(*buyma_keys) if buyma_keys else set()
    return {'candidates': len(rows), 'reference_claims': len(refs),
            'reference_sites': dict(Counter(r['site'] for r in refs)),
            'reference_statuses': dict(Counter(r['status'] for r in refs)),
            'priced_reference_claims': sum(r['price_jpy'] is not None for r in refs),
            'missing_reference_observed_at': sum(not r['observed_at'].strip() for r in refs),
            'missing_reference_size': sum(r['size'].strip() in ('', '—', '-', '–') for r in refs),
            'missing_reported_sku': sum(not row['sku'].strip() for row in rows),
            'reported_verification_statuses': dict(Counter(row['verification_status'] for row in rows)),
            'common_buyma_listing_keys_across_all_candidates': len(common),
            'buyma_fallback_candidate_ids': [row['id'] for row in rows if any('BUYMA最低出品' in s for s in row['sources'])],
            'verified_offers': sum(r['buy_price'] is not None for r in decisions),
            'verified_sales': sum(r['matched_sales'] for r in decisions),
            'verified_profits': sum(r['profit_jpy'] is not None for r in decisions),
            'hold': sum(r['decision'] == 'HOLD' for r in decisions),
            'review_ready': sum(r['review_ready'] for r in decisions),
            'approved_for_import': sum(r['approved_for_import'] for r in decisions),
            'published': 0}


def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def audit(input_dir, out):
    input_dir = Path(input_dir)
    raw = {name: (input_dir / name).read_bytes() for name in FILES}
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in raw.items()}
    main = validate(load_json(raw['candidates.json'].decode('utf-8-sig')))
    csv_count = compare_csv(raw['candidates.csv'].decode('utf-8-sig'), main)
    test = validate(load_json(raw['discover_test.json'].decode('utf-8-sig')))
    # The CSV is another representation of the pilot, not another batch.
    # Discover is a separate diagnostic dataset, never merged into the pilot.
    claims = quarantine(main, 'candidates.json', hashes['candidates.json'])
    test_claims = quarantine(test, 'discover_test.json', hashes['discover_test.json'])
    decisions, test_decisions = decide(claims), decide(test_claims)
    report = {'status': 'QUARANTINE_ONLY', 'source_sha256': hashes,
              'csv_json_equivalent': True, 'csv_candidates': csv_count,
              'pilot': summarize(main, decisions), 'discover_test': summarize(test, test_decisions),
              'discover_merged_into_pilot': False, 'live_requests': 0, 'published': 0}
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    write_json(out / 'report_claims.json', claims)
    write_json(out / 'decisions.json', decisions)
    write_json(out / 'discover_test_claims.json', test_claims)
    write_json(out / 'discover_test_decisions.json', test_decisions)
    write_json(out / 'audit_summary.json', report)
    with (out / 'candidate_watchlist.csv').open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['candidate_id', 'brand', 'name', 'reported_style_code', 'reference_claims', 'decision', 'verified_buy_price', 'verified_stock', 'verified_profit_jpy'])
        writer.writeheader()
        for item, result in zip(claims, decisions):
            writer.writerow(dict(item['candidate'], reference_claims=len(item['report_claims']['references']),
                                 decision=result['decision'], verified_stock='UNKNOWN'))
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--input-dir', required=True)
    p.add_argument('--out', required=True)
    a = p.parse_args()
    print(json.dumps(audit(a.input_dir, a.out), ensure_ascii=False, indent=2))

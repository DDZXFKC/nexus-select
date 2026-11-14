"""Import GLM pilot report claims for review; never treat report text as verified offers.
Requires python-docx. No network, no external writes, no live verification.
"""
import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from docx import Document
from sourcing_gate import run

HEADER = ['ID', 'ブランド', '商品名', 'SKU', '買付価格(JPY)', '選定理由', 'SNKRDUNK', 'BUYMA', '判定']
DETAIL = ['ID', '商品', 'SKU', '買付価格', 'JPY換算', '海外在庫', '国内販売状況']

def table_rows(document, header):
    tables = [t for t in document.tables if [c.text.strip() for c in t.rows[0].cells] == header]
    if len(tables) != 1:
        raise ValueError('missing or ambiguous report table')
    rows = {}
    for row in tables[0].rows[1:]:
        data = dict(zip(header, (c.text.strip() for c in row.cells)))
        key = data['ID']
        if not re.fullmatch(r'AHC-\d+', key) or key in rows:
            raise ValueError('invalid or duplicate candidate ID')
        rows[key] = data
    return rows

def read_claims(path):
    document = Document(path)
    summary = table_rows(document, HEADER)
    detail = table_rows(document, DETAIL)
    if set(summary) != set(detail):
        raise ValueError('candidate table mismatch')
    refs = {k: [] for k in summary}
    seen = set()
    for paragraph in document.paragraphs:
        m = re.match(r'^\[(AHC-\d+)-(\d+)\]\s*(.*)$', paragraph.text)
        if not m:
            continue
        candidate_id, index, raw = m.groups()
        ref_id = candidate_id + '-' + index
        if candidate_id not in refs or ref_id in seen:
            raise ValueError('unknown or duplicate report reference')
        seen.add(ref_id)
        refs[candidate_id].append({'report_reference_id': ref_id, 'raw_report_text': raw,
                                   'status': 'UNVERIFIED_REPORT_CLAIM'})
    output = []
    for key, row in summary.items():
        d = detail[key]
        if row['SKU'] != d['SKU'] or row['買付価格(JPY)'] != d['JPY換算']:
            raise ValueError('report table value mismatch: ' + key)
        output.append({'candidate': {'candidate_id': key, 'brand': row['ブランド'],
                        'name': row['商品名'], 'reported_style_code': row['SKU']},
                       'offers': [], 'references': [], 'cost_inputs': {},
                       'report_claims': {'summary': row, 'detail': d, 'references': refs[key]}})
    return output

def audit(path, out):
    path = Path(path)
    data = read_claims(path)
    decisions = run(data, datetime.now(timezone.utc))
    if len(decisions) != len(data) or any(r.get('review_ready') or r.get('approved_for_import') or r.get('profit_jpy') is not None for r in decisions):
        raise ValueError('unsafe report import')
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    (out/'report_claims.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    (out/'decisions.json').write_text(json.dumps(decisions, ensure_ascii=False, indent=2), encoding='utf-8')
    with (out/'candidate_watchlist.csv').open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['candidate_id','brand','name','reported_style_code','reference_claims','decision','verified_buy_price','verified_stock','verified_profit_jpy'])
        writer.writeheader()
        for item in data:
            writer.writerow(dict(item['candidate'], reference_claims=len(item['report_claims']['references']),
                                 decision='HOLD', verified_stock='UNKNOWN'))
    report = dict(source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  candidates=len(data), reference_claims=sum(len(x['report_claims']['references']) for x in data),
                  verified_offers=0, verified_sales=0, verified_profits=0, hold=len(data), published=0)
    (out/'audit_summary.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--report', required=True)
    p.add_argument('--out', required=True)
    a = p.parse_args()
    print(json.dumps(audit(a.report, a.out)))

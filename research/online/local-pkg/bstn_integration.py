"""Import BSTN iMac evidence without silently treating merchant SKU as manufacturer SKU.

Offline only. Every source row is retained in a staging table and remains HOLD.
"""
import argparse
import csv
import json
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

CREATE = '''CREATE TABLE IF NOT EXISTS merchant_evidence (
 source_url TEXT NOT NULL, merchant_sku TEXT NOT NULL, size TEXT NOT NULL,
 brand TEXT NOT NULL, name TEXT NOT NULL, color_claim TEXT NOT NULL,
 price_claim TEXT NOT NULL, currency TEXT NOT NULL, stock_claim TEXT NOT NULL,
 observed_utc TEXT NOT NULL, manufacturer_sku TEXT NOT NULL DEFAULT '', product_id TEXT NOT NULL DEFAULT '',
 verification_state TEXT NOT NULL DEFAULT 'UNVERIFIED', decision TEXT NOT NULL DEFAULT 'HOLD',
 PRIMARY KEY(source_url, merchant_sku, size)
)'''

def import_csv(conn, filename):
    conn.execute(CREATE)
    added = rejected = 0
    with open(filename, encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            url = r.get('product_url', '')
            u = urlparse(url)
            if (u.scheme != 'https' or u.hostname not in ('www.bstn.com', 'bstn.com')
                or not all(r.get(k) for k in ('sku','size','brand','price','currency','observed_utc'))):
                rejected += 1
                continue
            # Evidence is not a verified offer: preserve even missing color.
            conn.execute('''INSERT INTO merchant_evidence
             (source_url,merchant_sku,size,brand,name,color_claim,price_claim,currency,stock_claim,observed_utc)
             VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(source_url,merchant_sku,size) DO UPDATE SET
             brand=excluded.brand,name=excluded.name,color_claim=excluded.color_claim,
             price_claim=excluded.price_claim,currency=excluded.currency,
             stock_claim=excluded.stock_claim,observed_utc=excluded.observed_utc,
             manufacturer_sku='',verification_state='UNVERIFIED',decision='HOLD' ''',
             (url,r['sku'],r['size'],r['brand'],r.get('name',''),r.get('color',''),
              r['price'],r['currency'],r.get('availability_claim',''),r['observed_utc']))
            added += 1
    conn.commit()
    return {'staged':added,'rejected':rejected,'auto_listed':0,'auto_purchased':0}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--csv',required=True)
    ap.add_argument('--db',required=True)
    args=ap.parse_args()
    conn=sqlite3.connect(args.db)
    print(json.dumps(import_csv(conn,Path(args.csv))))
    conn.close()

if __name__=='__main__': main()

#!/usr/bin/env python3
"""Select the next ten from the local 158 eligible products, then reuse batch 1 generator.
No listing, network, price changes or source file writes."""
import argparse
import csv
import json
import pathlib
import subprocess
import sys
import tempfile

def read(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        reader=csv.DictReader(f)
        fields=reader.fieldnames
        if not fields or len(set(fields))!=len(fields):
            raise ValueError('invalid CSV header: '+str(path))
        rows=list(reader)
    if any(None in r or any(v is None for v in r.values()) for r in rows):
        raise ValueError('malformed CSV: '+str(path))
    return fields,rows

def ids(rows,key):
    values=[r.get(key,'').strip() for r in rows]
    if not all(values) or len(set(values))!=len(values):
        raise ValueError('missing or duplicate product ID: '+key)
    return values

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--eligible',required=True,type=pathlib.Path,help='local final 158 eligible product CSV, in batch 1 selection order')
    p.add_argument('--batch1',required=True,type=pathlib.Path,help='actual batch 1 ten-product manifest CSV')
    p.add_argument('--key',default='product_id')
    p.add_argument('--batch1-key',default=None)
    p.add_argument('--output',required=True,type=pathlib.Path,help='new batch 2 directory; must not exist')
    p.add_argument('--generator',required=True,help='JSON argv array for existing batch 1 generator; use {input} and {output} placeholders')
    a=p.parse_args()
    fields,rows=read(a.eligible)
    if 'verdict' in fields:
        rows=[r for r in rows if r['verdict']=='販売可能']
    all_ids=ids(rows,a.key)
    _,previous=read(a.batch1)
    old=ids(previous,a.batch1_key or a.key)
    if len(all_ids)!=158 or len(old)!=10 or not set(old)<=set(all_ids):
        raise ValueError('expected 158 eligible and 10 distinct batch 1 IDs within eligible set')
    selected=[r for r in rows if r[a.key].strip() not in set(old)][:10]
    if len(selected)!=10:
        raise ValueError('not enough remaining products')
    argv=json.loads(a.generator)
    if not isinstance(argv,list) or not argv or not all(isinstance(x,str) for x in argv) or not any('{input}' in x for x in argv) or not any('{output}' in x for x in argv):
        raise ValueError('generator must be JSON argv with input and output placeholders')
    a.output.mkdir(parents=False,exist_ok=False)
    manifest=a.output/'batch2_selection.csv'
    with manifest.open('x',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader()
        w.writerows(selected)
    result=a.output/'listing_data'
    cmd=[x.replace('{input}',str(manifest.resolve())).replace('{output}',str(result.resolve())) for x in argv]
    subprocess.run(cmd,check=True)
    if not result.exists():
        raise ValueError('existing generator did not produce expected output')
    print(json.dumps({'selected_ids':ids(selected,a.key),'count':10,'output':str(result)},ensure_ascii=False))

if __name__=='__main__':
    try:
        main()
    except (ValueError,OSError,subprocess.CalledProcessError) as exc:
        sys.exit(str(exc))

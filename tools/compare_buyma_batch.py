#!/usr/bin/env python3
"""Compare actual generated files against reference, reporting every cell difference."""
import argparse,csv,json
from pathlib import Path
def load(p):
    with p.open(encoding='utf-8-sig',newline='') as f:
        r=csv.reader(f);return list(r)
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--actual',type=Path,required=True)
    p.add_argument('--expected',type=Path,required=True)
    p.add_argument('--prefix',default='batch1')
    a=p.parse_args();diff=[];stats={}
    for suffix in ('items','colorsizes'):
        name=a.prefix+'_'+suffix+'.csv'
        x=load(a.actual/name);y=load(a.expected/name)
        stats[name]={'actual_rows':len(x)-1,'expected_rows':len(y)-1,'byte_equal':(a.actual/name).read_bytes()==(a.expected/name).read_bytes()}
        for i in range(max(len(x),len(y))):
            u=x[i] if i<len(x) else [];v=y[i] if i<len(y) else []
            for j in range(max(len(u),len(v))):
                aa=u[j] if j<len(u) else None;bb=v[j] if j<len(v) else None
                if aa!=bb:diff.append({'file':name,'row':i+1,'column':j+1,'actual':aa,'expected':bb})
        if suffix=='colorsizes':
            k=y[0].index('検索用サイズ')
            stats[name]['actual_blank_search']=sum(not r[k] for r in x[1:])
            stats[name]['expected_blank_search']=sum(not r[k] for r in y[1:])
    print(json.dumps({'stats':stats,'differences':diff},ensure_ascii=False,indent=2))
    return bool(diff)
if __name__=='__main__':raise SystemExit(main())

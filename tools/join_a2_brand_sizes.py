#!/usr/bin/env python3
"""G-1: join A2 brand-size export to selected Shoe Palace variants.
Read-only source; ambiguous/conflicting/unknown data are HOLD, never inferred.
"""
import argparse,csv,json,re,sys
from collections import defaultdict
from pathlib import Path
from decimal import Decimal,InvalidOperation

def load(path):
    with open(path,encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or len(set(reader.fieldnames))!=len(reader.fieldnames):
            raise ValueError('invalid CSV header '+str(path))
        rows=list(reader)
        if any(None in r or None in r.values() for r in rows):
            raise ValueError('malformed CSV '+str(path))
        return rows

def size(s):
    m=re.fullmatch(r'(?:US\s*)?(\d+(?:\.\d+)?)([CY]?)',s.strip().upper())
    if not m: raise ValueError('unsupported size '+s)
    return format(Decimal(m[1]).normalize(),'f')+m[2]

def cm(s):
    if not s.strip(): return ''
    d=Decimal(s.strip())
    if not d.is_finite() or d<=0: raise ValueError('invalid cm '+s)
    return format(d.normalize(),'f')

def div(s):
    v={'men':'Men','women':'Women','kids':'Kids'}.get(s.strip().lower())
    if not v: raise ValueError('unknown department '+s)
    return v

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--a2',required=True,type=Path,help='actual A2 brand-size CSV')
    p.add_argument('--variants',required=True,type=Path,help='selected variant CSV')
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--config',required=True,type=Path,help='JSON mapping source headers to canonical names')
    a=p.parse_args()
    if a.output.exists(): raise ValueError('output exists')
    cfg=json.loads(a.config.read_text(encoding='utf-8'))
    c=cfg['a2_columns'];v=cfg['variant_columns']
    required_a=('brand','department','size_original','cm','source_url')
    required_v=('sku','product_id','variant_id','brand','department','size_original')
    charts=defaultdict(list)
    for r in load(a.a2):
        k=(r[c['brand']].strip().upper(),div(r[c['department']]),size(r[c['size_original']]))
        source=r[c['source_url']].strip()
        value=cm(r[c['cm']])
        # Explicit missing JP/CM is not a usable conversion.
        if value and not source.startswith('https://'): raise ValueError('missing chart provenance '+str(k))
        charts[k].append((value,source,r.get(c.get('scope',''),'').strip()))
    result=[];seen=set()
    for r in load(a.variants):
        vid=r[v['variant_id']].strip()
        if not vid or vid in seen: raise ValueError('duplicate variant ID '+vid)
        seen.add(vid)
        sku=r[v['sku']].strip();pid=r[v['product_id']].strip()
        if not sku or not pid: raise ValueError('missing identity')
        brand=r[v['brand']].strip().upper();department=div(r[v['department']])
        original=size(r[v['size_original']])
        k=(brand,department,original)
        values=charts.get(k,[])
        # Scope-specific charts may only apply when exact product ID matches.
        applicable=[(val,source,scope) for val,source,scope in values if not scope or scope==pid]
        resolved={(val,source) for val,source,_ in applicable if val}
        cm_values={val for val,_ in resolved}
        if len(cm_values)>1: status='HOLD_CONFLICT';chosen=('','')
        elif len(cm_values)==1:
            # More than one provenance for same cm is acceptable, deterministically select.
            chosen=sorted(resolved)[0];status='MATCHED'
        else: chosen=('','');status='HOLD_NO_JP_CM' if applicable else 'HOLD_NO_CHART'
        # UGG infant/toddler 4C is ambiguous for three known variants.
        if vid in {'41707750162638','42228915372238','42843176403150'}:
            chosen=('','');status='HOLD_UGG_INFANT_AMBIGUITY'
        result.append({'sku':sku,'product_id':pid,'variant_id':vid,'brand':brand,
                       'department':department,'size_original':original,
                       'cm':chosen[0],'source_url':chosen[1],'status':status,
                       'source_candidates':str(len(applicable))})
    a.output.parent.mkdir(parents=True,exist_ok=True)
    fields=['sku','product_id','variant_id','brand','department','size_original','cm','source_url','status','source_candidates']
    with a.output.open('x',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(result)
    stats={s:sum(r['status']==s for r in result) for s in sorted(set(r['status'] for r in result))}
    print(json.dumps({'total':len(result),'status':stats,'output':str(a.output)},ensure_ascii=False))
    if cfg.get('require_all_matched',False) and any(r['status']!='MATCHED' for r in result):
        return 2
    return 0

if __name__=='__main__':
    try: sys.exit(main())
    except (ValueError,KeyError,OSError,InvalidOperation) as exc:sys.exit(str(exc))

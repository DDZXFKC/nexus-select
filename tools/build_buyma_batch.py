#!/usr/bin/env python3
"""Generate exact batch1 BUYMA CSV layout from selected SKUs and original inputs."""
import argparse,csv,json,re,math,tempfile
from pathlib import Path
from collections import defaultdict
from decimal import Decimal

COLORSYS={'black':2,'white':1,'grey':3,'gray':3,'brown':4,'chestnut':4,'beige':5,'alabaster':1,
'green':6,'blue':7,'purple':8,'yellow':9,'pink':10,'red':11,'orange':12,'silver':13,'gold':14,
'navy':16,'cream':5,'tan':4,'olive':6,'maroon':11,'charcoal':3,'stucco':5,'rose':10,'carnation':10,
'mauve':8,'stellar':3,'galactic':3,'squid':2,'truffle':4,'salt':1,'sea':6,'oatmeal':5,'faded':2}

def color_of(name):
    m=re.search(r'\(([^)]*)\)\s*$', name)
    return m.group(1) if m else ''
def sys_of(color):
    main=color.split('/')[0].strip().lower()
    for k,v in COLORSYS.items():
        if main.startswith(k) or k in main: return v
    return 99


cols=['商品管理番号','コントロール','商品名','ブランド','ブランド名','カテゴリ','シーズン','テーマ','単価','買付可数量','購入期限','参考価格/通常出品価格','参考価格','商品コメント','配送方法','買付エリア','買付都市','買付ショップ','発送エリア','発送都市','関税込み','商品イメージ1','商品イメージ2','商品イメージ3','出品メモ','買付先メモ']

ccols=['商品管理番号','並び順','サイズ名称','検索用サイズ','色名称','色系統','在庫ステータス','手元に在庫あり数量']

def read(path):
    with open(path,encoding='utf-8-sig',newline='') as f:
        r=csv.DictReader(f)
        if not r.fieldnames or len(set(r.fieldnames))!=len(r.fieldnames):
            raise ValueError('invalid CSV header')
        rows=list(r)
        if any(None in x or None in x.values() for x in rows):
            raise ValueError('malformed CSV')
        return rows

def norm(s):
    m=re.fullmatch(r'(?:US\s*)?(\d+(?:\.\d+)?)([CY]?)',str(s).strip().upper())
    if not m: raise ValueError('unsupported size '+str(s))
    return format(Decimal(m[1]).normalize(),'f')+m[2]

def unique(rows,key):
    out={}
    for r in rows:
        k=r[key]
        if not k or k in out: raise ValueError('duplicate or empty '+key+': '+k)
        out[k]=r
    return out

def sizebook(path):
    raw=Path(path).read_text(encoding='utf-8-sig')
    if '{' in raw and 'values' in raw:
        rows=json.loads(raw[raw.index('{'):])['values'][1:]
    else:
        rows=[[r['brand'],r['department'],r['size_original'],r['cm']] for r in read(path)]
    out={}
    for row in rows:
        if len(row)<4 or not row[3]: continue
        key=(row[0].upper(),row[1],norm(row[2]))
        cm=Decimal(str(row[3]))
        if not cm.is_finite() or cm<=0: raise ValueError('invalid cm')
        if key in out and out[key]!=cm: raise ValueError('conflicting chart '+str(key))
        out[key]=cm
    return out

def division(name):
    if re.search(r'\b(?:Grade School|Little Kids|Big Kids|Toddler|Infant|Preschool|Kids)\b',name,re.I): return 'Kids'
    if re.search(r'\bWomens\b',name,re.I): return 'Women'
    if re.search(r'\bMens\b',name,re.I): return 'Men'
    raise ValueError('unknown department '+name)

def generate(selected,woo,config,book,allow_missing=False,approved_categories=None):
    approved_categories = approved_categories or {}
    parents=unique([r for r in woo if r['Type']=='variable'],'SKU')
    variations=defaultdict(list)
    for r in woo:
        if r['Type']=='variation': variations[r['Parent']].append(r)
    sources={b:unique(read(c['source']),'productId') for b,c in config['brands'].items()}
    items=[]; cs=[]
    for sku in selected:
        p=parents[sku]; brand=p['Brand']; cfg=config['brands'][brand]
        if brand=='CONVERSE': raise ValueError('BUYMA Converse disabled')
        if brand=='UGG' and str(cfg['brand_id'])!='89': raise ValueError('UGG ID must be 89')
        src=sources[brand][sku.removeprefix('SP-')]
        name=p['Name']; div=division(name); color=color_of(name)
        if not color: raise ValueError('missing color '+sku)
        sysid=sys_of(color)
        if not allow_missing:
            sysid=cfg['color_ids'][color]
        imgs=[u.strip() for u in p['Images'].split(',') if u.strip()]
        price=int(p['Regular price'])
        if price<=0: raise ValueError('invalid price')
        if not allow_missing:
            price=int(cfg['approved_buyma_prices'][sku])
            if price<=0: raise ValueError('invalid approved price')
        vs=variations[sku]
        if not any(v['In stock?']=='1' for v in vs): raise ValueError('no stock '+sku)
        items.append(dict(zip(cols,[sku,'下書き',name,str(cfg['brand_id']),cfg['brand_name'],str(approved_categories.get(sku, cfg['categories'][div])),'51','0',str(price),'1','','0','',(src['description_en'] or '')[:900],'1103985','2001001','0','Shoe Palace','','','1',*(imgs+['','',''])[:3],'追加画像：'+' '.join(imgs[3:]) if len(imgs)>3 else '',src['url']])))
        def sortkey(v):
            s=norm(v['Attribute 1 value'])
            return (1 if s.endswith('Y') else 0,Decimal(s.rstrip('CY')))
        seen=set()
        for n,v in enumerate(sorted(vs,key=sortkey),1):
            us=norm(v['Attribute 1 value'])
            if us in seen: raise ValueError('duplicate size '+sku+' '+us)
            seen.add(us)
            if v['In stock?'] not in ('0','1'): raise ValueError('invalid stock')
            cm=book.get((brand,div,us))
            if brand=='UGG' and div=='Kids':
                if us not in cfg.get('verified_kids_sizes',{}).get(sku,[]): raise ValueError('unverified Kids size '+sku+' '+us)
            if cm is None and not allow_missing: raise ValueError('missing size '+sku+' '+us)
            label='US '+(us if us.endswith(('C','Y')) else f'{Decimal(us):.1f}')
            search=str(int(cm*10)) if cm is not None else ''
            cs.append(dict(zip(ccols,[sku,str(n),label,search,color,str(sysid),v['In stock?'],''])))
    return items,cs

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--config',required=True,type=Path)
    p.add_argument('--prefix',default='batch2')
    p.add_argument('--preflight-dir',type=Path,help='mandatory for batch3: passed E-1 preflight audit')
    p.add_argument('--reproduce-batch1',action='store_true',help='historical reproduction only; not for listing')
    a=p.parse_args()
    cfg=json.loads(a.config.read_text(encoding='utf-8'))
    selected=[r[cfg.get('selection_sku','SKU')] for r in read(a.input)]
    if len(selected)!=10 or len(set(selected))!=10 or not all(selected): raise ValueError('expected 10 distinct SKUs')
    if not re.fullmatch(r'[A-Za-z0-9_-]+',a.prefix): raise ValueError('invalid prefix')
    if a.reproduce_batch1 and a.prefix!='batch1': raise ValueError('historical mode requires batch1 prefix')
    approved_categories = {}
    if a.prefix == 'batch3':
        if a.reproduce_batch1 or a.preflight_dir is None:
            raise ValueError('batch3 requires a passing --preflight-dir; historical mode forbidden')
        import hashlib
        def sha(path):
            return hashlib.sha256(path.read_bytes()).hexdigest()
        manifest_path = a.preflight_dir / 'preflight_manifest.json'
        csv_path = a.preflight_dir / 'preflight.csv'
        receipt = json.loads(manifest_path.read_text(encoding='utf-8'))
        if receipt.get('preflight_version') != 'batch3-e1-preflight-v1':
            raise ValueError('wrong preflight version')
        if receipt.get('selection_sha256') != sha(a.input):
            raise ValueError('selection differs from preflight snapshot')
        if receipt.get('preflight_csv_sha256') != sha(csv_path):
            raise ValueError('preflight CSV differs from audited snapshot')
        if receipt.get('pool_count') != 163 or receipt.get('pass_count') != 10 or receipt.get('hold_count') != 0:
            raise ValueError('batch3 requires 163-row pool and all 10 PASS')
        audited = unique(read(csv_path), 'sku')
        if set(audited) != set(selected) or any(r['preflight_status'] != 'PASS' for r in audited.values()):
            raise ValueError('preflight SKUs or status mismatch')
        approved_categories = {sku: audited[sku]['selected_category_id'] for sku in selected}
        if any(not x.isdecimal() for x in approved_categories.values()):
            raise ValueError('invalid approved category')
    elif a.preflight_dir is not None:
        raise ValueError('preflight-dir only supported for batch3')
    items,cs=generate(selected,read(cfg['woo']),cfg,sizebook(cfg['size_table']),
                      a.reproduce_batch1,approved_categories)
    if a.output.exists(): raise ValueError('output exists')
    with tempfile.TemporaryDirectory(dir=a.output.parent) as t:
        d=Path(t)/'out';d.mkdir()
        for suffix,fields,rows in [('items',cols,items),('colorsizes',ccols,cs)]:
            with (d/(a.prefix+'_'+suffix+'.csv')).open('w',encoding='utf-8-sig',newline='') as f:
                w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
        d.rename(a.output)
    print(json.dumps({'items':len(items),'colorsizes':len(cs),'missing_search':sum(not r['検索用サイズ'] for r in cs)}))

if __name__=='__main__': main()

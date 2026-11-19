import csv, json, math, re
from collections import defaultdict

BASE='/home/hatch/workspace/'
# --- size table (brand size book export) ---
raw=open('/tmp/size_table.csv',encoding='utf-8').read()
d=json.loads(raw[raw.index('{'):])
sizes={}
for row in d['values'][1:]:
    if len(row)>=4:
        sizes[(row[0].upper(), row[1], row[2].rstrip('0').rstrip('.') if '.' in row[2] else row[2])]=row[3]
def cm_for(brand, div, us):
    usn = str(float(us)) if '.' in str(us) else str(us)
    usn = usn.rstrip('0').rstrip('.') if '.' in usn else usn
    for key in [(brand,div,usn),(brand,div,str(us))]:
        if key in sizes: return sizes[key]
    return None

# --- SP raw (HOKA) ---
hoka={}
with open(BASE+'fl-scrape/shoepalace-hoka-all.csv',encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        hoka[r['productId']]=r

# --- Woo prep ---
parents=[]; variations=defaultdict(list)
with open(BASE+'fl-scrape/shoepalace-woo-import-prep.csv',encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        if r['Type']=='variable': parents.append(r)
        elif r['Type']=='variation': variations[r['Parent']].append(r)

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

items_out=[]; cs_out=[]; summary=[]
hoka_parents=[p for p in parents if p['Brand']=='HOKA']
# order by rank in hoka csv
rank={pid:i for i,pid in enumerate(hoka.keys())}
hoka_parents.sort(key=lambda p: rank.get(p['SKU'][3:], 999))
picked=0
for p in hoka_parents:
    if picked>=10: break
    pid=p['SKU'][3:]
    src=hoka.get(pid)
    if not src: continue
    vs=variations[p['SKU']]
    if not any(v['In stock?']=='1' for v in vs): continue
    name=p['Name']
    div='Men' if 'Mens' in name else ('Women' if 'Womens' in name else None)
    if div is None: continue
    usd=float(src['priceMin'])
    cost=round(usd*158*1.02+2200+1500+60)
    price=int(p['Regular price'])
    calc=math.ceil(cost/0.745/100)*100
    color=color_of(name); sysid=sys_of(color)
    imgs=[u.strip() for u in p['Images'].split(',') if u.strip()]
    items_out.append({
      '商品管理番号':p['SKU'],'コントロール':'下書き','商品名':name,'ブランド':'6906','ブランド名':'HOKA ONE ONE',
      'カテゴリ':'3321' if div=='Men' else '3081','シーズン':'51','テーマ':'0','単価':str(price),'買付可数量':'1',
      '購入期限':'','参考価格/通常出品価格':'0','参考価格':'',
      '商品コメント':(src['description_en'] or '')[:900],
      '配送方法':'1103985','買付エリア':'2001001','買付都市':'0','買付ショップ':'Shoe Palace',
      '発送エリア':'','発送都市':'','関税込み':'1',
      '商品イメージ1':imgs[0] if len(imgs)>0 else '','商品イメージ2':imgs[1] if len(imgs)>1 else '',
      '商品イメージ3':imgs[2] if len(imgs)>2 else '',
      '出品メモ':'追加画像：'+' '.join(imgs[3:]) if len(imgs)>3 else '',
      '買付先メモ':src['url']})
    n=0
    def usnum(v):
        m=re.search(r'US\s*([0-9.]+)', v); return m.group(1) if m else v
    vs_sorted=sorted(vs, key=lambda v: float(usnum(v['Attribute 1 value'])))
    for v in vs_sorted:
        n+=1
        us=usnum(v['Attribute 1 value'])
        cm=cm_for('HOKA', div, us)
        cs_out.append({'商品管理番号':p['SKU'],'並び順':str(n),'サイズ名称':f'US {float(us):.1f}',
          '検索用サイズ':str(int(float(cm)*10)) if cm else '','色名称':color,'色系統':str(sysid),
          '在庫ステータス':v['In stock?'],'手元に在庫あり数量':''})
    fee=round(price*0.055)
    summary.append({'sku':p['SKU'],'name':name,'usd':usd,'cost':cost,'price':price,'calc':calc,
      'match':price==calc,'profit_after_fee':price-cost-fee,'instock_sizes':sum(1 for v in vs if v['In stock?']=='1'),
      'total_sizes':len(vs),'color':color,'sys':sysid,'img':imgs[0] if imgs else ''})
    picked+=1

cols=['商品管理番号','コントロール','商品名','ブランド','ブランド名','カテゴリ','シーズン','テーマ','単価','買付可数量','購入期限','参考価格/通常出品価格','参考価格','商品コメント','配送方法','買付エリア','買付都市','買付ショップ','発送エリア','発送都市','関税込み','商品イメージ1','商品イメージ2','商品イメージ3','出品メモ','買付先メモ']
with open(BASE+'buyma/sp-listing/batch1_items.csv','w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=cols); w.writeheader(); w.writerows(items_out)
ccols=['商品管理番号','並び順','サイズ名称','検索用サイズ','色名称','色系統','在庫ステータス','手元に在庫あり数量']
with open(BASE+'buyma/sp-listing/batch1_colorsizes.csv','w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=ccols); w.writeheader(); w.writerows(cs_out)
print(json.dumps(summary,ensure_ascii=False,indent=1))
print('items:',len(items_out),'colorsizes:',len(cs_out))

import csv, re, json, collections

SRC='/home/hatch/workspace/fl-scrape/shoepalace-woo-import-158.csv'
OUT='/home/hatch/workspace/fl-scrape/shoepalace-woo-import-final.csv'
MAP='/home/hatch/workspace/fl-scrape/sp-category-map.json'

# --- brand kids size charts (JP cm for UGG/Vans; HOKA foot-length cm, double-sourced official reprints) ---
UGG={'4C':11.5,'5C':12.5,'6C':13,'7C':14,'8C':15,'9C':16,'10C':17,'11C':18,'12C':19,'13C':20,
     '1Y':21,'2Y':22,'3Y':23,'4Y':24,'5Y':25,'6Y':26}
# half sizes on the JP scale = whole + 0.5 (scale arithmetic)
for base in ['10C','11C','12C','13C','1Y','2Y','3Y','4Y','5Y','6Y']:
    num=float(base[:-1]); half=f"{num+0.5:g}"+base[-1]
    UGG[half]=UGG[base]+0.5
VANS={'10.5C':16.5,'11C':17,'11.5C':17.5,'12C':18,'12.5C':18.5,'13C':19,'13.5C':19.5,
      '1Y':20,'2Y':21,'3Y':22,'3.5Y':21.5,'4Y':22,'4.5Y':22.5,'5Y':23,'5.5Y':23.5,'6Y':24,'6.5Y':24.5,'7Y':25}
HOKA={'10C':15.5,'10.5C':16,'11C':16.5,'11.5C':17,'12C':18,'12.5C':18.5,'13C':19,'13.5C':19,
      '1Y':19.5,'1.5Y':20,'2Y':20.5,'2.5Y':21,'3Y':21.5,'3.5Y':22,'4Y':22.5,'4.5Y':23,'5Y':23.5,'5.5Y':24,'6Y':24.5,'6.5Y':25,'7Y':25.5}
CHARTS={'UGG':UGG,'Vans':VANS,'HOKA':HOKA}

def gender_of(name):
    if any(t in name for t in ['Grade School','Toddler','Infant','Preschool','Little Kids','Big Kids']): return 'kids'
    if 'Womens' in name: return 'womens'
    if 'Mens' in name: return 'mens'
    return None

def leaf_of(name):
    n=re.sub(r'\s*\([^)]*\)\s*$','',name)
    if n.endswith('Hoodie'): return 'hoodie'
    if n.endswith('Pants'): return 'pants'
    if n.endswith('Jacket'): return 'jacket'
    if n.endswith('Boots') or n.endswith('Boot'): return 'boots'
    if n.endswith('Sandals') or n.endswith('Sandal'): return 'sandals'
    if 'Running' in n: return 'running'
    return 'sneakers'
GROUP={'sneakers':'shoes','running':'shoes','basketball':'shoes','boots':'shoes','sandals':'shoes',
       'hoodie':'clothing','pants':'clothing','jacket':'clothing'}

rows=list(csv.DictReader(open(SRC)))
fields=list(rows[0].keys())
parents={r['SKU']:r for r in rows if r['Type']=='variable'}

# name fix
fixed=[]
for r in rows:
    if r['Type']=='variable' and r['Name'].endswith('Free Shipping'):
        r['Name']=r['Name'].replace(' Free Shipping','').strip()
        fixed.append(r['SKU'])

# category map
catmap={}
for sku,r in parents.items():
    g=gender_of(r['Name']); leaf=leaf_of(r['Name'])
    catmap[sku]=[g, f"{g}-{GROUP[leaf]}", f"{g}-{leaf}"]

# kids cm annotation
unannotated=[]
def annotate(size_label, brand):
    m=re.match(r'^US ([0-9.]+[CY])$', size_label)
    if not m: return size_label
    core=m.group(1)
    chart=CHARTS.get(brand)
    if chart and core in chart:
        cm=chart[core]
        cm_s=f"{cm:g}"
        return f"US {core} ({cm_s}cm)"
    unannotated.append((brand,size_label))
    return size_label

kids_skus={s for s,r in parents.items() if gender_of(r['Name'])=='kids'}
for r in rows:
    if r['Type']=='variation' and r['Parent'] in kids_skus:
        brand=parents[r['Parent']]['Brand']
        r['Attribute 1 value']=annotate(r['Attribute 1 value'], brand)
# parent value(s) lists for kids
for sku in kids_skus:
    r=parents[sku]; brand=r['Brand']
    vals=[v.strip() for v in r['Attribute 1 value(s)'].split(',')] if r['Attribute 1 value(s)'] else []
    r['Attribute 1 value(s)']=','.join(annotate(v, brand) for v in vals)

with open(OUT,'w',newline='') as f:
    w=csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
json.dump(catmap, open(MAP,'w'), ensure_ascii=False, indent=1)

print('rows:', len(rows), 'name fixed:', fixed)
print('catmap entries:', len(catmap))
print('leaf counts:', collections.Counter(v[2] for v in catmap.values()))
print('unannotated kids sizes:', collections.Counter(unannotated))

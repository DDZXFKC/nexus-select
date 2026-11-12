"""Single-command, multi-merchant evidence -> review exports; never publishes.
Python 3.9 standard library. Source CSV must come from permitted collection.
"""
import argparse,csv,json,sqlite3,decimal,re
from pathlib import Path
from urllib.parse import urlparse
from bstn_integration import CREATE
from channel_exports_v2 import export
D=decimal.Decimal
FIELDS=['product_url','product_id','shop','brand','name','sku','manufacturer_sku','color','size','price','currency','availability_claim','observed_utc','image_urls','description','category','ship_from','shipping_cost','import_tax','partner_fee','international_shipping','platform_fee_rate','fx_jpy','selling_price_jpy','image_rights']
EXT='''CREATE TABLE IF NOT EXISTS product_enrichment (source_url TEXT NOT NULL,merchant_sku TEXT NOT NULL,size TEXT NOT NULL,image_urls TEXT NOT NULL DEFAULT '',description TEXT NOT NULL DEFAULT '',category TEXT NOT NULL DEFAULT '',ship_from TEXT NOT NULL DEFAULT '',shipping_cost TEXT NOT NULL DEFAULT '',import_tax TEXT NOT NULL DEFAULT '',partner_fee TEXT NOT NULL DEFAULT '',international_shipping TEXT NOT NULL DEFAULT '',platform_fee_rate TEXT NOT NULL DEFAULT '',fx_jpy TEXT NOT NULL DEFAULT '',selling_price_jpy TEXT NOT NULL DEFAULT '',image_rights TEXT NOT NULL DEFAULT '',product_id TEXT NOT NULL DEFAULT '',PRIMARY KEY(source_url,merchant_sku,size))'''
def is_money(v):
 try: return D(str(v)).is_finite() and D(str(v))>=0
 except (decimal.InvalidOperation,ValueError):return False
def stage(conn,csvpath):
 conn.execute(CREATE);conn.execute(EXT);stats={'accepted':0,'rejected':0,'rejection_reasons':{}}
 with open(csvpath,encoding='utf-8-sig',newline='') as f:
  reader=csv.DictReader(f)
  for r in reader:
   url=r.get('product_url','').strip();u=urlparse(url)
   mandatory=['sku','size','brand','price','currency','observed_utc']
   reason=next((k+'_missing' for k in mandatory if not r.get(k,'' ).strip()),None)
   if not reason and (u.scheme!='https' or not u.hostname or u.username or u.password):reason='invalid_https_url'
   if not reason and not is_money(r['price']):reason='invalid_price'
   if not reason and not re.fullmatch(r'[A-Z]{3}',r['currency'].strip()):reason='invalid_currency'
   if reason:
    stats['rejected']+=1;stats['rejection_reasons'][reason]=stats['rejection_reasons'].get(reason,0)+1;continue
   key=(url,r['sku'].strip(),r['size'].strip())
   conn.execute('''INSERT INTO merchant_evidence (source_url,merchant_sku,size,brand,name,color_claim,price_claim,currency,stock_claim,observed_utc,manufacturer_sku,product_id,verification_state,decision) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,'UNVERIFIED','HOLD') ON CONFLICT(source_url,merchant_sku,size) DO UPDATE SET brand=excluded.brand,name=excluded.name,color_claim=excluded.color_claim,price_claim=excluded.price_claim,currency=excluded.currency,stock_claim=excluded.stock_claim,observed_utc=excluded.observed_utc,manufacturer_sku=excluded.manufacturer_sku,product_id=excluded.product_id,verification_state='UNVERIFIED',decision='HOLD' ''',key+(r['brand'],r.get('name',''),r.get('color',''),r['price'],r['currency'],r.get('availability_claim',''),r['observed_utc'],r.get('manufacturer_sku',''),r.get('product_id','')))
   enriched=[r.get(k,'') for k in ('image_urls','description','category','ship_from','shipping_cost','import_tax','partner_fee','international_shipping','platform_fee_rate','fx_jpy','selling_price_jpy','image_rights')]
   conn.execute('INSERT INTO product_enrichment VALUES ('+','.join('?' for _ in range(16))+') ON CONFLICT(source_url,merchant_sku,size) DO UPDATE SET '+','.join(k+'=excluded.'+k for k in ('image_urls','description','category','ship_from','shipping_cost','import_tax','partner_fee','international_shipping','platform_fee_rate','fx_jpy','selling_price_jpy','image_rights')),key+tuple(enriched)+(r.get('product_id',''),))
   stats['accepted']+=1
 conn.commit();return stats

def profit_review(conn,out):
 rows=conn.execute('''SELECT m.source_url,m.merchant_sku,m.size,m.price_claim,m.currency,e.shipping_cost,e.import_tax,e.partner_fee,e.international_shipping,e.platform_fee_rate,e.fx_jpy,e.selling_price_jpy,e.image_rights,e.image_urls,m.product_id FROM merchant_evidence m LEFT JOIN product_enrichment e ON (m.source_url=e.source_url AND m.merchant_sku=e.merchant_sku AND m.size=e.size)''').fetchall()
 fields=['source_url','merchant_sku','size','currency','source_price','selling_price_jpy','cost_jpy','estimated_profit_jpy','missing_cost_inputs','image_rights','image_urls','status']
 with (out/'profit_review.csv').open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for url,sku,size,price,cur,ship,tax,partner,intship,fee,fx,sell,rights,images,_pid in rows:
   raw={'shipping_cost':ship,'import_tax':tax,'partner_fee':partner,'international_shipping':intship,'platform_fee_rate':fee,'fx_jpy':fx,'selling_price_jpy':sell}
   missing=[k for k,v in raw.items() if v is None or v=='' or not is_money(v)]
   if not missing and D(fee)>1:missing.append('platform_fee_rate_out_of_range')
   cost=profit=''
   if not missing:
    # shipping_cost in source currency; import tax, partner fee, international shipping in JPY
    cost=(D(price)+D(ship))*D(fx)+D(tax)+D(partner)+D(intship)
    profit=D(sell)*(1-D(fee))-cost
    cost=str(cost.quantize(D('0.01')));profit=str(profit.quantize(D('0.01')))
   w.writerow({'source_url':url,'merchant_sku':sku,'size':size,'currency':cur,'source_price':price,'selling_price_jpy':sell or '', 'cost_jpy':cost,'estimated_profit_jpy':profit,'missing_cost_inputs':'|'.join(missing),'image_rights':rights or '', 'image_urls':images or '', 'status':'HOLD'})
 return len(rows)

def run(csvpath,db,out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 conn=sqlite3.connect(db)
 try:
  stats=stage(conn,csvpath);profit_count=profit_review(conn,out)
 finally:conn.close()
 grouped=export(db,out)
 report={'stage':stats,'grouped_products':grouped['grouped_products'],'woo_rows':grouped['woo_rows'],'buyma_products':grouped['buyma_products'],'profit_rows':profit_count,'published':0,'status':'REVIEW_ONLY','note':'No actual platform import or live stock validation performed. Prices remain blank in channel exports.'}
 (out/'pipeline_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--csv',required=True);p.add_argument('--db',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 print(json.dumps(run(a.csv,a.db,a.out),ensure_ascii=False))

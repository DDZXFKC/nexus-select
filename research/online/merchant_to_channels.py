"""Local saved merchant HTML to conservative two-channel review exports; Python 3.9."""
import argparse,csv,json,sqlite3
from pathlib import Path
from collector import parse
from production_pipeline import FIELDS,stage,profit_review
from channel_ready_v4 import export
def run(manifest,db,out):
 manifest=Path(manifest).resolve();out=Path(out).resolve()
 with manifest.open(encoding="utf-8-sig",newline="") as f:
  reader=csv.DictReader(f)
  if not reader.fieldnames or not {"html_file","product_url"}.issubset(reader.fieldnames):raise ValueError("manifest requires html_file,product_url")
  entries=list(reader)
 if not entries:raise ValueError("empty manifest")
 out.mkdir(parents=True,exist_ok=True);rows=[];pages=[]
 for entry in entries:
  path=(manifest.parent/entry["html_file"]).resolve()
  if manifest.parent not in path.parents:raise ValueError("HTML path outside manifest directory")
  if path.stat().st_size>3000000:raise ValueError("HTML too large")
  parsed=parse(path.read_text(encoding="utf-8"),entry["product_url"])
  for item in parsed:
   record={k:item.get(k,"") for k in FIELDS}
   record["manufacturer_sku"]="";record["image_rights"]=""
   rows.append(record)
  pages.append({"url":entry["product_url"],"size_rows":len(parsed)})
 if not rows:raise ValueError("No JSON-LD products parsed")
 staging=out/"extracted_evidence.csv"
 with staging.open("w",encoding="utf-8-sig",newline="") as f:
  w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
 conn=sqlite3.connect(str(db))
 try:
  stats=stage(conn,staging);profit_review(conn,out)
 finally:conn.close()
 result=export(db,out)
 report={"pages":pages,"parsed_size_rows":len(rows),"stage":stats,"products":result["products"],"woo_rows":result["woocommerce_rows"],"buyma_rows":result["buyma_rows"],"published":0,"approved_for_import":False}
 (out/"end_to_end_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
 return report
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--manifest",required=True);p.add_argument("--db",required=True);p.add_argument("--out",required=True);a=p.parse_args()
 print(json.dumps(run(a.manifest,a.db,a.out),ensure_ascii=False))

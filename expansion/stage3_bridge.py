"""Bridge expansion to the validated stage3 collector. Review only."""
import argparse,csv,json,sqlite3,re,sys
from pathlib import Path
from urllib.parse import urlsplit

HOSTS={"www.bstn.com","www.notre-shop.com","patta.nl"}
ALIASES={"bstn.com":"www.bstn.com","notre-shop.com":"www.notre-shop.com","www.patta.nl":"patta.nl"}
def host(url):
    p=urlsplit(url)
    if p.scheme!="https" or p.netloc not in HOSTS|set(ALIASES) or p.query or p.fragment:
        raise ValueError("unapproved product URL")
    return ALIASES.get(p.netloc,p.netloc)

def offline(manifests,db,out):
    from stage3_catalog import init,prepare,process,extract,report
    groups={}
    for manifest in manifests:
        manifest=Path(manifest).resolve()
        with manifest.open(encoding="utf-8-sig",newline="") as f:
            for row in csv.DictReader(f):
                url=row["product_url"]; h=host(url)
                p=(manifest.parent/row["html_file"]).resolve()
                if manifest.parent not in p.parents:raise ValueError("outside manifest")
                g=groups.setdefault(h,{})
                raw=p.read_bytes()
                if url in g and g[url]!=raw:raise ValueError("conflicting snapshot")
                g[url]=raw
    if set(groups)!=HOSTS or any(len(g)!=2 for g in groups.values()):
        raise ValueError("expected two distinct pages per host")
    out=Path(out);out.mkdir()
    results={}
    with sqlite3.connect(db) as c:
        init(c)
        for h,g in sorted(groups.items()):
            cfg=dict(host=h,product_path_regex="offline exact manifest",sitemap_seeds=["offline"])
            run="offline:"+h
            prepare(c,run,cfg,sorted(g))
            dest=out/h;dest.mkdir()
            try:
                process(c,run,g.__getitem__,extract,len(g))
            finally:
                results[h]=report(c,run,dest)
        counts={h:results[h]["rows"] for h in results}
        expected={"www.bstn.com":14,"www.notre-shop.com":26,"patta.nl":12}
        passed=counts==expected and all(r["complete"] and not r["published"] and not r["approved_for_import"] for r in results.values())
        summary=dict(passed=passed,counts=counts,results=results,published=0,approved_for_import=False)
        (out/"acceptance.json").write_text(json.dumps(summary,indent=2))
        if not passed:raise ValueError("six-page acceptance failed")
    return summary

def live(config,db,out,run,limit):
    from stage3_catalog import policy,Fetch,init,prepare,process,extract,report,scope
    cfg=json.loads(Path(config).read_text())
    policy(cfg)
    if cfg["host"] not in HOSTS or not 1<=limit<=5 or cfg["request_budget"]>10:
        raise ValueError("pilot scope/budget")
    if cfg.get("listing_seeds") or not cfg.get("pilot_product_urls"):
        raise ValueError("pilot requires explicit product URLs and sitemap policy")
    urls=sorted(set(cfg["pilot_product_urls"]))
    if len(urls)!=limit:raise ValueError("pilot URL count must equal limit")
    for u in urls:
        scope(u,cfg["host"])
        if not re.fullmatch(cfg["product_path_regex"],urlsplit(u).path):raise ValueError("product path outside scope")
    out=Path(out);out.mkdir()
    # One fresh DB per pilot; never retry an ambiguous network attempt.
    with Path(db).open("xb"):pass
    with sqlite3.connect(db) as c:
        init(c);prepare(c,run,cfg,urls)
        f=Fetch(cfg)
        try:
            f.init_robots()
            process(c,run,f,extract,limit)
        finally:
            result=report(c,run,out)
            result["requests"]=f.n
            (out/"pilot.json").write_text(json.dumps(result,indent=2))
        if not result["complete"]:raise ValueError("pilot incomplete")
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--package",required=True)
    p.add_argument("--db",required=True);p.add_argument("--out",required=True)
    p.add_argument("--manifest",action="append");p.add_argument("--config")
    p.add_argument("--run",default="pilot");p.add_argument("--limit",type=int,default=1)
    a=p.parse_args()
    sys.path.insert(0,str(Path(a.package).resolve()))
    if bool(a.manifest)==bool(a.config):p.error("choose offline manifests or live config")
    print(json.dumps(offline(a.manifest,a.db,a.out) if a.manifest else live(a.config,a.db,a.out,a.run,a.limit)))
if __name__=="__main__":main()

"""Bounded candidate probe; never represents full catalog coverage."""
import argparse,json,sqlite3,hashlib
from pathlib import Path
from urllib.parse import urlsplit
from stage3_catalog import (Fetch,policy,listing_page,listing_hits,init,prepare,
                            process,extract,report,utc,require)

def probe(cfg,fetch,max_pages):
    require(type(max_pages) is int and 1<=max_pages<=5,'invalid probe bound')
    require(len(cfg.get('listing_seeds',[]))==1,'probe requires one seed')
    seed=cfg['listing_seeds'][0]
    seen=set(); products=set(); excluded=set(); evidence=[]
    for page in range(1,max_pages+1):
        url=listing_page(seed,page)
        raw=fetch.listing(url)
        urls,total,pages=listing_hits(raw,page)
        overlap=sorted(seen.intersection(urls))
        evidence.append(dict(url=url,page=page,total=total,pages=pages,
                             overlap=overlap,urls=urls,sha256=hashlib.sha256(raw).hexdigest(),at=utc()))
        seen.update(urls)
        for u in urls:
            if urlsplit(u).path.startswith('/eu_en/r/'):
                excluded.add(u)
            else:
                import re
                require(re.fullmatch(cfg['product_path_regex'],urlsplit(u).path),'product outside configured scope')
                products.add(u)
        if page>=pages:break
    require(products,'no matching products')
    return sorted(products),dict(coverage='PARTIAL',catalog_complete=False,
        pages=evidence,unique_candidates=len(products),excluded_release=len(excluded),
        drift=any(e['overlap'] or (e['total'],e['pages'])!=(evidence[0]['total'],evidence[0]['pages']) for e in evidence))

def main():
    p=argparse.ArgumentParser()
    for k in ('config','db','run','out'):p.add_argument('--'+k,required=True)
    p.add_argument('--pages',type=int,default=2)
    a=p.parse_args()
    cfg=json.loads(Path(a.config).read_text());policy(cfg)
    require(1<=a.pages<=5,'invalid probe bound')
    require(not Path(a.db).exists(),'probe requires separate fresh DB')
    out=Path(a.out);out.mkdir()
    f=Fetch(cfg);f.init_robots()
    urls,evidence=probe(cfg,f,a.pages)
    (out/'discovery.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
    selected=urls[:5];require(len(selected)==5,'fewer than five candidates')
    with sqlite3.connect(a.db) as c:
        init(c);prepare(c,a.run,cfg,selected)
        try:process(c,a.run,f,extract,5)
        finally:
            result=report(c,a.run,out)
            result.update(catalog_complete=False,coverage='PARTIAL',trial=True)
            (out/'report.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
            print(json.dumps(result))
if __name__=='__main__':main()

"""§27 bounded persistent discovery; no publication. One campaign per DB."""
import argparse, hashlib, json, sqlite3, time, re
from pathlib import Path
from urllib.parse import urlsplit
from stage3_catalog import Fetch, policy, listing_page, listing_hits, listing_scope, scope, require, utc, init, prepare, process, extract, report

def setup(c,cfg,cap):
    policy(cfg)
    require(cfg['host']=='www.bstn.com' and len(cfg.get('listing_seeds',[]))==1,'BSTN single seed only')
    require(type(cap) is int and 1<=cap<=10000,'invalid campaign cap')
    sig=json.dumps([cfg['host'],cfg['listing_seeds'],cfg['product_path_regex'],cap],sort_keys=True)
    c.executescript("""CREATE TABLE IF NOT EXISTS campaign(sig TEXT PRIMARY KEY);
    CREATE TABLE IF NOT EXISTS ledger(id INTEGER PRIMARY KEY, url TEXT, kind TEXT, at REAL, status TEXT, raw BLOB, captured_at TEXT);
    CREATE TABLE IF NOT EXISTS pages(id TEXT PRIMARY KEY, seed TEXT, page INTEGER, at TEXT, sha TEXT, raw BLOB, total INTEGER, pages INTEGER, urls TEXT, releases TEXT, overlap TEXT, drift INTEGER);
    CREATE TABLE IF NOT EXISTS candidates(url TEXT PRIMARY KEY, first_seen TEXT,last_seen TEXT);
    CREATE TABLE IF NOT EXISTS sightings(capture TEXT,url TEXT,PRIMARY KEY(capture,url));
    """)
    init(c)
    with c:
        old=c.execute('SELECT sig FROM campaign').fetchall()
        require(not old or old==[(sig,)],'campaign scope/cap changed')
        c.execute('INSERT OR IGNORE INTO campaign VALUES(?)',(sig,))

class PersistentFetch(Fetch):
    def __init__(self,cfg,c,cap):
        super().__init__(dict(cfg));self.c=c;self.cap=cap
    def read(self,url,kind):
        # Reserve durably before network; unresolved or failed attempts stop campaign.
        c=self.c
        c.execute('BEGIN IMMEDIATE')
        try:
            require(not c.execute("SELECT 1 FROM ledger WHERE status!='OK'").fetchone(),'unresolved/failed request: review required')
            n,last=c.execute('SELECT count(*),max(at) FROM ledger').fetchone()
            require(n<self.cap and self.n<self.cfg['request_budget'],'request budget reached')
            time.sleep(max(0,self.cfg['interval_seconds']-(time.time()-(last or 0))))
            i=c.execute("INSERT INTO ledger(url,kind,at,status) VALUES(?,?,?,'PENDING')",(url,kind,time.time())).lastrowid
            c.commit()
        except BaseException:
            c.rollback();raise
        try:
            raw=super().read(url,kind)
        except BaseException:
            with c:c.execute("UPDATE ledger SET status='FAILED' WHERE id=?",(i,))
            raise
        with c:c.execute("UPDATE ledger SET status='OK',raw=?,captured_at=? WHERE id=?",(raw,utc(),i))
        return raw

def capture(c,cfg,page,raw,at):
    seed=cfg['listing_seeds'][0]
    listing_scope(listing_page(seed,page),cfg['host'])
    urls,total,pages=listing_hits(raw,page)
    releases=[];products=[]
    for u in urls:
        scope(u,cfg['host'])
        if urlsplit(u).path.startswith('/eu_en/r/'):releases.append(u)
        else:
            require(re.fullmatch(cfg['product_path_regex'],urlsplit(u).path),'product outside scope')
            products.append(u)
    sha=hashlib.sha256(raw).hexdigest()
    key=hashlib.sha256(json.dumps([seed,page,at,sha]).encode()).hexdigest()
    with c:
        if c.execute('SELECT 1 FROM pages WHERE id=?',(key,)).fetchone():return key
        prior=c.execute('SELECT page,total,pages,urls FROM pages WHERE seed=?',(seed,)).fetchall()
        seen={u for p,_,__,s in prior if p!=page for u in json.loads(s)}
        overlap=sorted(seen.intersection(urls))
        drift=bool(overlap or any((n,k)!=(total,pages) for _,n,k,_ in prior))
        c.execute('INSERT INTO pages VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(key,seed,page,at,sha,raw,total,pages,json.dumps(urls),json.dumps(releases),json.dumps(overlap),int(drift)))
        for u in products:
            c.execute('INSERT INTO candidates VALUES(?,?,?) ON CONFLICT(url) DO UPDATE SET first_seen=min(first_seen,excluded.first_seen),last_seen=max(last_seen,excluded.last_seen)',(u,at,at))
            c.execute('INSERT INTO sightings VALUES(?,?)',(key,u))
    return key

def summary(c):
    return dict(coverage='PARTIAL',catalog_complete=False,unique_candidates=c.execute('SELECT count(*) FROM candidates').fetchone()[0],captures=c.execute('SELECT count(*) FROM pages').fetchone()[0],drift=bool(c.execute('SELECT 1 FROM pages WHERE drift=1').fetchone()),requests=dict(c.execute('SELECT status,count(*) FROM ledger GROUP BY status')),published=0,approved_for_import=False)

def main():
    p=argparse.ArgumentParser()
    for k in ('config','db','out'):p.add_argument('--'+k,required=True)
    p.add_argument('--cap',type=int,required=True)
    p.add_argument('--start',type=int,required=True)
    p.add_argument('--end',type=int,required=True)
    p.add_argument('--detail-run')
    p.add_argument('--detail-limit',type=int,default=0)
    a=p.parse_args()
    require(1<=a.start<=a.end<=9999 and a.end-a.start<5,'invalid bounded range')
    require(0<=a.detail_limit<=5 and bool(a.detail_run)==bool(a.detail_limit),'invalid detail request')
    cfg=json.loads(Path(a.config).read_text());policy(cfg)
    out=Path(a.out);out.mkdir()
    with sqlite3.connect(a.db) as c:
        setup(c,cfg,a.cap)
        f=PersistentFetch(cfg,c,a.cap)
        try:
            f.init_robots()
            for page in range(a.start,a.end+1):
                if c.execute('SELECT 1 FROM pages WHERE seed=? AND page=?',(cfg['listing_seeds'][0],page)).fetchone():continue
                url=listing_page(cfg['listing_seeds'][0],page)
                saved=c.execute("SELECT raw,captured_at FROM ledger WHERE url=? AND kind='listing' AND status='OK' ORDER BY id DESC LIMIT 1",(url,)).fetchone()
                if not saved:
                    f.listing(url)
                    saved=c.execute("SELECT raw,captured_at FROM ledger WHERE url=? AND kind='listing' AND status='OK' ORDER BY id DESC LIMIT 1",(url,)).fetchone()
                capture(c,cfg,page,*saved)
            if a.detail_run:
                old=c.execute('SELECT url,state FROM queue WHERE run=? ORDER BY url',(a.detail_run,)).fetchall()
                require(not any(s=='ERROR' for _,s in old),'detail error requires review')
                urls=[u for u,_ in old] or [u for (u,) in c.execute('SELECT url FROM candidates ORDER BY url LIMIT ?',(a.detail_limit,))]
                require(urls,'no candidates')
                prepare(c,a.detail_run,cfg,urls)
                process(c,a.detail_run,f,extract,a.detail_limit)
                result=report(c,a.detail_run,out)
                result.pop('delta',None)
                result.update(catalog_complete=False,coverage='PARTIAL',detail_queue_complete=result['complete'])
                (out/'report.json').write_text(json.dumps(result,indent=2))
        finally:
            (out/'discovery.json').write_text(json.dumps(summary(c),indent=2))
if __name__=='__main__':main()

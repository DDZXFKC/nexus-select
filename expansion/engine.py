"""Offline expansion runner. No network or production writes."""
import argparse, json, sqlite3
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, urljoin

def canonical(url, host):
    p = urlsplit(url)
    if p.scheme != "https" or p.netloc.lower() != host.lower() or p.username or p.password:
        raise ValueError("outside approved origin")
    return urlunsplit(("https", host.lower(), p.path or "/", p.query, ""))

class ShopifyAdapter:
    def discover(self, snapshot):
        return snapshot["urls"]
    def parse(self, snapshot):
        p = snapshot["product"]
        rows = []
        for v in p["variants"]:
            rows.append(dict(product_id=str(p["id"]), variant_id=str(v["id"]),
                brand=p["vendor"], title=p["title"], size=v["size"],
                price=str(v["price"]), currency=snapshot["currency"],
                available=v["available"], images=p.get("images", [])))
        return rows

class Engine:
    def __init__(self, db, sites):
        self.db = sqlite3.connect(db)
        self.sites = sites
        self.adapters = {"shopify_fixture": ShopifyAdapter()}
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS queue(site TEXT,url TEXT,state TEXT DEFAULT 'pending',
          error TEXT, PRIMARY KEY(site,url));
        CREATE TABLE IF NOT EXISTS variants(site TEXT,url TEXT,variant TEXT,payload TEXT,
          PRIMARY KEY(site,url,variant));
        """)
    def site(self, key):
        s = self.sites[key]
        if not s.get("enabled") or not s.get("policy_review"):
            raise ValueError("site disabled")
        return s
    def discover(self, key, snapshot):
        s = self.site(key)
        urls = [canonical(u,s["host"]) for u in self.adapters[s["adapter"]].discover(snapshot)]
        with self.db:
            self.db.executemany("INSERT OR IGNORE INTO queue(site,url) VALUES (?,?)", [(key,u) for u in urls])
    def run(self, key, snapshots):
        from decimal import Decimal
        s = self.site(key)
        pending = self.db.execute("SELECT url FROM queue WHERE site=? AND state='pending' ORDER BY url",(key,)).fetchall()
        for (url,) in pending:
            if url not in snapshots:
                continue
            try:
                rows = self.adapters[s["adapter"]].parse(snapshots[url])
                if not rows or len({r["variant_id"] for r in rows}) != len(rows):
                    raise ValueError("empty or duplicate variants")
                for r in rows:
                    if any(not str(r.get(k) or "").strip() for k in ("product_id","variant_id","brand","title","size","currency","price")):
                        raise ValueError("missing required field")
                    if type(r["available"]) is not bool or r["currency"] != s["currency"]:
                        raise ValueError("invalid availability/currency")
                    amount = Decimal(r["price"])
                    if not amount.is_finite() or amount <= 0:
                        raise ValueError("invalid price")
                    r.update(source_url=url, status="HOLD", approved_for_import=False)
                with self.db:
                    self.db.executemany("INSERT OR REPLACE INTO variants VALUES (?,?,?,?)",[(key,url,r["variant_id"],json.dumps(r,ensure_ascii=False)) for r in rows])
                    self.db.execute("UPDATE queue SET state='done',error=NULL WHERE site=? AND url=?",(key,url))
            except (ValueError, KeyError, TypeError, ArithmeticError) as e:
                with self.db:
                    self.db.execute("UPDATE queue SET state='hold',error=? WHERE site=? AND url=?",(str(e),key,url))
    def export(self):
        return [json.loads(r[0]) for r in self.db.execute("SELECT payload FROM variants ORDER BY site,url,variant")]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--fixture",required=True)
    p.add_argument("--db",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    data=json.loads(Path(a.fixture).read_text())
    e=Engine(a.db,data["sites"])
    for key, batch in data["batches"].items():
        e.discover(key,batch)
        e.run(key,batch["snapshots"])
    Path(a.output).write_text(json.dumps(e.export(),ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()

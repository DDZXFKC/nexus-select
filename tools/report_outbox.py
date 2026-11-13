#!/usr/bin/env python3
"""Local report outbox. No network, credentials or approval automation."""
import argparse, hashlib, json, os, shutil, tempfile
from pathlib import Path
from datetime import datetime, timezone

def digest(b): return hashlib.sha256(b).hexdigest()
def atomic(p,b):
    p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=p.parent)
    try:
        with os.fdopen(fd,"wb") as f:
            f.write(b); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,p)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
def enqueue(root,source):
    source=Path(source)
    if source.suffix.lower() not in (".md",".json",".txt"): raise ValueError("report files only")
    b=source.read_bytes()
    key=digest(source.name.encode()+b"\0"+b)
    dest=root/"pending"/key
    if (root/"sent"/key).exists(): return key
    atomic(dest/source.name,b)
    atomic(dest/"entry.json",json.dumps({"id":key,"name":source.name,"sha256":digest(b),"created":datetime.now(timezone.utc).isoformat()}).encode())
    return key
def batch(root,out):
    out.mkdir(parents=True,exist_ok=False)
    entries=[]
    for p in sorted((root/"pending").glob("*/entry.json")):
        e=json.loads(p.read_text()); b=(p.parent/e["name"]).read_bytes()
        if digest(b)!=e["sha256"]: raise ValueError("corrupt report")
        name=e["id"][:16]+"-"+e["name"]
        atomic(out/name,b); entries.append(dict(e,batch_file=name))
    atomic(out/"manifest.json",json.dumps(entries,indent=2).encode())
    return entries
def ack(root,manifest,commit):
    import re
    if not re.fullmatch("[0-9a-f]{40}",commit): raise ValueError("verified commit SHA required")
    for e in json.loads(Path(manifest).read_text()):
        p=root/"pending"/e["id"]
        if not p.exists(): continue
        if digest((p/e["name"]).read_bytes())!=e["sha256"]: raise ValueError("changed report")
        atomic(p/"receipt.json",json.dumps({"commit":commit}).encode())
        dest=root/"sent"/e["id"]; dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists(): raise ValueError("receipt collision")
        p.rename(dest)
def main():
    p=argparse.ArgumentParser();p.add_argument("--root",default="~/.nexus-report-outbox")
    s=p.add_subparsers(dest="cmd",required=True)
    q=s.add_parser("enqueue");q.add_argument("files",nargs="+")
    q=s.add_parser("batch");q.add_argument("out")
    q=s.add_parser("ack");q.add_argument("manifest");q.add_argument("commit")
    s.add_parser("status")
    a=p.parse_args();root=Path(a.root).expanduser()
    if a.cmd=="enqueue":
        for f in a.files: print(enqueue(root,f))
    elif a.cmd=="batch": print(len(batch(root,Path(a.out))))
    elif a.cmd=="ack": ack(root,a.manifest,a.commit)
    else: print(json.dumps({k:len(list((root/k).glob("*/entry.json"))) for k in ("pending","sent")}))
if __name__=="__main__":main()

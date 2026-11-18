#!/usr/bin/env python3
"""Offline shared color-name resolver. Writes candidates only; no sheet mutations."""
import argparse
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from urllib.request import urlopen
import hashlib

REV = "4e9d724b03a4c8334933a312958f370d187317c4"
ROOT = f"https://raw.githubusercontent.com/meodai/color-names/{REV}/"
BASE = {"black":"#171717","white":"#FFFFFF","gray":"#999999","grey":"#999999","red":"#C62828","blue":"#2864A0","navy":"#172B4D","green":"#40734C","olive":"#73784B","yellow":"#E6C53B","orange":"#D97732","purple":"#80559C","pink":"#E5A0B5","brown":"#795548","beige":"#D8C6A6","cream":"#F1E8D4","tan":"#C49A6C","gold":"#C6A34A","silver":"#BFC2C5","khaki":"#B4A482","burgundy":"#6B2535","maroon":"#713642","teal":"#287F82","ivory":"#F3EBDD","cyan":"#00FFFF","aqua":"#00FFFF","magenta":"#FF00FF"}
BLOCKED = set(["multi","multicolor","multi color","multi-color","nocolor","no color","assorted","clear","transparent","none","unknown"])
HEX = re.compile(r"#[0-9a-fA-F]{6}\Z")

def norm(value):
    return " ".join(unicodedata.normalize("NFKC", value or "").casefold().split())

def valid(value):
    return bool(HEX.fullmatch(value or ""))

def cache_source(cache):
    cache.mkdir(parents=True, exist_ok=True)
    for remote, local in (("src/colornames.csv", "colornames.csv"), ("LICENSE", "LICENSE")):
        path = cache / local
        if not path.exists():
            with urlopen(ROOT + remote, timeout=60) as response:
                data = response.read(5_000_001)
            if len(data) > 5_000_000:
                raise ValueError("source too large")
            tmp = path.with_suffix(".tmp")
            tmp.write_bytes(data)
            tmp.replace(path)
    metadata = {"revision": REV, "source": ROOT, "sha256": {
        name: hashlib.sha256((cache / name).read_bytes()).hexdigest()
        for name in ("colornames.csv", "LICENSE")}}
    manifest = cache / "manifest.json"
    if manifest.exists() and json.loads(manifest.read_text()) != metadata:
        raise ValueError("cache changed; use a new verified cache")
    manifest.write_text(json.dumps(metadata, indent=2) + "\n")
    return cache / "colornames.csv"

def read_dictionary(path):
    result = defaultdict(set)
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            key, value = norm(row["name"]), row["hex"]
            if key and valid(value):
                result[key].add(value.upper())
    if not result:
        raise ValueError("empty dictionary")
    return result

def read_palette(path):
    return {norm(k): v.upper() for k, v in json.loads(path.read_text()).items() if valid(v)}

def resolve(token, existing, palette, dictionary):
    key = norm(token)
    if key in BLOCKED or not key:
        return "", "SPECIAL"
    if valid(existing):
        return existing.upper(), "EXISTING"
    if key in palette:
        return palette[key], "PALETTE_EXACT"
    hits = dictionary.get(key, set())
    if len(hits) == 1:
        return next(iter(hits)), "DICTIONARY_EXACT"
    if len(hits) > 1:
        return "", "DICTIONARY_CONFLICT"
    hits = {BASE[word] for word in re.split(r"[\s-]+", key) if word in BASE}
    if len(hits) == 1:
        return next(iter(hits)), "BASIC_WORD"
    return "", "AMBIGUOUS_BASIC" if hits else "UNKNOWN"

def run(master, dictionary, palette, output):
    with master.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    seen = set()
    counts = Counter()
    output_rows = []
    for row in rows:
        key = norm(row["token_normalized"])
        if not key or key in seen:
            raise ValueError(f"duplicate or empty shared token: {key}")
        seen.add(key)
        value, method = resolve(key, row.get("display_hex", ""), palette, dictionary)
        counts[method] += 1
        output_rows.append({"color_id": row["color_id"], "token_normalized": key,
                            "candidate_hex": value, "method": method})
    if master.resolve() == output.resolve():
        raise ValueError("refusing to overwrite input")
    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["color_id", "token_normalized", "candidate_hex", "method"])
        writer.writeheader()
        writer.writerows(output_rows)
    return dict(sorted(counts.items()))

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--master", type=Path, required=True)
    p.add_argument("--palette", type=Path, required=True)
    p.add_argument("--cache", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--dictionary", type=Path, help="local already verified CSV instead of download")
    args = p.parse_args()
    dictionary = read_dictionary(args.dictionary or cache_source(args.cache))
    print(json.dumps(run(args.master, dictionary, read_palette(args.palette), args.output), ensure_ascii=False))

if __name__ == "__main__":
    main()

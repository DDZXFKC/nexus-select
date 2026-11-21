#!/usr/bin/env python3
"""Build or upload the inert XServer/SFTP handoff (no activation, no passwords).
Reads AHC_SFTP_HOST, AHC_SFTP_USER, AHC_SFTP_KEY, AHC_REMOTE_MUPLUGINS
from the operator's iMac environment, never from GitHub. Port fixed at 10022.
Does not modify wp-config, plugins or product data, and never executes PHP.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "tools/ahc-stock-inline-endpoints-staging.php",
    "tools/ahc-stock-sp158-owner-bridge-staging.php",
    "tools/ahc-stock-sp158-cost-coverage-provider.php",
    "tools/ahc-stock-sp-live-adapter-staging.php",
    "tools/ahc-sp158-staging-loader.php",
    "tools/ahc_fl_cowprint_wpcli.php",
    "local-snapshot-2026-11-15/mu-plugins/ahc-stock-check-ui.php",
    "local-snapshot-2026-11-15/mu-plugins/ahc-stock-check-ui.js",
    "data/xserver-export/sp158-live-sku-match-2026-11-22.csv",
    "data/images/footlocker/IO0442-200/O0442200_01-white-square.png",
    "data/images/footlocker/IO0442-200/O0442200_03-white-square.png",
    "data/images/footlocker/IO0442-200/O0442200_04-white-square.png",
    "data/images/footlocker/IO0442-200/provenance.json",
]
DEST = "ahc-staging-handoff-2026-11-22"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(out):
    out.mkdir(parents=True, exist_ok=True)
    manifest = []
    for relative in FILES:
        source = ROOT / relative
        if not source.is_file():
            raise FileNotFoundError(f"Required verified repo file missing: {relative}")
        destination = out / source.name
        if destination.exists():
            raise RuntimeError(f"Output collision: {destination}")
        shutil.copyfile(source, destination)
        manifest.append({
            "repository_path": relative,
            "staged_name": source.name,
            "size": destination.stat().st_size,
            "sha256": digest(destination),
        })
    (out / "manifest.json").write_text(
        json.dumps({"status": "INERT_UPLOAD_ONLY", "site": "AFTER HOURS CLUB",
                    "port": 10022, "files": manifest}, indent=2) + "\n",
        encoding="utf-8")
    return manifest


def sftp_batch(commands, host, user, key):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sftp", delete=False) as f:
        f.write("\n".join(commands) + "\n")
        batch = f.name
    try:
        subprocess.run(["sftp", "-oBatchMode=yes", "-oStrictHostKeyChecking=yes",
                        "-oConnectTimeout=15", "-P", "10022", "-i", key, "-b",
                        batch, f"{user}@{host}"], check=True, timeout=180)
    finally:
        os.unlink(batch)


def upload(out, manifest):
    host, user, key, remote_root = (
        os.environ.get("AHC_SFTP_HOST", ""),
        os.environ.get("AHC_SFTP_USER", ""),
        os.environ.get("AHC_SFTP_KEY", ""),
        os.environ.get("AHC_REMOTE_MUPLUGINS", ""),
    )
    # Do not interpolate shell metacharacters in batch commands or expose secrets.
    if not host or not user or not re.fullmatch(r"[A-Za-z0-9.-]+", host) or \
       not re.fullmatch(r"[A-Za-z0-9_.-]+", user) or \
       not remote_root.startswith("/") or \
       not re.fullmatch(r"[/A-Za-z0-9_.-]+", remote_root) or \
       not Path(key).is_file():
        raise RuntimeError("Valid iMac SFTP host/user/key and absolute MU-plugin folder required")
    remote = remote_root.rstrip("/") + "/" + DEST
    cmds = [f"-mkdir {remote}"]
    for item in manifest:
        cmds.append(f"put {out / item['staged_name']} {remote}/{item['staged_name']}")
    cmds.append(f"put {out / 'manifest.json'} {remote}/manifest.json")
    sftp_batch(cmds, host, user, key)
    # Read back everything to prove full upload, not just an exit code.
    with tempfile.TemporaryDirectory() as verified:
        getcmd = [
            f"get {remote}/{item['staged_name']} {Path(verified) / item['staged_name']}"
            for item in manifest
        ]
        getcmd.append(f"get {remote}/manifest.json {Path(verified) / 'manifest.json'}")
        sftp_batch(getcmd, host, user, key)
        for item in manifest:
            if digest(Path(verified) / item["staged_name"]) != item["sha256"]:
                raise RuntimeError(f"SFTP readback mismatch {item['staged_name']}")
        if digest(Path(verified) / "manifest.json") != digest(out / "manifest.json"):
            raise RuntimeError("SFTP manifest readback mismatch")
    print("SFTP_UPLOAD_READBACK_PASS")
    print("STAGING_INERT_ONLY — old plugins were not disabled; no API activated")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--upload", action="store_true")
    args = p.parse_args()
    manifest = build(args.output)
    print("BUNDLE_PREPARED", len(manifest))
    if args.upload:
        upload(args.output, manifest)


if __name__ == "__main__":
    main()

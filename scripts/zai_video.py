#!/usr/bin/env python3
"""Z.ai CogVideoX-3 video generation helper.

Usage:
  zai_video.py generate --prompt "..." [--image /path/to/first-frame.jpg]
                        [--size 720x1280] [--duration 10] [--fps 30]
                        [--out /path/to/output.mp4]
Submits an async generation task, polls until done, downloads the MP4.
The API key is injected by the Muse credential surrogate; never handled here.
"""
import argparse, base64, json, sys, time, urllib.request, urllib.error
sys.path.insert(0, "/opt/muse/skills/custom-connector-setup/bin")
from dynamic_credentials import add_surrogate_to_request, read_json_response

BASE = "https://api.z.ai/api/paas/v4"
HOSTS = ["api.z.ai"]

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        raise RuntimeError("redirect refused, verify the endpoint")

def call(method, url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    add_surrogate_to_request(req, "custom.z-ai", allowed_hosts=HOSTS)
    try:
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=60) as resp:
            return resp.status, read_json_response(resp)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        return e.code, {"http_error_body": body}

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate")
    g.add_argument("--prompt", required=True)
    g.add_argument("--image", default=None, help="first-frame image path (jpg/png/webp)")
    g.add_argument("--size", default="720x1280")
    g.add_argument("--duration", type=int, default=10)
    g.add_argument("--fps", type=int, default=30)
    g.add_argument("--quality", default="quality")
    g.add_argument("--out", required=True)
    g.add_argument("--poll-seconds", type=int, default=20)
    g.add_argument("--max-polls", type=int, default=45)
    f = sub.add_parser("fetch")
    f.add_argument("--task-id", required=True)
    f.add_argument("--out", required=True)
    args = ap.parse_args()

    if args.cmd == "fetch":
        s2, r2 = call("GET", f"{BASE}/async-result/{args.task_id}")
        print("fetch_status:", s2, "task_status:", r2.get("task_status"))
        results = r2.get("video_result") or []
        if not results:
            print("NO_VIDEO_RESULT", json.dumps(r2)[:600]); return 1
        url = results[0]["url"]
        # Chunked download with per-chunk Range requests (CDN drops long reads).
        CHUNK = 512 * 1024
        blob = bytearray()
        while True:
            start = len(blob)
            end = start + CHUNK - 1
            ok = False
            for attempt in range(6):
                try:
                    req = urllib.request.Request(url)
                    req.add_header("Range", f"bytes={start}-{end}")
                    with urllib.request.build_opener(NoRedirect()).open(req, timeout=120) as r:
                        part = r.read()
                        total = None
                        cr = r.headers.get("Content-Range")
                        if cr and "/" in cr:
                            total = int(cr.rsplit("/", 1)[1])
                    blob.extend(part)
                    ok = True
                    break
                except Exception as e:
                    print(f"chunk @{start} attempt {attempt+1} failed: {e}")
                    time.sleep(3)
            if not ok:
                print("DOWNLOAD_FAILED at", start); return 1
            if total is not None and len(blob) >= total:
                break
            if len(part) < CHUNK:
                break
        with open(args.out, "wb") as fh:
            fh.write(bytes(blob))
        print("DOWNLOADED:", args.out, len(blob), "bytes")
        return 0

    payload = {
        "model": "cogvideox-3",
        "prompt": args.prompt,
        "size": args.size,
        "duration": args.duration,
        "fps": args.fps,
        "quality": args.quality,
        "with_audio": False,
    }
    if args.image:
        with open(args.image, "rb") as f:
            payload["image_url"] = base64.b64encode(f.read()).decode()

    status, resp = call("POST", f"{BASE}/videos/generations", payload)
    print("submit_status:", status)
    print("submit_resp:", json.dumps(resp)[:600])
    if status != 200 or not resp.get("id"):
        print("GENERATION_SUBMIT_FAILED")
        return 1
    task_id = resp["id"]

    for i in range(args.max_polls):
        time.sleep(args.poll_seconds)
        s2, r2 = call("GET", f"{BASE}/async-result/{task_id}")
        ts = r2.get("task_status")
        print(f"poll {i+1}: http={s2} task_status={ts}")
        if ts == "SUCCESS":
            results = r2.get("video_result") or []
            if not results:
                print("NO_VIDEO_RESULT", json.dumps(r2)[:600]); return 1
            url = results[0]["url"]
            req = urllib.request.Request(url)
            with urllib.request.build_opener(NoRedirect()).open(req, timeout=300) as r:
                blob = r.read()
            with open(args.out, "wb") as f:
                f.write(blob)
            print("DOWNLOADED:", args.out, len(blob), "bytes")
            print("cover:", results[0].get("cover_image_url"))
            return 0
        if ts in ("FAIL", "FAILED"):
            print("TASK_FAILED", json.dumps(r2)[:600]); return 1
    print("POLL_TIMEOUT")
    return 1

if __name__ == "__main__":
    sys.exit(main())

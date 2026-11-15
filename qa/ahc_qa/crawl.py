"""Same-site crawler: links, HTTP status, redirects, titles, brand-name residue,
image display/decoding, and owner-invariant checks on the rendered HTML.

Standard library only (Pillow is optional, for image decode verification).
Read-only: performs GET/HEAD requests only, never submits forms.
"""
from __future__ import annotations

import base64
import io
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from html.parser import HTMLParser

from .findings import Finding

try:
    from PIL import Image  # type: ignore
except Exception:  # pragma: no cover
    Image = None

UA = "AHC-QA/1.0 (+read-only quality inspection)"
ALL_GROUP_LINK = re.compile(r"^ALL (?:(?:MEN'S|WOMEN'S|KIDS|MENS|WOMENS) )?(?:SHOES|CLOTHING|HEADWEAR|ACCESSORIES)(?: ITEMS)?$")
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class PageParser(HTMLParser):
    """Collects links, images, title, visible text and a light element tree for invariant checks."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []  # (href, anchor-location)
        self.link_texts: list[str] = []  # visible text of each link, parallel to self.links
        self._a_idx = None
        self.images: list[tuple[str, str]] = []  # (src, alt)
        self.title = ""
        self._in_title = False
        self._skip = 0  # inside script/style
        self.text: list[str] = []
        self.attr_text: list[tuple[str, str]] = []  # (where, value) for alt/title/meta content
        self.stack: list[tuple[str, set]] = []  # open elements: (tag, classes)
        self.elements: list[dict] = []  # flat list of elements with ancestor classes

    def _ancestor_classes(self) -> set:
        s = set()
        for _, cl in self.stack:
            s |= cl
        return s

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = set((a.get("class") or "").split())
        anc = self._ancestor_classes()
        self.elements.append({"tag": tag, "classes": classes, "ancestors": anc, "attrs": a})
        if tag in ("script", "style", "noscript", "template"):
            self._skip += 1
        if tag == "title":
            self._in_title = True
        if tag == "a" and a.get("href"):
            self.links.append((a["href"], " ".join(sorted(anc | classes))[:120]))
            self.link_texts.append("")
            self._a_idx = len(self.links) - 1
        if tag == "img":
            src = a.get("src") or a.get("data-src") or ""
            if src:
                self.images.append((src, a.get("alt") or ""))
            for cand in (a.get("srcset") or "").split(","):
                u = cand.strip().split(" ")[0]
                if u:
                    self.images.append((u, a.get("alt") or ""))
            if a.get("alt"):
                self.attr_text.append(("img alt", a["alt"]))
        if tag == "meta" and a.get("content") and (a.get("property", "").startswith("og:") or a.get("name") in ("description", "twitter:title", "twitter:description", "application-name")):
            self.attr_text.append((f"meta {a.get('property') or a.get('name')}", a["content"]))
        if tag in ("a", "button", "img", "input") and a.get("aria-label"):
            self.attr_text.append((f"{tag} aria-label", a["aria-label"]))
        if tag not in VOID:
            self.stack.append((tag, classes))

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "template") and self._skip:
            self._skip -= 1
        if tag == "title":
            self._in_title = False
        if tag == "a":
            self._a_idx = None
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if self._a_idx is not None and not self._skip:
            self.link_texts[self._a_idx] += data
        if self._in_title:
            self.title += data
        elif not self._skip and data.strip():
            self.text.append(data.strip())


# Findings that come from a shared template (header/footer/title) are reported once with a page count.
AGGREGATE_TYPES = {"BRAND_RESIDUE", "INV_EMPTY_CATEGORY_HIDDEN", "INV_NO_HEADER_DROPDOWN", "INV_NO_ALL_GROUP_LINK"}


def aggregate(findings: list) -> list:
    out, groups = [], {}
    for f in findings:
        if f.type in AGGREGATE_TYPES:
            groups.setdefault(f.cause_group, []).append(f)
        else:
            out.append(f)
    for cg, fs in groups.items():
        pages = sorted({f.page_url for f in fs if f.page_url})
        first = fs[0]
        out.append(Finding(first.type, first.severity, f"{first.message}（{len(pages)}ページ）", judge=first.judge,
                           page_url=pages[0] if pages else "", location=first.location if first.type != "BRAND_RESIDUE" else cg.split(":", 1)[1],
                           evidence=f"{first.evidence[:120]} ／ 例: " + ", ".join(pages[:5]), cause_group=cg,
                           extra={"pages": pages[:200], "page_count": len(pages)}))
    return out


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Fetcher:
    def __init__(self, cfg: dict, cache_dir: str):
        self.timeout = cfg["crawl"]["timeout_seconds"]
        self.delay = cfg["crawl"]["delay_seconds"]
        self.allowed = {h.lower() for h in cfg["allowed_hosts"]}
        self.opener = urllib.request.build_opener(NoRedirect())
        user, pw = os.environ.get("AHC_QA_USER"), os.environ.get("AHC_QA_PASS")
        self.auth = "Basic " + base64.b64encode(f"{user}:{pw}".encode()).decode() if user and pw else None
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def host_ok(self, url: str) -> bool:
        return (urllib.parse.urlsplit(url).hostname or "").lower() in self.allowed

    def _one(self, url: str, method: str = "GET"):
        if not self.host_ok(url):
            raise ValueError(f"host not allowed: {url}")
        req = urllib.request.Request(url, method=method, headers={"User-Agent": UA, "Accept-Encoding": "identity"})
        if self.auth:
            req.add_header("Authorization", self.auth)
        time.sleep(self.delay)
        try:
            with self.opener.open(req, timeout=self.timeout) as resp:
                return resp.status, dict(resp.headers), resp.read() if method == "GET" else b""
        except urllib.error.HTTPError as e:
            try:
                body = e.read() if method == "GET" else b""
                return e.code, dict(e.headers or {}), body
            finally:
                e.close()

    def get(self, url: str, max_hops: int = 10):
        """Follow redirects manually. Returns (final_url, status, headers, body, chain)."""
        chain = []
        cur = url
        for _ in range(max_hops + 1):
            status, headers, body = self._one(cur)
            if status in (301, 302, 303, 307, 308):
                loc = headers.get("Location") or headers.get("location")
                if not loc:
                    return cur, status, headers, body, chain
                nxt = urllib.parse.urljoin(cur, loc)
                chain.append((cur, status))
                if nxt in [c[0] for c in chain]:
                    return nxt, -1, headers, b"", chain + [(nxt, "LOOP")]
                if not self.host_ok(nxt):
                    return nxt, status, headers, b"", chain
                cur = nxt
                continue
            return cur, status, headers, body, chain
        return cur, -1, {}, b"", chain


def normalize(url: str) -> str:
    p = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((p.scheme, p.netloc.lower(), p.path or "/", p.query, ""))


class Crawler:
    def __init__(self, cfg: dict, state_dir: str, export: dict | None = None):
        self.cfg = cfg
        self.f = Fetcher(cfg, os.path.join(state_dir, "cache"))
        self.state_path = os.path.join(state_dir, "crawl_state.json")
        self.excl = cfg["crawl"]["exclude_patterns"]
        self.export = export or {}
        self.residue = [s.lower() for s in cfg.get("brand_residue_patterns", [])]
        self.inv = cfg["invariants"]
        self.findings: list[Finding] = []
        self.pages: dict[str, dict] = {}
        self.inbound: dict[str, list[str]] = {}
        self.images_checked: dict[str, dict] = {}
        self.scheme_mismatch: dict[str, list] = {}
        self._empty_cat_paths = self._empty_category_paths()

    def _empty_category_paths(self) -> set:
        from .data_checks import CategoryTree
        cats, prods = self.export.get("categories", []), self.export.get("products", [])
        if not cats:
            return set()
        tree = CategoryTree(cats, prods)
        out = set()
        for c in cats:
            if c.get("link") and not tree.subtree_product_ids(c["id"], prods):
                out.add(urllib.parse.urlsplit(c["link"]).path.rstrip("/") + "/")
        return out

    def excluded(self, url: str) -> bool:
        return any(x in url for x in self.excl)

    # ---- resume support
    def load_state(self):
        if os.path.exists(self.state_path):
            with open(self.state_path, encoding="utf-8") as fh:
                st = json.load(fh)
            self.pages, self.inbound, self.images_checked = st["pages"], st["inbound"], st["images"]
            return st.get("queue", [])
        return None

    def save_state(self, queue):
        tmp = self.state_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"pages": self.pages, "inbound": self.inbound, "images": self.images_checked, "queue": list(queue)}, fh, ensure_ascii=False)
        os.replace(tmp, self.state_path)

    def seeds(self) -> list[str]:
        base = self.cfg["base_url"]
        s = [base, urllib.parse.urljoin(base, "cart/"), urllib.parse.urljoin(base, "shop/"), urllib.parse.urljoin(base, "brands/")]
        for c in self.export.get("categories", []):
            if c.get("link"):
                s.append(c["link"])
        for p in self.export.get("products", []):
            if p.get("permalink"):
                s.append(p["permalink"])
        return [normalize(u) for u in s if self.f.host_ok(u)]

    def run(self, resume: bool = True, log=print) -> list[Finding]:
        queue = self.load_state() if resume else None
        if queue is None:
            queue = self.seeds()
            self.pages, self.inbound, self.images_checked = {}, {}, {}
        q = deque(dict.fromkeys(queue))
        seen = set(self.pages) | set(q)
        maxp = self.cfg["crawl"]["max_pages"]
        n = 0
        while q and len(self.pages) < maxp:
            url = q.popleft()
            if url in self.pages:
                continue
            try:
                final, status, headers, body, chain = self.f.get(url)
                rec = {"status": status, "final": final, "chain": chain, "title": "", "error": ""}
                ctype = (headers.get("Content-Type") or headers.get("content-type") or "")
                if status == 200 and "html" in ctype:
                    parser = PageParser()
                    parser.feed(body.decode("utf-8", "replace"))
                    rec["title"] = parser.title.strip()
                    # judge the page at the URL it was actually served from (after redirects)
                    self._page_checks(normalize(final), parser)
                    for href, where in parser.links:
                        nxt = self._resolve(final, href)
                        if not nxt:
                            continue
                        self.inbound.setdefault(nxt, [])
                        if len(self.inbound[nxt]) < 5:
                            self.inbound[nxt].append(url)
                        if nxt not in seen and not self.excluded(nxt):
                            seen.add(nxt)
                            q.append(nxt)
                    if self.cfg["crawl"]["check_images"]:
                        self._image_checks(final, parser)
            except Exception as e:  # one failure must not stop the run
                rec = {"status": 0, "final": url, "chain": [], "title": "", "error": f"{type(e).__name__}: {e}"}
            self.pages[url] = rec
            n += 1
            if n % 25 == 0:
                self.save_state(q)
                log(f"  巡回 {len(self.pages)} ページ（残り {len(q)}）")
        self.save_state(q)
        if not q and self.export:
            self.check_old_category_urls()
        self._status_findings()
        for origin, pages in self.scheme_mismatch.items():
            uniq = sorted(set(pages))
            self.findings.append(Finding("SCHEME_MISMATCH", "LOW", f"サイト内リンクの一部が {origin} を指しています" + ("（Localのため巡回は " + self.cfg['base_url'] + " に揃えて実施）" if origin.split(":")[0] != urllib.parse.urlsplit(self.cfg['base_url']).scheme and urllib.parse.urlsplit(self.cfg['base_url']).hostname.endswith((".local", ".localhost", ".test", "127.0.0.1", "localhost")) else ""),
                                         location=origin, evidence=f"{len(uniq)}ページ。例: " + ", ".join(uniq[:3]),
                                         cause_group="SCHEME_MISMATCH"))
        self.findings = aggregate(self.findings)
        return self.findings

    def _resolve(self, base: str, href: str) -> str | None:
        href = href.strip()
        if not href or href.startswith(("mailto:", "tel:", "javascript:", "#", "data:")):
            return None
        u = urllib.parse.urljoin(base, href)
        if not u.startswith(("http://", "https://")) or not self.f.host_ok(u):
            return None
        base_parts = urllib.parse.urlsplit(self.cfg["base_url"])
        want = base_parts.scheme
        parts = urllib.parse.urlsplit(u)
        # Local only: a self-signed https certificate is an environment issue, so crawl it as http.
        # On production the original URL is crawled as-is so a broken https link is still caught.
        local = (base_parts.hostname or "").endswith((".local", ".localhost", ".test")) or base_parts.hostname in ("localhost", "127.0.0.1")
        if local and parts.scheme != want and (parts.hostname or "") == (base_parts.hostname or ""):
            self.scheme_mismatch.setdefault(f"{parts.scheme}://{parts.netloc}", []).append(base)
            u = urllib.parse.urlunsplit((want,) + tuple(parts[1:]))
        elif not local and parts.scheme != want and (parts.hostname or "") == (base_parts.hostname or ""):
            self.scheme_mismatch.setdefault(f"{parts.scheme}://{parts.netloc}", []).append(base)
        return normalize(u)

    # ---- per-page checks
    def _page_checks(self, url: str, p: PageParser):
        if not p.title.strip():
            self.findings.append(Finding("TITLE_MISSING", "MEDIUM", "ページタイトル（<title>）がありません", page_url=url))
        hay = [("ページタイトル", p.title)] + [("本文", t) for t in p.text] + p.attr_text
        for where, val in hay:
            low = val.lower()
            for r in self.residue:
                if r in low:
                    self.findings.append(Finding("BRAND_RESIDUE", "HIGH", f"旧ブランド名が表示されています（{where}）",
                                                 page_url=url, location=where, evidence=val[:200],
                                                 cause_group=f"BRAND_RESIDUE:{where}:{r}"))
                    break
        self._invariants(url, p)

    def _invariants(self, url: str, p: PageParser):
        base_path = urllib.parse.urlsplit(self.cfg["base_url"]).path or "/"
        is_home = (urllib.parse.urlsplit(url).path or "/") == base_path
        hero = self.inv["pc_hero_class"]
        if is_home:
            vids = [e for e in p.elements if e["tag"] in ("video", "iframe") and (hero in e["ancestors"] or hero in e["classes"])]
            if vids:
                self.findings.append(Finding("INV_PC_HERO_STATIC", "HIGH", "PCホームのヒーローに動画要素があります（確定事項：静止画のみ）",
                                             page_url=url, location=f".{hero}", evidence=json.dumps(vids[0]["attrs"], ensure_ascii=False)[:200]))
            alt = self.inv["logo_alt"]
            header_cls = set(self.inv["header_classes"])
            logos = [e for e in p.elements if e["tag"] == "img" and (e["ancestors"] & header_cls) and (e["attrs"].get("alt") or "").strip() == alt]
            if not logos:
                self.findings.append(Finding("INV_LOGO", "HIGH", f"ヘッダーに承認済みロゴ（alt=\"{alt}\" の画像）が見つかりません",
                                             page_url=url, location="header"))
        header_cls = set(self.inv["header_classes"])
        markers = self.inv["dropdown_class_markers"]
        for e in p.elements:
            if not (e["ancestors"] & header_cls):
                continue
            hit = [c for c in e["classes"] if any(m in c.lower() for m in markers)]
            if hit:
                self.findings.append(Finding("INV_NO_HEADER_DROPDOWN", "HIGH", "ヘッダーにドロップダウンの要素があります（確定事項：廃止）",
                                             page_url=url, location=" ".join(hit), evidence=e["tag"],
                                             cause_group="INV_NO_HEADER_DROPDOWN"))
                break
        if self._empty_cat_paths:
            for href, where in p.links:
                path = urllib.parse.urlsplit(urllib.parse.urljoin(url, href)).path.rstrip("/") + "/"
                if path in self._empty_cat_paths:
                    self.findings.append(Finding("INV_EMPTY_CATEGORY_HIDDEN", "HIGH", "商品が0件のカテゴリーへのリンクが表示されています（確定事項：空カテゴリーは非表示）",
                                                 page_url=url, location=path, evidence=where,
                                                 cause_group=f"INV_EMPTY_CATEGORY_HIDDEN:{path}"))
        for (href, where), text in zip(p.links, p.link_texts):
            t = re.sub(r"\s+", " ", text).strip().upper().replace("’", "'")
            if ALL_GROUP_LINK.match(t):
                self.findings.append(Finding("INV_NO_ALL_GROUP_LINK", "HIGH", f"「{t}」のリンクがあります（確定事項：SHOES等を押せば全商品が出るため、ALL SHOESなどの重複リンクは設けない）",
                                             page_url=url, location=href, cause_group=f"INV_NO_ALL_GROUP_LINK:{t}"))
        if urllib.parse.urlsplit(url).path.startswith("/product-category/"):
            self._category_page_checks(url, p)
        if "/product/" in urllib.parse.urlsplit(url).path:
            gal = self.inv["product_gallery_class"]
            if not any(gal in e["classes"] for e in p.elements):
                self.findings.append(Finding("INV_PRODUCT_VERTICAL_GALLERY", "HIGH", f"商品ページに縦スクロールのギャラリー（.{gal}）がありません",
                                             page_url=url))
            sliders = [e for e in p.elements if e["classes"] & {"flex-viewport", "flex-control-nav", "swiper", "slick-slider"}]
            if sliders:
                self.findings.append(Finding("INV_PRODUCT_VERTICAL_GALLERY", "HIGH", "商品ページにスライダー形式のギャラリーがあります（確定事項：縦スクロール）",
                                             page_url=url, location=" ".join(sorted(sliders[0]["classes"]))))

    def _category_page_checks(self, url: str, p: PageParser):
        # /page/N/ belongs to the same category; the nav links to the category's first page.
        path = re.sub(r"/page/\d+/?$", "/", urllib.parse.urlsplit(url).path).rstrip("/") + "/"
        nav = [e for e in p.elements if e["tag"] == "a" and "nx-catnav__link" in e["classes"]]
        # An empty category (NO ITEMS, reached directly) is hidden from the nav by rule, so it cannot be highlighted.
        empty = any("nx-archive__empty" in e["classes"] for e in p.elements)
        if nav and not empty:
            cur = [e for e in nav if e["attrs"].get("aria-current") == "page"]
            ok = len(cur) == 1 and urllib.parse.urlsplit(urllib.parse.urljoin(url, cur[0]["attrs"].get("href", ""))).path.rstrip("/") + "/" == path
            if not ok:
                self.findings.append(Finding("CAT_CURRENT_HIGHLIGHT", "HIGH", "カテゴリーナビで、今いるカテゴリーがハイライトされていません",
                                             page_url=url, evidence=f"aria-current の数: {len(cur)}", cause_group="CAT_CURRENT_HIGHLIGHT"))
        ids = []
        for e in p.elements:
            if e["tag"] == "li" and "product" in e["classes"]:
                pid = next((c for c in e["classes"] if re.fullmatch(r"post-\d+", c)), None)
                if pid:
                    ids.append(pid)
        dups = sorted({i for i in ids if ids.count(i) > 1})
        if dups:
            self.findings.append(Finding("CAT_LIST_DUPLICATE", "HIGH", "商品一覧に同じ商品が2回以上表示されています",
                                         page_url=url, evidence=", ".join(dups[:20]), cause_group="CAT_LIST_DUPLICATE"))

    def check_old_category_urls(self):
        from .category_spec import old_category_urls
        for old, new, slug in old_category_urls(self.export, self.cfg["base_url"]):
            if not self.f.host_ok(old):
                continue
            try:
                final, status, _, _, chain = self.f.get(old)
            except Exception as e:
                self.findings.append(Finding("CAT_OLD_URL", "HIGH", "旧カテゴリーURLを確認できませんでした", page_url=old, location=slug, evidence=str(e)[:200]))
                continue
            first = chain[0][1] if chain else status
            if normalize(final) == normalize(old) and status == 200 and normalize(new) == normalize(old):
                continue  # not yet migrated: old URL is the current URL
            if not (len(chain) == 1 and first == 301 and normalize(final) == normalize(new) and status == 200):
                self.findings.append(Finding("CAT_OLD_URL", "HIGH", "旧カテゴリーURLが新しいURLへ1回の301転送になっていません",
                                             page_url=old, location=slug,
                                             evidence=" → ".join(f"{c[0]}({c[1]})" for c in chain) + f" → {final}({status}) / 期待: {new}",
                                             cause_group="CAT_OLD_URL"))

    def _image_checks(self, page_url: str, p: PageParser):
        maxi = self.cfg["crawl"]["max_images"]
        for src, alt in p.images:
            u = self._resolve(page_url, src)
            if not u:
                continue
            if u in self.images_checked:
                rec = self.images_checked[u]
                if rec.get("problem") and len(rec.setdefault("pages", [])) < 5 and page_url not in rec["pages"]:
                    rec["pages"].append(page_url)
                continue
            if len(self.images_checked) >= maxi:
                return
            rec = {"pages": [page_url], "problem": "", "detail": ""}
            try:
                final, status, headers, body, _ = self.f.get(u)
                if status != 200:
                    rec["problem"], rec["detail"] = "http", f"HTTP {status}"
                elif self.cfg["crawl"]["verify_image_decode"] and Image is not None and not u.lower().endswith(".svg"):
                    try:
                        with Image.open(io.BytesIO(body)) as im:
                            im.verify()
                        with Image.open(io.BytesIO(body)) as im:
                            im.load()
                    except Exception as e:
                        rec["problem"], rec["detail"] = "broken", f"{type(e).__name__}: {e}"
            except Exception as e:
                rec["problem"], rec["detail"] = "http", f"{type(e).__name__}: {e}"
            self.images_checked[u] = rec

    def _status_findings(self):
        for url, rec in self.pages.items():
            src = self.inbound.get(url, [])
            where = "リンク元: " + ", ".join(src[:3]) if src else ""
            st = rec["status"]
            if rec.get("error"):
                self.findings.append(Finding("FETCH_ERROR", "HIGH", "ページを取得できませんでした", page_url=url, location=where, evidence=rec["error"]))
            elif st == -1:
                kind = "REDIRECT_LOOP" if rec["chain"] and rec["chain"][-1][1] == "LOOP" else "REDIRECT_CHAIN"
                self.findings.append(Finding(kind, "HIGH", "リダイレクトが終わりません", page_url=url, location=where,
                                             evidence=" → ".join(str(c[0]) for c in rec["chain"])))
            elif st >= 500:
                self.findings.append(Finding("HTTP_ERROR", "CRITICAL", f"サーバーエラー（HTTP {st}）", page_url=url, location=where,
                                             cause_group=f"HTTP_{st}"))
            elif st >= 400:
                t = "BROKEN_LINK" if src else "HTTP_ERROR"
                self.findings.append(Finding(t, "HIGH", f"リンク先がありません（HTTP {st}）", page_url=url, location=where,
                                             cause_group=f"HTTP_{st}"))
            if st != -1 and len(rec.get("chain") or []) > self.cfg["crawl"]["max_redirect_hops_ok"]:
                self.findings.append(Finding("REDIRECT_CHAIN", "MEDIUM", f"リダイレクトが{len(rec['chain'])}回続いています",
                                             page_url=url, location=where, evidence=" → ".join(f"{c[0]}({c[1]})" for c in rec["chain"]) + f" → {rec['final']}"))
        for u, rec in self.images_checked.items():
            if rec["problem"] == "http":
                self.findings.append(Finding("IMAGE_HTTP_ERROR", "HIGH", "画像が表示されません", image_url=u,
                                             page_url=rec["pages"][0], location="表示ページ: " + ", ".join(rec["pages"][:3]), evidence=rec["detail"]))
            elif rec["problem"] == "broken":
                self.findings.append(Finding("IMAGE_BROKEN", "HIGH", "画像ファイルが壊れています", image_url=u,
                                             page_url=rec["pages"][0], location="表示ページ: " + ", ".join(rec["pages"][:3]), evidence=rec["detail"]))

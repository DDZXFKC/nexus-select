"""A tiny stateful mock of the shop, with switchable intentional defects.

defects=set() serves a clean site (used to check for false positives).
"""
from __future__ import annotations

import http.server
import io
import threading
import urllib.parse

from PIL import Image


def png_bytes(color=(255, 255, 255)) -> bytes:
    b = io.BytesIO()
    Image.new("RGB", (40, 40), color).save(b, "PNG")
    return b.getvalue()


GOOD_PNG = png_bytes()
BROKEN_PNG = GOOD_PNG[:30]


def make_handler(defects: set):
    carts: dict[str, dict] = {}

    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _cart(self):
            ck = self.headers.get("Cookie", "")
            sid = ck.split("sid=")[1].split(";")[0] if "sid=" in ck else None
            if not sid:
                sid = str(len(carts) + 1)
                carts[sid] = {}
            return sid, carts.setdefault(sid, {})

        def _send(self, code, body=b"", ctype="text/html; charset=utf-8", headers=None):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            for k, v in (headers or {}).items():
                self.send_header(k, v)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def page(self, title, body, sid=None):
            header_extra = "<ul class='nx-dropdown'><li>x</li></ul>" if "dropdown" in defects else ""
            footer_name = "NEXUS SELECT" if "residue" in defects else "AFTER HOURS CLUB"
            empty_link = "<a href='/product-category/kids/'>KIDS</a>" if "emptycat" in defects else ""
            nav = ("<header class='nexus-v08-header'><a href='/'><img src='/img/logo.png' alt='AFTER HOURS CLUB'></a>"
                   f"<nav><a href='/product-category/mens/'>MEN</a>{empty_link}<a href='/cart/'>BAG</a></nav>{header_extra}</header>")
            t = f"<title>{title}</title>" if title else ""
            html = f"<!doctype html><html><head>{t}</head><body>{nav}{body}<footer><p>{footer_name}</p></footer></body></html>"
            hdr = {"Set-Cookie": f"sid={sid}; Path=/"} if sid else None
            self._send(200, html.encode(), headers=hdr)

        def do_GET(self):
            u = urllib.parse.urlsplit(self.path)
            path, q = u.path, urllib.parse.parse_qs(u.query)
            sid, cart = self._cart()
            if path == "/":
                hero_media = "<video src='/v.mp4'></video>" if "video" in defects else "<img src='/img/hero.png' alt='hero'>"
                extra = ""
                if "broken" in defects:
                    extra += "<a href='/missing-page/'>missing</a><img src='/img/broken.png' alt='b'><a href='/r1/'>r</a><a href='/loop-a/'>loop</a>"
                self.page("Home", f"<section class='nexus-pc-hero'>{hero_media}</section>"
                                  "<a href='/product/test-shoe/'>shoe</a><a href='/product/test-tee/'>tee</a>"
                                  "<a href='/order-tracking/'>track</a>" + extra, sid)
            elif path == "/product-category/mens/":
                self.page("Men", "<a href='/product/test-shoe/'>shoe</a>", sid)
            elif path == "/product-category/mens/mens-shoes/mens-sneakers/":
                cur = "" if "nohighlight" in defects else " aria-current='page'"
                all_link = "<li><a class='nx-catnav__link' href='/product-category/mens/mens-shoes/'>ALL SHOES</a></li>" if "alllink" in defects else ""
                nav = ("<details class='nx-catnav' open><nav><ul>"
                       "<li><a class='nx-catnav__link nx-catnav__link--all' href='/product-category/mens/'>ALL MEN'S ITEMS</a></li>"
                       "<li><a class='nx-catnav__link' href='/product-category/mens/mens-shoes/'>SHOES</a></li>" + all_link +
                       f"<li><a class='nx-catnav__link' href='/product-category/mens/mens-shoes/mens-sneakers/'{cur}>Sneakers</a></li></ul></nav></details>")
                items = "<li class='product type-product post-1'><a href='/product/test-shoe/'>shoe</a></li>"
                if "dupitem" in defects:
                    items += "<li class='product type-product post-1'><a href='/product/test-shoe/'>shoe</a></li>"
                self.page("Sneakers", nav + f"<ul class='products'>{items}</ul>", sid)
            elif path == "/product-category/mens/mens-sneakers/":
                if "oldurl" in defects:
                    self._send(302, headers={"Location": "/product-category/mens/mens-shoes/mens-sneakers/"})
                else:
                    self._send(301, headers={"Location": "/product-category/mens/mens-shoes/mens-sneakers/"})
            elif path.startswith("/product-category/"):
                self.page("Category", "<p>NO ITEMS</p>", sid)
            elif path.startswith("/product/"):
                slug = path.split("/")[2]
                gallery = "" if "nogallery" in defects and slug == "test-tee" else "<div class='woocommerce-product-gallery nexus-gallery'><img src='/img/p.png' alt='p'></div>"
                if slug == "test-shoe":
                    form = ("<form class='cart variations_form' method='post' action='/add/'>"
                            "<select name='attribute_pa_size'><option value=''>選択</option><option value='27'>27</option></select>"
                            "<input type='hidden' name='pid' value='1'><button type='submit' class='single_add_to_cart_button'>ADD TO BAG</button></form>")
                else:
                    dis = " disabled" if "addbroken" in defects else ""
                    form = ("<form class='cart' method='post' action='/add/'><input type='hidden' name='pid' value='2'>"
                            f"<button type='submit' class='single_add_to_cart_button'{dis}>ADD TO BAG</button></form>")
                title = "" if ("notitle" in defects and slug == "test-tee") else slug
                self.page(title, gallery + form, sid)
            elif path == "/cart/":
                if "remove_item" in q:
                    cart.pop(q["remove_item"][0], None)
                    return self._send(302, headers={"Location": "/cart/"})
                prices = {"1": 20000, "2": 8000}
                rows, total = "", 0
                for pid, n in cart.items():
                    unit = prices[pid]
                    sub = unit * n + (1 if "badtotal" in defects else 0)
                    total += sub
                    rows += (f"<tr class='cart_item'><td><a class='remove' href='/cart/?remove_item={pid}'>×</a></td>"
                             f"<td class='product-price'>¥{unit:,}</td><td><input class='qty' name='qty_{pid}' value='{n}'></td>"
                             f"<td class='product-subtotal'>¥{sub:,}</td></tr>")
                ship = "送料 ¥1,000" if "shipping" in defects else "送料無料"
                body = (f"<form method='post' action='/cart/update/'><table>{rows}</table>"
                        "<button type='submit' name='update_cart'>更新</button></form>"
                        f"<table><tr class='cart-subtotal'><td>¥{total:,}</td></tr><tr class='woocommerce-shipping-totals'><td>{ship}</td></tr></table>")
                self.page("Cart", body, sid)
            elif path == "/checkout/":
                body = ("<form class='checkout'><input id='billing_last_name'><input id='billing_email'><input id='billing_postcode'>"
                        "<button id='place_order' onclick='window.__placed=1;return false'>注文する</button></form>")
                self.page("Checkout", body, sid)
            elif path == "/order-tracking/":
                self.page("Tracking", "<form><input name='orderid'></form>", sid)
            elif path == "/shop/" or path == "/brands/":
                self.page(path.strip("/"), "<p>list</p>", sid)
            elif path == "/r1/":
                self._send(301, headers={"Location": "/r2/"})
            elif path == "/r2/":
                self._send(301, headers={"Location": "/r3/"})
            elif path == "/r3/":
                self.page("R3", "<p>end</p>", sid)
            elif path == "/loop-a/":
                self._send(302, headers={"Location": "/loop-b/"})
            elif path == "/loop-b/":
                self._send(302, headers={"Location": "/loop-a/"})
            elif path.startswith("/img/"):
                if path == "/img/broken.png":
                    self._send(200, BROKEN_PNG, "image/png")
                else:
                    self._send(200, GOOD_PNG, "image/png")
            else:
                self._send(404, b"<html><head><title>404</title></head><body>not found</body></html>")

        def do_POST(self):
            sid, cart = self._cart()
            n = int(self.headers.get("Content-Length") or 0)
            form = urllib.parse.parse_qs(self.rfile.read(n).decode())
            if self.path == "/add/":
                pid = form["pid"][0]
                cart[pid] = cart.get(pid, 0) + 1
                return self._send(302, headers={"Location": "/product/test-shoe/" if pid == "1" else "/product/test-tee/"})
            if self.path == "/cart/update/":
                for k, v in form.items():
                    if k.startswith("qty_"):
                        cart[k[4:]] = int(v[0])
                return self._send(302, headers={"Location": "/cart/"})
            self._send(404)

    return H


class MockSite:
    def __init__(self, defects=()):
        self.defects = set(defects)
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), make_handler(self.defects))
        self.port = self.httpd.server_address[1]
        self.base = f"http://127.0.0.1:{self.port}/"

    def __enter__(self):
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *a):
        self.httpd.shutdown()


def mock_export(base: str, defects=()) -> dict:
    d = set(defects)
    cats = [
        {"id": 10, "name": "MEN'S", "slug": "mens", "parent": 0, "count": 1, "link": base + "product-category/mens/"},
        {"id": 11, "name": "WOMEN'S", "slug": "womens", "parent": 0, "count": 0, "link": base + "product-category/womens/"},
        {"id": 12, "name": "KIDS", "slug": "kids", "parent": 0, "count": 0, "link": base + "product-category/kids/"},
        {"id": 20, "name": "SHOES", "slug": "mens-shoes", "parent": 10, "count": 1, "link": base + "product-category/mens/mens-shoes/"},
        {"id": 30, "name": "Sneakers", "slug": "mens-sneakers", "parent": 20, "count": 1, "link": base + "product-category/mens/mens-shoes/mens-sneakers/"},
        {"id": 21, "name": "CLOTHING", "slug": "womens-clothing", "parent": 11, "count": 1 if "countmismatch" not in d else 5, "link": base + "product-category/womens/womens-clothing/"},
    ]
    img = lambda i, exists=True: {"id": i, "url": base + f"img/p{i}.png", "file": f"/x/p{i}.png", "exists": exists,
                                   "mime": "image/png", "width": 1000, "height": 1000,
                                   "sizes": {"thumbnail": {"file": f"/x/p{i}-150.png", "exists": True, "width": 150, "height": 150}}}
    shoe = {"id": 1, "name": "Test Shoe", "slug": "test-shoe", "type": "variable", "status": "publish", "visibility": "visible",
            "sku": "SHOE-1", "price": "20000", "regular_price": "", "sale_price": "", "description_length": 100,
            "short_description_length": 10, "category_ids": [10, 20, 30], "brands": ["Nike"], "attributes": {}, "image_id": 100,
            "gallery_ids": [], "permalink": base + "product/test-shoe/", "stock_status": "instock", "purchasable": True,
            "variations": [{"id": 101, "status": "publish", "sku": "SHOE-1-27", "price": "20000" if "varprice" not in d else "",
                            "regular_price": "20000", "sale_price": "", "attributes": {"pa_size": "27"},
                            "stock_status": "instock", "purchasable": True, "image_id": None}]}
    tee = {"id": 2, "name": "Test Tee" if "noname" not in d else "", "slug": "test-tee", "type": "simple", "status": "publish",
           "visibility": "visible", "sku": "TEE-1" if "dupsku" not in d else "SHOE-1",
           "price": "8000" if "noprice" not in d else "", "regular_price": "8000", "sale_price": "",
           "description_length": 50, "short_description_length": 0,
           "category_ids": [21] if "nocat" not in d else [], "brands": ["Patta"] if "nobrand" not in d else [],
           "attributes": {}, "image_id": 200 if "noimage" not in d else None, "gallery_ids": [],
           "permalink": base + "product/test-tee/", "stock_status": "instock", "purchasable": True, "variations": []}
    if "gendermix" in d:
        tee["category_ids"] = [21, 12]
    images = [img(100), img(200, exists="filemissing" not in d)]
    return {"exported_at": "2026-11-15T00:00:00Z",
            "site": {"blogname": "NEXUS SELECT" if "blogname" in d else "AFTER HOURS CLUB", "blogdescription": "",
                     "home_url": base, "currency": "JPY", "theme": "nexus-select",
                     "theme_mods": {"nexus_pc_hero_image": 1, "nexus_pc_hero_video": 5 if "video" in d else 0}},
            "categories": cats, "products": [shoe, tee], "images": images}

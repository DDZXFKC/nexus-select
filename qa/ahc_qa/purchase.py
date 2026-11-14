"""Purchase-flow checks with Playwright (WebKit + Chromium).

Safety rules (hard-coded, not configurable):
- Runs only when the base URL host is in purchase_allowed_hosts AND ends with .local / is localhost.
- Never clicks "place order" / submits checkout. Stops at the checkout page.
- Never types personal data. Fills nothing on the checkout form.
"""
from __future__ import annotations

import os
import re
import urllib.parse

from .findings import Finding

SAFE_SUFFIXES = (".local", ".localhost", ".test")
SAFE_HOSTS = {"localhost", "127.0.0.1", "[::1]"}


def host_is_safe(base_url: str, allowed: list[str]) -> bool:
    h = (urllib.parse.urlsplit(base_url).hostname or "").lower()
    return h in {a.lower() for a in allowed} and (h in SAFE_HOSTS or h.endswith(SAFE_SUFFIXES))


def _yen(text: str) -> int | None:
    digits = re.sub(r"[^\d]", "", text or "")
    return int(digits) if digits else None


def pick_test_products(export: dict, n: int = 2) -> list[dict]:
    """One in-stock variable product and one simple product, if available."""
    picks, seen_types = [], set()
    for p in export.get("products", []):
        if p.get("stock_status") != "instock" or not p.get("permalink"):
            continue
        t = p.get("type")
        if t == "variable":
            ok = [v for v in p.get("variations", []) if v.get("stock_status") == "instock" and v.get("purchasable")]
            if not ok:
                continue
        if t in seen_types:
            continue
        seen_types.add(t)
        picks.append(p)
        if len(picks) >= n:
            break
    return picks


def run_purchase_checks(cfg: dict, export: dict, shot_dir: str, log=print) -> list[Finding]:
    pc = cfg["purchase"]
    base = cfg["base_url"]
    if not pc.get("enabled"):
        return []
    if not host_is_safe(base, cfg.get("purchase_allowed_hosts", [])):
        return [Finding("PURCHASE_SKIPPED", "REVIEW", "購入機能の検査は、Local環境（.local など）でのみ実行します。対象が許可されていないため実行しませんでした",
                        judge="人", page_url=base)]
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception:
        return [Finding("PURCHASE_SKIPPED", "REVIEW", "Playwrightが入っていないため、購入機能の検査を実行できませんでした（README参照）",
                        judge="人", page_url=base)]
    products = pick_test_products(export)
    if not products:
        return [Finding("PURCHASE_SKIPPED", "REVIEW", "検査に使える在庫ありの商品が見つかりませんでした", judge="人", page_url=base)]

    os.makedirs(shot_dir, exist_ok=True)
    out: list[Finding] = []
    user, pw = os.environ.get("AHC_QA_USER"), os.environ.get("AHC_QA_PASS")
    with sync_playwright() as pwr:
        for bname in pc.get("browsers", ["webkit", "chromium"]):
            try:
                browser = getattr(pwr, bname).launch()
            except Exception as e:
                out.append(Finding("PURCHASE_SKIPPED", "REVIEW", f"{bname} を起動できませんでした（playwright install {bname} が必要かもしれません）",
                                   judge="人", evidence=str(e)[:200], location=bname))
                continue
            for vp_name, vp in (("PC", {"width": 1440, "height": 900}), ("SP", {"width": 390, "height": 844})):
                ctx = browser.new_context(viewport=vp, http_credentials={"username": user, "password": pw} if user and pw else None,
                                          is_mobile=(vp_name == "SP" and bname == "chromium"))
                page = ctx.new_page()
                tag = f"{bname}/{vp_name}"
                try:
                    out.extend(_flow(page, base, products, pc, shot_dir, tag, log))
                except Exception as e:
                    shot = _shot(page, shot_dir, f"{bname}-{vp_name}-error", pc)
                    out.append(Finding("PURCHASE_FLOW", "CRITICAL", "購入の流れの途中で処理が止まりました", location=tag,
                                       evidence=f"{type(e).__name__}: {str(e)[:300]}", screenshot=shot, page_url=page.url,
                                       cause_group=f"PURCHASE_FLOW:{type(e).__name__}"))
                finally:
                    ctx.close()
            browser.close()
    return out


def _shot(page, d, name, pc) -> str:
    if not pc.get("screenshot"):
        return ""
    path = os.path.join(d, re.sub(r"[^\w.-]", "_", name) + ".png")
    try:
        page.screenshot(path=path, full_page=True)
        return path
    except Exception:
        return ""


def _fail(msg, tag, page, shot_dir, pc, name, sev="CRITICAL", **kw) -> Finding:
    return Finding("PURCHASE_FLOW", sev, msg, location=tag, page_url=page.url,
                   screenshot=_shot(page, shot_dir, f"{tag}-{name}", pc), cause_group=f"PURCHASE_FLOW:{name}", **kw)


def _flow(page, base, products, pc, shot_dir, tag, log) -> list[Finding]:
    out = []
    added = 0
    for p in products:
        page.goto(p["permalink"], wait_until="domcontentloaded")
        base_kw = dict(product_id=p["id"], product_name=p["name"])
        form = page.locator("form.cart").first
        if form.count() == 0:
            out.append(_fail("商品ページにカート追加フォームがありません", tag, page, shot_dir, pc, "no-form", **base_kw))
            continue
        if p["type"] == "variable":
            v = next(v for v in p["variations"] if v.get("stock_status") == "instock" and v.get("purchasable"))
            for attr, val in (v.get("attributes") or {}).items():
                sel = page.locator(f"form.variations_form select[name='attribute_{attr}']")
                if sel.count() == 0:
                    out.append(_fail(f"選択肢（{attr}）のプルダウンが見つかりません", tag, page, shot_dir, pc, "no-select", sev="HIGH", **base_kw))
                    continue
                if val:
                    sel.select_option(value=val)
                else:
                    opts = sel.locator("option").evaluate_all("os => os.map(o => o.value).filter(Boolean)")
                    if opts:
                        sel.select_option(value=opts[0])
            page.wait_for_timeout(800)
            # colour change -> main image should still be visible
            main_img = page.locator(".nexus-gallery img, .woocommerce-product-gallery img").first
            if main_img.count() and not main_img.evaluate("i => i.complete && i.naturalWidth > 0"):
                out.append(_fail("選択肢を変えたあと、商品画像が表示されていません", tag, page, shot_dir, pc, "variation-image", sev="HIGH", **base_kw))
        btn = page.locator("form.cart button[type=submit]:not([disabled]), form.cart .single_add_to_cart_button").first
        if btn.count() == 0 or btn.is_disabled():
            out.append(_fail("ADD TO BAG ボタンが押せない状態です", tag, page, shot_dir, pc, "add-disabled", **base_kw))
            continue
        btn.click()
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(1200)
        if page.locator(".woocommerce-error").count():
            out.append(_fail("カート追加でエラーが表示されました", tag, page, shot_dir, pc, "add-error",
                             evidence=page.locator(".woocommerce-error").first.inner_text()[:200], **base_kw))
            continue
        added += 1

    page.goto(urllib.parse.urljoin(base, "cart/"), wait_until="domcontentloaded")
    rows = page.locator("tr.cart_item, .wc-block-cart-items__row")
    if rows.count() < added or added == 0:
        out.append(_fail(f"カートに商品が入っていません（追加 {added} 件、カート {rows.count()} 行）", tag, page, shot_dir, pc, "cart-empty"))
        return out

    # quantity change on classic cart
    qty = page.locator("tr.cart_item input.qty").first
    if qty.count():
        qty.fill("2")
        upd = page.locator("button[name='update_cart']")
        if upd.count():
            upd.click()
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(1200)
        line = page.locator("tr.cart_item").first
        unit = _yen(line.locator(".product-price").inner_text()) if line.locator(".product-price").count() else None
        sub = _yen(line.locator(".product-subtotal").inner_text()) if line.locator(".product-subtotal").count() else None
        if unit and sub and sub != unit * 2:
            out.append(_fail(f"数量2にしたときの小計が合いません（単価 {unit} × 2 ≠ {sub}）", tag, page, shot_dir, pc, "qty-subtotal"))
        # totals: sum of line subtotals vs cart subtotal
        subs = [_yen(t) for t in page.locator("tr.cart_item .product-subtotal").all_inner_texts()]
        cart_sub = page.locator(".cart-subtotal td, .cart-subtotal .amount").first
        if subs and all(subs) and cart_sub.count():
            cs = _yen(cart_sub.inner_text())
            if cs is not None and cs != sum(subs):
                out.append(_fail(f"カートの小計が商品ごとの合計と合いません（{sum(subs)} ≠ {cs}）", tag, page, shot_dir, pc, "cart-subtotal"))
    if pc.get("free_shipping_expected"):
        ship = page.locator(".woocommerce-shipping-totals, .shipping, .wc-block-components-totals-shipping").first
        txt = ship.inner_text() if ship.count() else ""
        if txt and not re.search(r"無料|free|¥\s*0(?!\d)|0円", txt, re.I):
            out.append(_fail("日本国内送料無料が適用されていない可能性があります", tag, page, shot_dir, pc, "shipping", sev="HIGH",
                             judge="人", evidence=txt[:200]))
    # checkout page loads (we never fill or submit it)
    page.goto(urllib.parse.urljoin(base, "checkout/"), wait_until="domcontentloaded")
    if page.locator("form.checkout, .wc-block-checkout").count() == 0:
        out.append(_fail("チェックアウト画面が表示されません", tag, page, shot_dir, pc, "checkout"))
    else:
        for fid in ("billing_last_name", "billing_email", "billing_postcode"):
            if page.locator(f"#{fid}").count() == 0:
                out.append(_fail(f"チェックアウトの入力欄（{fid}）がありません", tag, page, shot_dir, pc, f"field-{fid}", sev="HIGH"))
    # order tracking page
    tp = pc.get("tracking_page_path")
    if tp:
        resp = page.goto(urllib.parse.urljoin(base, tp.lstrip("/")), wait_until="domcontentloaded")
        if not resp or resp.status >= 400:
            out.append(_fail(f"注文追跡ページが表示されません（HTTP {resp.status if resp else '?'}）", tag, page, shot_dir, pc, "tracking", sev="HIGH"))
        elif page.locator("form").count() == 0:
            out.append(_fail("注文追跡ページに入力フォームがありません", tag, page, shot_dir, pc, "tracking-form", sev="HIGH", judge="人"))
    # remove one item
    page.goto(urllib.parse.urljoin(base, "cart/"), wait_until="domcontentloaded")
    before = page.locator("tr.cart_item").count()
    rm = page.locator("tr.cart_item a.remove").first
    if rm.count():
        rm.click()
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(1200)
        after = page.locator("tr.cart_item").count()
        if after != before - 1:
            out.append(_fail(f"カートから商品を削除できません（{before} → {after}）", tag, page, shot_dir, pc, "remove"))
    # leave the cart empty for the next run
    page.goto(urllib.parse.urljoin(base, "cart/"), wait_until="domcontentloaded")
    for _ in range(10):
        r = page.locator("tr.cart_item a.remove").first
        if not r.count():
            break
        r.click()
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(600)
    log(f"  購入機能 {tag}: 不具合 {len(out)} 件")
    return out

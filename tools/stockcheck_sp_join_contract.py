"""Shoe Palace SKU join: parent Shopify product ID + exact variant SKU.

Identity only; never approves purchase or changes source size strings.
"""
import re
from urllib.parse import urlparse
SP_SKU=re.compile(r"SP-([0-9]+)$")
def _txt(x): return str(x).strip() if x is not None else ""
def link_sp_variation(product, variation, supplier_records):
    pid=product.get("product_id"); vid=variation.get("variation_id")
    if type(pid) is not int or type(vid) is not int or pid<=0 or vid<=0:
        return {"status":"HOLD","reason":"INVALID_WOO_IDS"}
    if variation.get("product_id")!=pid:
        return {"status":"HOLD","reason":"WOO_PRODUCT_VARIATION_MISMATCH"}
    if _txt(product.get("product_type")).lower()!="variable":
        return {"status":"HOLD","reason":"UNSUPPORTED_TYPE"}
    match=SP_SKU.fullmatch(_txt(product.get("sku")))
    if not match or _txt(product.get("shop_code")).upper()!="SP" or match.group(1)!=_txt(product.get("supplier_product_id")):
        return {"status":"HOLD","reason":"SP_PARENT_ID_MISMATCH"}
    woo_sku=_txt(variation.get("variation_sku",variation.get("sku")))
    if not woo_sku: return {"status":"HOLD","reason":"MISSING_WOO_VARIATION_SKU"}
    candidates=[]
    for row in supplier_records:
        if row.get("verified") is not True: continue
        if _txt(row.get("shop_code")).upper()!="SP" or _txt(row.get("supplier_product_id"))!=match.group(1): continue
        ep=row.get("woo_product_id"); ev=row.get("variation_id",row.get("woo_variation_id"))
        if ep is not None and _txt(ep)!=str(pid): continue
        if ev is not None and _txt(ev)!=str(vid): continue
        # Independent supplier Shopify variants[].sku evidence is mandatory.
        if not _txt(row.get("merchant_variant_sku")) or _txt(row.get("merchant_variant_sku"))!=woo_sku: continue
        merchant_variant_id=_txt(row.get("merchant_variant_id"))
        if not merchant_variant_id.isdecimal(): continue
        url=_txt(row.get("source_url")); parsed=urlparse(url)
        if parsed.scheme!="https" or parsed.hostname!="www.shoepalace.com" or parsed.username or parsed.password or not parsed.path.startswith("/products/"): continue
        candidates.append(row)
    if len(candidates)!=1:
        return {"status":"HOLD","reason":"NO_VERIFIED_VARIATION_SKU_MATCH" if not candidates else "AMBIGUOUS_SUPPLIER_VARIANT"}
    row=candidates[0]
    return {"status":"CANDIDATE_ONLY","woo_product_id":pid,"woo_variation_id":vid,
            "woo_variation_sku":woo_sku,"shop_code":"SP","supplier_product_id":match.group(1),
            "merchant_variant_id":_txt(row["merchant_variant_id"]),"source_url":_txt(row["source_url"]),
            "reason":"SKU_IDENTITY_ONLY_LIVE_STOCK_AND_PRICE_PENDING"}

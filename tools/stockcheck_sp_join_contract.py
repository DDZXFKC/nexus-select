"""Fail-closed identity contract for Woo variation -> supplier Shopify variant.

This is an offline candidate linker. It does not fetch live stock or prices,
grant checkout, infer unknown variant IDs, or write to WordPress.
"""
from __future__ import annotations
import re
import unicodedata
from collections import defaultdict
from decimal import Decimal, InvalidOperation

SP_SKU = re.compile(r"^SP-([0-9]+)$")
UNSUPPORTED = {"", "N/A", "UNKNOWN", "NONE", "-"}
def _norm(value):
    return unicodedata.normalize("NFKC",str(value or "")).strip()
def _custom_attrs(attrs):
    if not isinstance(attrs,dict):
        return {}
    return { _norm(k).lower().removeprefix("attribute_"): _norm(v) for k,v in attrs.items() }

def _us_size_key(value):
    """US numeric format only; never infer UK/EU or gender conversion.

    This is a syntactic comparison, NOT authorization to match a new product:
    the matching evidence must explicitly identify Woo variation_id.
    """
    match = re.fullmatch(r"US\s+([0-9]+(?:\.[0-9]+)?)", _norm(value), re.I)
    if not match:
        return None
    try:
        number = Decimal(match.group(1))
    except InvalidOperation:
        return None
    if number <= 0 or (number * 2) != (number * 2).to_integral_value():
        return None
    return str(number.normalize())

def _gs_size_key(value):
    """Only explicitly observed SP grade-school Y-sizes; cm is annotation.

    The cm value is NOT used to calculate or infer a shoe size, and the
    merchant variant ID + Woo variation ID must still agree.
    """
    match = re.fullmatch(
        r"US\\s+([1-9][0-9]?Y)\\s*\\(([0-9]+(?:\\.[0-9]+)?)cm\\)",
        _norm(value), re.I)
    return match.group(1).upper() if match else None

def link_sp_variation(product, variation, supplier_records):
    """Return a single verified candidate or HOLD with explicit reason.

    supplier_records must originate from a reviewed SP product+variant export:
    {shop_code, supplier_product_id, merchant_variant_id, size, color,
     source_url, verified}. No fuzzy matching or guessed URL generation.
    """
    pid=product.get("product_id")
    vid=variation.get("variation_id",0)
    if variation.get("product_id")!=pid:
        return {"status":"HOLD","reason":"WOO_PRODUCT_VARIATION_MISMATCH"}
    sku=_norm(product.get("sku"))
    match=SP_SKU.fullmatch(sku)
    shop=_norm(product.get("shop_code")).upper()
    supplier=_norm(product.get("supplier_product_id"))
    if not match or shop!="SP" or supplier != match.group(1):
        return {"status":"HOLD","reason":"SP_PARENT_ID_MISMATCH"}
    if not isinstance(vid,int) or vid<0:
        return {"status":"HOLD","reason":"INVALID_WOO_VARIATION_ID"}
    typ=_norm(product.get("product_type")).lower()
    if typ=="variable" and vid==0:
        return {"status":"HOLD","reason":"MISSING_VARIATION"}
    if typ=="simple" and vid!=0:
        return {"status":"HOLD","reason":"SIMPLE_VARIATION_MISMATCH"}
    if typ not in ("simple","variable"):
        return {"status":"HOLD","reason":"UNSUPPORTED_TYPE"}
    attrs=_custom_attrs(variation.get("attributes",{}))
    size=attrs.get("サイズ","") or attrs.get("size","")
    color=attrs.get("カラー","") or attrs.get("color","")
    # Never assume English size/US9/EU42 equivalence without a verified map.
    if typ=="variable" and (not size or not color):
        return {"status":"HOLD","reason":"MISSING_SIZE_OR_COLOR"}
    candidates=[]
    for row in supplier_records:
        if _norm(row.get("shop_code")).upper()!="SP" or _norm(row.get("supplier_product_id"))!=supplier:
            continue
        if row.get("verified") is not True:
            continue
        if not _norm(row.get("merchant_variant_id")) or not _norm(row.get("source_url")).startswith("https://"):
            continue
        # If source row has an explicit Woo variation identity, it MUST match.
        # Existing archived fixtures lacking identity retain strict-text matching.
        evidence_vid = row.get("variation_id", row.get("woo_variation_id"))
        if evidence_vid is not None and str(evidence_vid) != str(vid):
            continue
        evidence_size = _norm(row.get("requested_size", row.get("size")))
        evidence_color = _norm(row.get("requested_color", row.get("color")))
        if evidence_size != size or evidence_color != color:
            continue
        # Shopify option1=8.5 is accepted for the owner-reviewed US 8.5
        # record ONLY when size format and exact Woo variation evidence exist.
        merchant_size = _norm(row.get("merchant_size", evidence_size))
        if merchant_size != evidence_size:
            if evidence_vid is None:
                continue
            allowed_size = _us_size_key(evidence_size)
            if allowed_size is None:
                allowed_size = _gs_size_key(evidence_size)
            if allowed_size is None or merchant_size != allowed_size:
                continue
        candidates.append(row)
    if len(candidates)!=1:
        return {"status":"HOLD","reason":"NO_VERIFIED_SIZE_COLOR_MATCH" if not candidates else "AMBIGUOUS_SUPPLIER_VARIANT"}
    chosen=candidates[0]
    return {"status":"CANDIDATE_ONLY","woo_product_id":pid,"woo_variation_id":vid,
            "shop_code":"SP","supplier_product_id":supplier,
            "merchant_variant_id":_norm(chosen["merchant_variant_id"]),
            "source_url":_norm(chosen["source_url"]),
            "size":size,"color":color,
            "reason":"EXACT_PRODUCT_AND_VARIANT_MATCH_LIVE_STOCK_PENDING"}

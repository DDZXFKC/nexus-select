"""Offline sourcing quality gate. Normalized evidence input only; no publishing."""
import argparse, csv, json, unicodedata
from datetime import datetime, timezone, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from statistics import median
from urllib.parse import urlsplit
from stage2_review import cost, COST_FIELDS, money

IDENTITY = ("brand", "style_code", "color_code", "size_system", "size", "condition")
COST_EXTRA = ("japan_shipping_jpy",)
def norm(v):
    return unicodedata.normalize("NFKC", v).strip().casefold() if isinstance(v, str) else ""
def identity(row):
    values = tuple(norm(row.get(k)) for k in IDENTITY)
    return values if all(values) else None
def positive(v):
    try:
        x = money(v)
        return x if x > 0 else None
    except (ValueError, TypeError, InvalidOperation):
        return None
def observed(row, now):
    try:
        u = urlsplit(row.get("source_url", ""))
        t = datetime.fromisoformat(row["checked_at"].replace("Z", "+00:00"))
        return (u.scheme == "https" and bool(u.hostname) and not u.username and
                t.tzinfo is not None and timedelta(0) <= now-t <= timedelta(hours=24)
                and row.get("price_status") == "OBSERVED" and positive(row.get("price")) is not None)
    except (ValueError, TypeError, KeyError, AttributeError):
        return False
def evaluate(candidate, offers, references, inputs, now):
    target = identity(candidate)
    result = dict(candidate_id=candidate.get("candidate_id"), decision="HOLD",
                  buy_price=None, currency=None, market_median_jpy=None,
                  matched_sales=0, matched_asks=0, ask_median_jpy=None,
                  profit_jpy=None, missing=[], rejected_references=0,
                  approved_for_import=False, review_ready=False)
    missing = result["missing"]
    if target is None:
        missing.append("identity")
        return result
    matches = [o for o in offers if identity(o)==target and observed(o,now)
               and o.get("role")=="PURCHASE_OFFER" and o.get("seller_verified") is True
               and o.get("stock")=="IN_STOCK" and o.get("stock_verified") is True
               and o.get("currency") in ("JPY","USD","EUR","GBP")]
    # Cost inputs must refer to one explicitly selected observed offer.
    selected = [o for o in matches if o.get("offer_id") and o["offer_id"]==inputs.get("offer_id")]
    if len(selected)!=1:
        missing.append("verified_purchase_offer")
    else:
        offer=selected[0]
        result.update(buy_price=str(offer["price"]), currency=offer["currency"])
    sales=[]; asks=[]; seen=set()
    for r in references:
        kind=r.get("role")
        rid=r.get("reference_id")
        if (identity(r)!=target or not observed(r,now) or r.get("currency")!="JPY"
                or kind not in ("COMPLETED_SALE","ASK") or not isinstance(rid,str)
                or not rid.strip() or (r.get("source_url"),rid) in seen):
            result["rejected_references"]+=1
            continue
        seen.add((r["source_url"],rid))
        (sales if kind=="COMPLETED_SALE" else asks).append(money(r["price"]))
    result.update(matched_sales=len(sales),matched_asks=len(asks),
                  market_median_jpy=str(median(sales)) if sales else None,
                  ask_median_jpy=str(median(asks)) if asks else None)
    if not sales:
        missing.append("completed_sales_reference")
    if len(selected)==1:
        try:
            if inputs.get("currency")!=offer["currency"] or money(inputs.get("price"))!=money(offer["price"]):
                raise ValueError("price mismatch")
            if inputs.get("cost_status")!="VERIFIED" or not inputs.get("cost_reference"):
                raise ValueError("unverified costs")
            if not all(k in inputs for k in COST_FIELDS+COST_EXTRA):
                raise ValueError("missing costs")
            if not sales:
                raise ValueError("no observed sales benchmark")
            # Conservative scenario: no assumed sale above the observed median.
            if positive(inputs.get("selling_price_jpy")) is None or money(inputs["selling_price_jpy"])>median(sales):
                raise ValueError("unsupported selling price")
            if offer["currency"]=="JPY" and money(inputs["fx_jpy"])!=1:
                raise ValueError("JPY FX mismatch")
            calc=cost(inputs)
            if not calc["profit_jpy"]:
                raise ValueError("incomplete costs")
            profit=money(calc["cost_jpy"])
            net=Decimal(calc["profit_jpy"])-money(inputs["japan_shipping_jpy"])
            result.update(cost_jpy=str(profit+money(inputs["japan_shipping_jpy"])),
                          profit_jpy=str(net))
            if net<=0:
                missing.append("positive_profit")
        except (ValueError,TypeError,InvalidOperation,KeyError):
            missing.append("verified_cost_or_sale_scenario")
    result["review_ready"]=not missing
    return result

def run(data, now):
    results=[]
    for item in data:
        try:
            results.append(evaluate(item["candidate"],item.get("offers",[]),
                                    item.get("references",[]),item.get("cost_inputs",{}),now))
        except (KeyError,ValueError,TypeError,AttributeError,InvalidOperation) as e:
            c = item.get("candidate") if isinstance(item,dict) else None
            results.append(dict(candidate_id=c.get("candidate_id") if isinstance(c,dict) else None,
                                decision="HOLD",error=type(e).__name__,approved_for_import=False,review_ready=False))
    return results

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True);p.add_argument("--out",required=True)
    a=p.parse_args()
    data=json.loads(Path(a.input).read_text(encoding="utf-8"))
    out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
    results=run(data,datetime.now(timezone.utc))
    (out/"sourcing_review.json").write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")
    keys=sorted(set().union(*(r.keys() for r in results))) if results else ["candidate_id","decision"]
    with (out/"sourcing_review.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(results)

if __name__=="__main__":
    main()

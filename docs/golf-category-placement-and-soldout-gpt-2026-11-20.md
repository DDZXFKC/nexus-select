# Owner 2026-11-20: SOLD OUT display + Golf category placement proposal (GPT)

Sources: `docs/owner-decisions-2026-11-20-soldout-golf.md` and `docs/owner-mandatory-storefront-purchase-flow-2026-11-19.md`.
Status: SOLD OUT **owner decided**; Golf placement **PROPOSAL, pending GLM/Claude design review and owner approval**. Site implementation is Claude's responsibility, not performed here.

## A. Owner-fixed stock policy vs storefront display

| Source state | Listing/catalog eligibility | Product card | Size selector | Purchase/inquiry control |
|---|---|---|---|---|
| At least one size observed in stock | Not blocked by inventory | Ordinary card (unless every size sold out) | OOS sizes marked SOLD OUT, available sizes normal | Stock-confirmation flow when implemented |
| All sizes observed out of stock | **Still listed** | SOLD OUT badge/text | Every known size SOLD OUT | No direct checkout; stock-confirmation request behavior must be aligned with approved final purchase-flow spec |
| Stock unknown / stale | **Still listed** | DO NOT assert SOLD OUT without evidence | Unknown state disclosed; no fake available flag | Verify at buyer inquiry and actual purchase |
| Product without any valid size records | Data integrity HOLD independent of inventory policy | No fabricated sizes | Missing-data handling required | Must not masquerade as zero-stock item |

- The display derives from a clearly labeled snapshot; it is *not* the final stock promise. Real stock, sourcing price and buyability must be checked on request and before purchase, per final owner flow.
- In ingestion/BUYMA batch3, `In stock?` copied into `colorsizes.在庫ステータス`; the generator must not drop zero-stock products. This is distinct from storefront display, which Claude must implement for desktop/mobile.
- Preserve old 1/2 batch reproducibility unless explicitly ordered otherwise.
- Avoid simultaneous contradictory messaging (SOLD OUT while a checkout/ADD TO BAG control promises immediate availability). Claude should define whether inquiry remains available under sold out, respecting owner mandatory `在庫を確認する` flow; no unauthorized decision on control redesign.
- No claim of real-time availability: lack of scheduled checks means stock is a historical observation.

## B. Golf category design candidates

### Recommended: existing 3-level gender hierarchy + golf thematic landing
Maintain core MEN'S / WOMEN'S / KIDS with gender → merch family → leaf categories. Add:
```text
MEN'S
  CLOTHING
    GOLF WEAR   [leaf]
  SHOES
    GOLF SHOES  [leaf]
  HEADWEAR
    GOLF CAPS   [leaf only if distinct inventory justifies]
  ACCESSORIES
    GOLF BAGS / GOLF ACCESSORIES [leaf only if verified stock exists]

WOMEN'S
  CLOTHING
    GOLF WEAR
  SHOES
    GOLF SHOES
  HEADWEAR / ACCESSORIES
    as warranted

KIDS
  future golf leaves ONLY when real eligible Kids products exist

GOLF [top-level marketing/navigation landing, not another taxonomic parent]
  MEN'S GOLF WEAR / WOMEN'S GOLF WEAR
  GOLF SHOES / CAPS / ACCESSORIES
```
GOLF is a landing/view layer reusing product memberships/tags, not a competing fourth-root taxonomic tree. Keep 3-level depth. If header top-level nav space is constrained, a GOLF entry can initially live in collections or a homepage campaign; **do not change approved header without owner authorization**.

### Classification rules
- Category source of truth is AFTER HOURS CLUB's approved brand × department × verified product type dictionary, not retailer categories. Store shop-category strings as lineage only.
- A golf product is NOT identified solely by brand; e.g. Nike, adidas or Malbon brand alone is insufficient for specific garment type. Require product-type or vendor/manufacturer product evidence. No unverified assignments by title keyword alone.
- Examples of candidate labels to investigate: `Malbon Golf`, `Eastside Golf`, `Nike Golf`, `adidas Golf`, `PUMA Golf`; these are examples, not verified inventory or category mappings.
- Golf polos, golf jackets and golf pants can all be children of a single `GOLF WEAR` leaf initially, with product-type filters in listings. Subdivide further only with enough actual products and owner approval.
- Prefer stable slugs proposed only (not implemented): `mens-golf-wear`, `womens-golf-wear`, `mens-golf-shoes`, `womens-golf-shoes`; use existing gender category paths for URLs, avoid assuming Woo hierarchy slug scheme. Update navigation, redirects, bread crumbs, filters and mobile menu only after review.
- A shoe that qualifies as both a sports performance item and a golf shoe should follow explicit multi-category policy (one primary merch family, verified golf thematic tag). Avoid duplicate Woo product creation.
- Keep source shop taxonomy separate from site categories and BUYMA categories. Site Golf navigation must not map into an invented BUYMA category ID; check approved BUYMA category master and E-1 preflight per actual product.

## C. Design alternatives / tradeoffs
A. **Recommended:** golf leaves under gender/merch family + one thematic GOLF landing. Pros: preserves approved Foot Locker style structure, supports clothing and footwear together; no extra DB, no duplicate product records.
B. Golf as category exclusively under CLOTHING. Simpler but hides golf shoes/caps; GOLF landing mitigates.
C. GOLF as a taxonomic fourth top-level parent. Not recommended at present: conflicts with established gender-first 3-level hierarchy and complicates breadcrumbs, filters and archive redirects.

## D. Review/acceptance conditions
1. Owner approves placement/nav visibility and final English labels; Claude determines UI presentation without violating established design.
2. Inspect current Woo category tree/slug collisions and actual inventory (all genders); do not create empty golf leaves in public nav if existing policy says show categories only with items.
3. Confirm product-type dictionary/evidence + BUYMA IDs separately, no assumption that Golf Wear has a single corresponding BUYMA ID.
4. Desktop/mobile: category listing, breadcrumbs, filters, SOLD OUT badge when all sizes OOS, size-level SOLD OUT, unknown stock behavior, no false checkout invitation.
5. Validation: a product from two shops has one site category decision; cross-shop source change does not change approved classification.
6. Do not introduce Golf classification or stock display changes into BUYMA batch3 during approved generator run unless specifically required.
7. Site category/UI implementation is **not authorized by this proposal**. No source/theme/category mutation performed.

## Separation of responsibilities
GPT: structure and data-classification proposal. GLM: final design assessment. Claude: site code and UI, after owner approval. Muse: actual Woo data and snapshot verification. Owner final decision overrides proposal.

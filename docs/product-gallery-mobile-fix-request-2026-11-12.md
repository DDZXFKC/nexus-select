# Mobile product gallery — fix request (2026-11-12, from user video)

Source: the user screen-recorded the live Local site on his iPhone
(2026-11-12 ~14:18 JST) and flagged two defects on the Timberland 6" Premium
Waterproof Boot product page (mobile). Both are reproduced below from the
recording and confirmed against the current theme code. A third item
(mobile home brand links) is bundled at the end.

## Defect 1 — the next image is visible before sliding

Recording: on the product page, a sliver of the NEXT gallery image is already
visible at the right edge before any swipe.

Cause (theme `style.css`, mobile breakpoints, two places — the generic block
around line 478 and the `body.single-product` block around line 622):

```css
.nexus-gallery { display:flex; overflow-x:auto; scroll-snap-type:x mandatory; gap:8px; }
.nexus-gallery a { flex: 0 0 88%; scroll-snap-align: start; }
```

Each slide is 88% of the container, so ~12% of the next image always shows.

Required: one image fills the visible area; no part of the next image is
visible before sliding. (Expected direction: `flex: 0 0 100%` and no
inter-slide gap showing through, in both blocks.)

## Defect 2 — the other color's images flow into the same slide sequence

Recording: the page is showing the Wheat boot; swiping moves through Wheat's
images and then the BLACK boot's images simply flow in, in one sequence.
The user: "黒流れてくる。これも修正" (the black ones flow in — fix this too).

Facts (verified from Store API + the page's variation JSON):

- The parent gallery contains all 6 images in one list:
  `10061713_01..03` (Wheat) followed by `11073001_01..03` (Black).
  `woocommerce/single-product/product-image.php` outputs featured + all
  gallery ids unfiltered.
- Variation → image mapping is correct: color `black` ↔ image stem
  `11073001` (13 variations), color `wheat` ↔ stem `10061713` (13 variations).
  So this is not a data-assignment error.
- The mu-plugin `nexus-variation-gallery.php` (NEXUS Variation UX Sync) only
  scrolls the stack to the selected variation's image and highlights it; it
  never hides the other color's images. On the mobile horizontal snap row,
  swiping therefore traverses both colors.

Required: the slide flow contains ONLY the selected color's images.
Switching color replaces the visible set and resets to that color's first
image. Desktop's stacked layout already groups by color blocks, so keep its
behavior consistent with this rule.

Grouping signal available in the data: a color's images share the
style-number stem of that color's variation lead image (e.g. `10061713_01`,
`_02`, `_03`). If a more data-true grouping exists (attachment metadata
etc.), prefer it over the filename convention and state which was used.

## Defect 3 — mobile home "SHOP BY BRAND" is plain text links, left-aligned

User report (2026-11-12 14:11 JST): at the bottom of the mobile home, the
BRAND links are still text and left-aligned. Markup: the
`nexus-pc-brand-index` block renders 8 text links (Nike, ASICS, Jordan,
Patta, adidas, New Balance, Carhartt WIP, Vans). The PC home has the adopted
12-brand logo marquee. Request: give the mobile brand section the logo
treatment consistent with PC (or state explicitly if it is intentionally a
separate text index, in which case fix at least the alignment).

## Return / verification

- Ship the patch as one batch (theme CSS and/or mu-plugin), with the usual
  one-shot execution notes if any iMac-side step is needed.
- Muse will apply it to Local, verify the served HTML/CSS via the Live
  Link, and the user will confirm on his iPhone at the real viewport
  (sliding behavior can only be judged there).

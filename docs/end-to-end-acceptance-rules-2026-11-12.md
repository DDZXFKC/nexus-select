# Goal-first acceptance rules
Define the user-visible outcome first, inspect current code and dependencies, prepare changes and regression tests in one batch, execute, inspect actual outputs, fix failures, repeat until acceptance. Do not report completion on unit tests alone. No user relay.

## Site acceptance (Local only)
Use actual browser interactions on desktop and mobile viewport, including real iPhone confirmation where available. Verify home brand logos and destinations, navigation, image edges and overlap, one full image per swipe, selected-color-only gallery through every image, color switch resets to first image, size selection, cart and test checkout. Verify desktop sticky product information and mobile single column. Preserve existing products/orders; no production changes. Capture evidence and exact blockers; do not claim device verification without it. Product page changes require user authorization where applicable.

## Collector acceptance
Use saved five-page manifest, fresh test DB and output. Verify actual exported rows, 51 variants, 5 merchant-page products, Notre 26/26 names, no cross-shop/color merge, preserved variant SKU/size, HOLD and published=0. Inspect WooCommerce/BUYMA output contents and counts, not just unit tests. Fix and rerun failures. Never publish or import.

## Reporting
Report completed verified outcomes and unresolved blockers only. Bundle dependencies, code, tests and execution instructions together. Do not ask the user to transfer messages. No Grok. No production WooCommerce changes.

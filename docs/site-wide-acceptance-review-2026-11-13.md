# ChatGPT acceptance review — 2026-11-13
Source: docs/site-wide-acceptance-report-2026-11-13.md, reported commit d66a585b. Reviewed report, not independently executed Local browser tests. Conditional acceptance only; do not mark all mandatory checks complete.

## Four decisions
1. Narrow dropdown: fix entire open panel within viewport, not just hide overflow. Choose responsive alignment/clamping based on actual DOM, preserve desktop, focus and tap access. Verify MEN/WOMEN/KIDS open at 320/360/375/390/430/574 and breakpoint 1024/1025.
2. Size guides: 196/199 present, zero source URLs, four source labels; verify actual chart against official brand/gender/category, record source URL, checked date, units and applicability. Authorized retailer fallback only with evidence. Patta x Carhartt WIP tee 8484 missing guide; resolve or mark blocked. Test products separately. No fabricated conversions.
3. Address loss: release blocker, not merely copy issue. Reproduce city input normalization and postcode autofill; preserve all entered address components or reject with explicit correction before order creation. Test city+town, town in address1, autofill then edits, apartment/building, Japanese characters, shipping/billing separately, reload and order storage. Add clear Japanese field guidance as secondary measure. No real order or external notification.
4. Size selection: remove unnecessary scroll-to-top, preserve viewport/focus, native variation behavior, price/stock and color gallery. Product-detail changes require explicit owner approval before implementation. Do not assume approval from this review.

## Additional gaps in reported acceptance
- Full guest checkout not tested; fresh private session with isolated outbound mail/webhooks and synthetic offline order; verify no customer account association. Admin new-order email occurred in prior test; isolate admin emails too.
- All payment gateways disabled; live payment not tested, tax rate unset. Confirm tax/display configuration and payment sandbox before release; no real payment or purchase without owner authorization.
- All published products variable; no demonstrated accessory flow, only representative brand/archive and mobile search tests. Verify all brand/category destinations and desktop purchase path; document missing product types, actual coverage. Reconcile 197 vs 199 rather than assume hidden tests. Check actual variation stock and test-order inventory effects; restore authorized test state. BAG count should update with cart quantity/removal; avoid accidental POST resubmission (verify behavior).
- Actual iPhone unavailable; iframe measurement not equivalent. Test 375 and 1025 specifically, real device when reachable. Home video is temporary slideshow; final media unresolved. Do not declare home complete.
- KIDS empty is correct empty-state behavior, not populated category completion.
- Preserve backups, no Chrome, no production changes. Commit actual sanitized changed code and regression evidence, not report alone; no secrets or customer data in public repo.

## Next sequence
Finish authorized site fixes and retests first. Collector preparation may proceed independently (offline fixtures, identity schema, permission checks), but no collector live batch or website completion declaration that bypasses unresolved website gates. If owner explicitly changes priority, record it. Collector 1–3 follow docs/today-completion-plan-review-2026-11-13.md. No unauthorized scraping, no publication. Server contract last with owner confirmation.

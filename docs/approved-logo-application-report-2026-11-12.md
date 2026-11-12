# Approved mobile logo batch — Local application report (2026-11-12, Muse)

Scope: apply the approved-logo batch to Local only. No product data, orders, product pages, or production were touched. Final logo candidate was NOT decided (per placement note).

## Source commits (integration/grok-review)
- 32f8a2c4 "Support approved transparent mobile homepage logo without font substitution" — header.php
- 83d21f5a "Place approved logo over existing mobile campaign when poster exists" — header.php
- dc0d12ea "Center original cutout logo in mobile homepage header" — style.css
- 3a9554f0 "Record exact approved logo placement and local acceptance checks" — docs/approved-mobile-logo-placement-2026-11-12.md (note only)

## Applied changes
- header.php (2 edits, applied in final combined form):
  1. Before the mobile home header tag: compute $nx_logo_id / $nx_logo_url from theme mod `nexus_mobile_approved_logo` (PNG attachments only) and $nx_logo_overlay from theme mod `nexus_mobile_poster` (large image). Header tag gains `nx-home-mobile-header--logo-overlay` only when both logo and poster exist.
  2. Logo anchor: renders the approved PNG (alt "AFTER HOURS CLUB", max-width 100%) when a logo is set; otherwise falls back to the existing text logo "NEXUS SELECT". No font substitution or generated logo is used.
- style.css: appended the approved-logo block at the end (mobile homepage only, max-width 1024px): header grid 88px/1fr/88px when an approved logo is present, logo width min(100%, 240px) centered, overlay header transparent with white foreground, admin-bar offsets.

## Backup / rollback
- Backup: /Users/discodadz/nexus-run/theme-backup-2026-11-12-logo/{header.php, style.css} (pre-application state: header.php 10,949 bytes, style.css 41,546 bytes).
- Rollback: copy those two files back over the theme files. Nothing else was changed.
- Post-application sizes: header.php 11,670 bytes; style.css 42,300 bytes.

## Verification (all read-only checks after application)
- PHP lint (Local PHP 8.2.29, disposable harness via Live Link, harness moved to Trash afterwards): "No syntax errors detected" for header.php.
- Live Link home HTML: mobile header renders without overlay class and without approved-logo class; logo falls back to text "NEXUS SELECT" (expected: no logo attachment set yet).
- Served style.css: 42,300 bytes, contains the approved-logo block, brace balance 0.
- Safari (kaitsuke-shop.local), window width 574px: mobile home header renders as before — menu left, centered text logo, search and bag (count badge 2) right; no overlap or overflow. Hero area remains blank (no poster/video asset — known blocker, unchanged).
- Safari, width 1025px: PC home unchanged.
- Safari, /shop/ and one product page at 574px: mobile home header absent; standard header only (home-only scope confirmed).

## Blockers / outstanding (not claimed complete)
- Logo PNG files are not yet available locally: after-hours-brush.png (965x129) and after-hours-minimal.png (1068x134) exist only inside the ChatGPT conversation per the placement note; they are not in this repository. A broad filename search on the iMac (after-hours*, IMG_669*) timed out with partial coverage and found nothing, so the candidate set/compare step could not run.
- Poster (nexus_mobile_poster) is not set, so the overlay state could not be visually verified. Per the note, the homepage is not declared complete while the poster is missing.
- Widths 320/390/430 could not be reached in Safari on this Mac (window minimum 574px); real-iPhone confirmation is also outstanding.
- Next step once the exact PNG files are accessible: upload both to the media library, set theme mod `nexus_mobile_approved_logo` to each in turn on Local only, capture both at the same position, and report — without deciding the final candidate.

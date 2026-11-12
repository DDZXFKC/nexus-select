# Approved Brush Italic logo — Local installation report (2026-11-12, Muse)

Final selection (recorded in f83ec3c3): Brush Italic adopted, Minimal Spaced not selected.

## How the file arrived
- The extracted PNG could not be transferred from ChatGPT to GitHub (binary transfer blocker, recorded in b04d82a8). The shared OpenAI link resolved to a placeholder image, not the logo.
- The user sent after-hours-brush.png directly to Muse in chat on 2026-11-12.

## File verification (pixel-measured, not visual impression)
- PNG, 965 x 129, RGBA, 21,586 bytes.
- Structure: solid white rectangular box with the lettering cut out (transparent). Corner pixels (all four) are fully opaque (alpha 255): the box corners are exact 90-degree angles, no rounding. The user explicitly required square 90-degree corners.
- Opaque pixels are pure white only; transparent pixels form the AFTER HOURS CLUB brush lettering.
- Note: an earlier interim reading of this file by Muse was reversed; the pixel measurements above are the verified result.

## Installation (Local only)
- Transferred to the iMac and registered in the media library: attachment ID 18898, URL /wp-content/uploads/2026/11/after-hours-brush.png.
- Theme mod `nexus_mobile_approved_logo` set to 18898 via a disposable PHP harness (harness moved to Trash after use).
- Home HTML now outputs the logo image (alt "AFTER HOURS CLUB") in the mobile home header. Theme CSS contains no border-radius that would round the logo.

## Display verification (Safari, kaitsuke-shop.local, window width 574px)
- Mobile home header renders with the approved-logo link present; menu left, search and bag (badge 2) right; no overlap.
- Current limitation: the campaign poster (theme mod `nexus_mobile_poster`) is still not set, so the white box sits on the white header and the logo is effectively not visible yet. Per the placement note, the homepage is NOT declared complete while the poster is missing.
- Outstanding: poster/video asset, real-iPhone check, and visual confirmation of the logo over an actual campaign frame.

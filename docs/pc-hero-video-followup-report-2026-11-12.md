# PC hero video follow-up report — 2026-11-12

Applied commit a2f70f20 (front-page.php playback hardening) to Local (kaitsuke-shop), per docs/pc-hero-video-followup-2026-11-12.md. Owner approved the application in chat before it was applied. Local only; no production, no product edits, no Chrome.

## Local comparison and backup
- Local front-page.php matched the patch's pre-image exactly for all three hunks (update(), playing listener, IntersectionObserver line), so the patch was applied as-is via three anchored replacements.
- Backup of the pre-change file: /Users/discodadz/nexus-run/theme-backup-2026-11-12-harden/front-page.php
- Existing design, mobile media, temporary reference placement and approved logos were not touched. Current hero media setting (nexus_pc_hero_video = 18909, the owner's reference-photo slideshow for Local checking) was left as-is and used for playback verification instead of swapping in a synthetic test file.

## Verification (Safari, real display)
- PHP lint: front-page.php, no syntax errors.
- Width 1280: hero video plays (toggle shows 動画を停止 / PAUSE). No overlap with hero text.
- Resize 1280 -> 574 during playback: page switches to the mobile homepage; the desktop video and its toggle are gone from the accessibility tree and the mobile poster + approved logo render normally. No desktop video visible at mobile width.
- Resize 574 -> 1280: desktop hero returns and playback resumes (toggle back to 動画を停止).
- Not covered in this pass: exact 1024/1025 boundary widths (Safari window minimum width in this setup snaps to 574/1280-class sizes), prefers-reduced-motion, and invalid-media fallback. These remain unverified, not passed.

## State after work
- Theme setting unchanged: nexus_pc_hero_video = 18909 (reference slideshow, Local checking only, not for publication).
- One-off PHP harnesses moved to Trash.
- Final licensed campaign footage is still required. The website-first instruction sheet (docs/website-first-completion-2026-11-12.md) has not appeared in either branch as of this report; work is proceeding from the text the owner pasted in chat.

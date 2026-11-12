# PC hero video application report — 2026-11-12

Applied to Local (kaitsuke-shop) from commits 8d618c66 (front-page.php) and 45572949 (functions.php), per runbook docs/pc-hero-video-runbook-2026-11-12.md. Local only; no production, no product edits, no Chrome.

## Backup
- front-page.php and functions.php copied to /Users/discodadz/nexus-run/theme-backup-2026-11-12-pchero/ before editing.
- Theme mods before: nexus_pc_hero_image=18882, nexus_pc_men_image=18883, nexus_pc_women_image=18884, nexus_pc_hero_video=0, mobile mods unchanged (poster 18903, mens 18904, womens 18905, kids 18906 — temporary reference placement), approved logo 18898.

## Changes applied
- front-page.php: nexus_pc_hero_video read + MP4 MIME check + poster URL; video element (hidden, muted, loop, playsinline, preload=none, data-src) with PLAY/PAUSE toggle; hero image alt and eyebrow changed to AFTER HOURS CLUB; inline playback script (desktop >=1025px only, reduced-motion aware, IntersectionObserver pause, error fallback).
- functions.php: Customizer section renamed to AFTER HOURS CLUB — PCホーム素材; new media setting nexus_pc_hero_video (mime_type video) added.
- Mobile markup and all other sections untouched. Approved logo and mobile mods preserved.

## Verification
- PHP lint: both files, no syntax errors.
- Test MP4: generated locally (ffmpeg testsrc, 4s, 1280x720, H.264 yuv420p, no audio), registered as attachment 18907, set as nexus_pc_hero_video. Note: first registration attempt hit a fatal in wp_generate_attachment_metadata (wp_read_video_metadata undefined) because media.php was not loaded; attachment 18907 had been created, metadata was regenerated with media.php loaded and the mod was set. No other data affected.
- HTML: video element present with data-src pointing to the test MP4 and poster = existing hero image (18882).
- Safari (desktop width 1280): test video actually played in the hero (test pattern visible), eyebrow reads AFTER HOURS CLUB, PAUSE button shown at bottom right, no overlap with hero text. Toggle click paused playback and the button label switched to 動画を再生 (PLAY). SHOP NOW link and page sections intact.
- Not verified in this pass: widths 1024/1025 boundary behaviour and mobile-width network behaviour (video uses data-src + preload=none, so no MP4 is fetched until the desktop script activates it; mobile visual check still outstanding along with the pending mobile reference placement check).

## Cleanup
- nexus_pc_hero_video removed (back to 0). Test attachment 18907 deleted. Existing poster (18882) preserved. Home HTML confirmed back to static hero (no video element).
- One-off PHP harnesses moved to Trash.

## Remaining
- A licensed final campaign MP4 is still required (see docs/ahc-seasonal-campaign-video-direction-2026-11-12.md and docs/ahc-video-source-candidates-2026-11-12.md). No final campaign selection or publication authorized.
- The hero now supports ONE desktop MP4. The owner's "about 3 videos" idea would need a further design (rotation or playlist) — not included in this implementation.

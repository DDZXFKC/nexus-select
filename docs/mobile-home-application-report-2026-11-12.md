# Mobile home implementation — Local application report (Muse, 2026-11-12)

Instruction followed: docs/mobile-home-implementation-2026-11-12.md
(commits 9a181849, 43c8ff36, ddc9edda, debd68ff).

## Done and verified

- Reconstructed the three theme files from the GitHub patches in commit
  order; all four patches applied with zero rejects (the local clone matched
  the repo parent state exactly).
- Backup BEFORE applying: full theme copied to the iMac at
  /Users/discodadz/nexus-run/theme-backup-2026-11-12-mobilehome/nexus-select/
  (24 files; MD5s of the three replaced files recorded in mh-apply.log and
  matching the pre-change state).
- Applied to Local (themes/nexus-select/): front-page.php (10,645 B),
  functions.php (5,186 B), style.css (39,697 B). MD5s on the iMac match the
  reconstructed files byte for byte.
- PHP lint (Local's PHP 8.2.29): no syntax errors in front-page.php and
  functions.php.
- Live Link was down (all-404) at start; revived by a Local site
  stop/start + Live Link re-enable, then verified:
  - Home returns 200, no PHP errors.
  - New mobile campaign block is served: BEYOND BORDERS /
    "ENJOY FASHION. ENJOY LIFE." / 好きな服で、毎日をもっと楽しく。 /
    SHOP NOW → /shop/, with the lazy-load video script (data-src, PLAY/PAUSE
    control, reduced-motion and off-screen handling).
  - Served style.css MD5 equals the new file.
  - Mobile segment contains NEW ARRIVALS with product links, WOMEN/KIDS
    sections, and SHOP BY BRAND with 12 brand links (previously 8 text
    links).
  - PC regression: the desktop home block (nexus-pc-home) is still present
    in the served markup; PC branch untouched per the patch contents.

## Not done — blockers, exactly

1. Media assets do not exist yet (as the instruction doc states): no poster
   image, no finished MP4, no category images in GitHub or on the iMac.
   Result on the live page: the campaign film frame (nx-mobile-film) is
   EMPTY — no <video> is emitted until the Customizer settings
   ("NEXUS SELECT — モバイルホーム") have a video/poster. Per the
   instruction, the page must not be treated as publishable until the
   assets are set.
2. Header diff (menu / centre logo / search / bag to match the approved
   sample) is not part of the committed implementation — header.php was not
   touched by the four commits. Still open as an implementation item.
3. Real-device verification (iOS Safari / Android Chrome at 320–1025 px,
   video failure behaviour, stop/resume, cart flow) is NOT done: Muse's
   browser environment cannot reach the Live Link subdomain at all (proven
   repeatedly on 2026-11-12), so these checks need the owner's iPhone pass
   or another reachable route. Markup-level checks above are what was
   actually exercised; no device claim is made.
4. Grok's review of the implementation is still outstanding (his channel
   is via the owner; Muse will transcribe).

## Notes

- Temporary harness nx-mh.php remains in the site root for the follow-up
  checks; it will be removed with the other session harnesses once the
  current batch settles.
- Product detail pages were not touched, per instruction.

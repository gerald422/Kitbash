**Review of the project's position (Nov 13) and the repo-only fixes from it (Josh: "go ahead with 1, 2, 3 and 5").**

Why: before the origins-at-the-joint work, check what is outstanding and what would go wrong the first time the repo
is cloned on the PC. Nothing on the PC changed; no installed file changed (`tools/installed.json` as it was).

- **1. Eight sidecars were tracked twice, as `Arms/` and `arms/`** (Marta: Hooded models x3, Lion Knights, Heavy
  Flying x2, Eliminators x2). Linux keeps both, the PC's disk has one folder, so a Windows clone keeps one of each
  pair at random. Five pairs differed: the `arms/` copies were from Nov 5-6, before the Nov 8 pad fix (their Pad
  socket still `tiow_anchor: copied`), so `sync_sidecars.py import` from such a clone could have put the old pad
  seats back. Removed: the five old `arms/` copies; for the three identical pairs, the copy whose case
  `_sources.csv` doesn't use. 6,887 sidecars now, one per `_sources.csv` row. `validate.py` refuses two tracked
  paths that differ only by case. One folder pair still differs only by case (Hooded models: `Arms/` with the 3
  pad-fix arms beside `arms/` with 30 files): no file collides, so they are one folder on the PC.
- **2. Line endings.** `.gitattributes` only covered `*.bat`, so Git for Windows' usual setting would turn the 5,877
  LF sidecars and every script into CRLF in a clone: `kb.py verify` (md5 of the clone's file against the installed
  one) would report every text file as different, and an import would rewrite sidecars. Now `* -text` (no
  conversion anywhere; `*.bat` still CRLF). A clone made before this should be made again.
- **3. The validator checked less than it said.** Added: `squad-builder/build_page.py --check` (the page equals what
  `src/` builds; it did); the `_sources.csv` row per sidecar the docstring promised (and no part listed twice);
  `tests/kb/t_kb.py`, 50 checks with no Blender: `merge` keeps clicked / copied / auto anchors, corrected sockets,
  held spots, `exact` fits and their notes, variants, old-only keys, and doesn't touch its inputs; `load` / `save`
  keep LF / CRLF / final newline / escaped files byte for byte; a `kb.deliver` package goes through
  `kb.py apply --check`, apply (contents, backups), a second apply (no-op), and is refused when a file changed on
  the PC, a "new" file is already there with other contents, or the payload is damaged. Each new check was seen to
  fail on a deliberate break (an anchor kind taken off the keep list, a `readme.md`, an unbuilt css edit).
- **5. `CLAUDE.md`** said bionic legs were "on hold"; now abandoned, as `OPEN.md` and the README say.
- **Not done, in `OPEN.md`**: 4. `share_server.py` accepts `/correct` and `/send` from any site (no `Origin` /
  `Content-Type` check): a page open in the owner's signed-in browser could post a fit and have it marked `exact`.
  It needs the tunnel address, and the daily backup and corrections log would show it; the fix is small but changes
  an installed file, so it goes with a delivery and a sharing restart.
- **Position**: `main` = installed (TIOW Inbox 1.17.8, Finalise 0.3.3). No `golden.json` yet, so there is no
  placement baseline; record it before origins at the joint. Corrections so far: 16 sidecars with `exact`, 2 with a
  corrected socket. Fit coverage by type is in `OPEN.md`. No open pull requests; CI (`validate`) passed on the
  fixes commit `ccc081f`. Pushed to the session's branch, not `main`: it needs merging.

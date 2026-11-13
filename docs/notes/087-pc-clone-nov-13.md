**The repo cloned on the PC (Nov 13), and the two things the first clone turned up.**

Why: `OPEN.md` has waited since Nov 10 for a clone on the PC so `Run checks.bat` can run there. Pull request 1 (the
Nov 13 review fixes, notes 086) was merged to `main` as `c8d2d81`; this is the first clone made from it, by a session
running on the PC.

- **Where**: `~\Desktop\TIOW Blender bridge\Kitbash` (inside the bridge folder, which had no clone and is not itself a
  repo). `main` at `c8d2d81`, clean status, `git fsck` clean. Moving it is moving the folder.
- **Long paths.** A plain `git clone` there stops with "Filename too long" on 9 sidecars (Marta Eliminators,
  `phoBOIS with cloak`): the longest tracked path is 230 characters and the clone's own path adds 51, past Windows'
  259. The PC has long paths switched on (`LongPathsEnabled` 1), but Git for Windows needs its own setting:
  `core.longpaths true`, set in this clone's config only, then `git reset --hard`. All 7,723 files are there. A new
  clone: `git clone -c core.longpaths=true ...`, or clone somewhere short (under `C:\Kitbash\` every path fits).
- **Line endings** are as notes 086 intended: every file byte for byte, only the 8 `.bat` files CRLF.
- **`tools/validate.py` crashed on the PC** (`UnicodeDecodeError`, then `'NoneType' object has no attribute 'split'`):
  `git()` read git's output with the Windows code page (cp1252) and `ls-files -z` prints the library's paths as UTF-8
  (byte 0x81 is in one of them). CI and the container are UTF-8, so it never showed there. Now `encoding="utf-8"` on
  that call. Passes on the PC with the default code page: 6,887 sidecars, 7,723 tracked files, kb tests pass.
  `Run checks.bat` runs this, so its "-- repo" section would have been a traceback.
- **`kb.py verify`: 17 of 18.** The bridge folder's `_library.json` was the Nov 9 one (`c43457c7`, exactly the repo's
  file at `8b99b05`, so not edited by hand); `main` has had `a38086ba` since Nov 10 (`9603b58`: the Wings and Wing
  Mounts joints, Loincloths moved after the belt types; no part type changed, so TIOW needs no re-patch).
  `kb.py install pc-clone-2026-11-13 _library.json`: installed, md5 matches, old copy in
  `_backups\pc-clone-2026-11-13\before\bridge\`. Verify now 18 of 18. `tools/installed.json` unchanged (it lists
  the file already).
- **Not done**: `Run checks.bat` itself (the golden run in Josh's Blender is still untested) and
  `Run checks.bat record`, which is Josh's to run when the builder looks right. `gh` is not on the PC; plain `git`
  reaches the repo.

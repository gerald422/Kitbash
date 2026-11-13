# Reference: how the work is done

## The PC (device tools)

Roots (print them with `python3 tools/kb.py roots`): library `D:\Kitbash Library`, maker downloads `D:\new cults`,
bridge `~\Desktop\TIOW Blender bridge` (page in its `Squad Builder\`), Blender add-ons
`~\AppData\Roaming\Blender Foundation\Blender\5.1\scripts\addons`, TIOW `~\AppData\Local\TIOW-FTRP`.
In the device shell they appear under `~/mnt/...` (`~/mnt/d`, `~/mnt/Desktop`). A new session has no folders
connected: ask once with `device_request_folder_access`. `device_bash` stops at 45 s: start long jobs in the
background with a log file and poll it.

Josh's working blends: `Desktop\query.blend` (corrections), `Desktop\Operation Marine\*.blend` (large),
`Desktop\example issues.blend`. Josh has a Blender MCP server, so his live Blender can be used; he restarts Blender
after an add-on change.

## A session running on the PC itself (Claude Code in the clone)

Since Nov 13 the repo is cloned at `~\Desktop\TIOW Blender bridge\Kitbash` and sessions run there. Then none of the device
tools, staging or `device_commit_files` below apply: the roots are real paths (`python tools/kb.py roots`), the
library is read and written in place, and installed files are delivered with `python tools/kb.py install <task>
[names]` (backs up, md5-checks) after adding them to `tools/installed.json`.
- Python: the system `python` has no numpy; use Blender's (`C:\Program Files\Blender Foundation\Blender 5.1\5.1\python
  \bin\python.exe`) for numpy work, `blender --background --python` when `bpy` / `mathutils` is needed (add
  `--factory-startup` unless his add-ons are wanted: several print errors in background mode). Set `PYTHONUTF8=1`.
- Blender tests: `blender --background --python tests/golden/run.py -- "D:\Kitbash Library" [--only ...]` (25 s for
  all 140 parts). His live Blender is also reachable through the Blender MCP server.
- D: is exFAT: no long-path trouble for Python (long paths are on), but tools that need NTFS features refuse it
  (Caliper's batch: notes 088). Keep such work folders in the temp folder on C:.
- The bridge folder's old `old-*` / `sidecars-*` / `library build` folders are in
  `~\Desktop\TIOW Blender bridge archive\` (history only).

## Where to run

1. **On the PC** (first choice): Python there sees the real library, so no staging, no 7-level limit, no chunking.
   Surveys, sidecar builds, index updates, `kb.py verify`, the golden run in his Blender.
2. **In the container**: only when Blender must run here. `tools/setup_container.sh` (bpy 5.1.2 venv, add-ons, the
   old working paths the historical scripts expect). Stage the few files the task needs; files deeper than 7 folder
   levels below a connected folder go in a tar first. ~44 GB disk: delete your own old outputs if it fills.

## Delivering (always the same)

    from kb import deliver
    d = deliver.Delivery("<task>-<date>", out_dir); d.new(...) / d.replace(...) / d.append(...) / d.copy(...)
    files = d.build()

`device_commit_files` them into `<library>\_backups\<task>\deliver\` (a new path every time: re-committing to a used
path has delivered stale copies), then on the PC `python3 kb.py apply <dir> --check`, and again without `--check`.
It refuses if a file changed since the work started (Josh edits `_hidden.txt` from the page), backs up to
`_backups\<task>\before\`, writes, and md5-checks. Makers' STLs are copied PC-side (`d.copy`), never through here.
Afterwards update `tools/installed.json` if a listed PC-only file changed (`kb.py record` on a clone that sees the PC).

## The page index

`kb.index.Index.load(path)`; `update_part(path, sidecar)` for changed parts; `add_parts(entries)` with entries from
`build_index.build(<small folder with the new files and a _sources.csv>)` plus their previews; `dumps()` writes it
back in the form Prepare left it. Previews need `fast_simplification` (pip) or they come out holed. New rows are
appended to `_sources.csv` with CRLF.

## Sidecars

`kb.sidecar`: `load` / `save` keep each file's own newline style; `merge(new, old)` is the only way to change an
existing one (it reports what of Josh's it kept); `problems(d, types)` before writing. Export the PC's sidecars into
`library/` with `library-tools/sync_sidecars.py export "D:\Kitbash Library" library` before a commit.

## Josh's corrections in a blend

`kits/corrections/query-*`: list the parts (`list_src.py`), rebuild the same model with TIOW and compare each part
with his relative to the torso (`rebuild.py`), so TIOW's own rock / settle / base rise isn't taken for his moves;
save with TIOW's `correct_socket` / `correct_part` (`both=False`, `folder=False`); rebuild to confirm 0.00 mm.

## Tests

- After a change: `tests/golden/run.py --only <the models it can touch>` plus a task test on the affected parts
  (`tests/<task>/t_*.py`), and the page tests for the steps touched (`squad-builder/test/t_*_step.js` against a
  served test library).
- `tests/kb/t_kb.py` (no Blender, a second; `validate.py` runs it): `kb.sidecar.merge` keeps clicked / copied / auto
  anchors, corrected sockets, held spots and `exact` fits; load / save keep a file's bytes; `kb.py apply` refuses
  files changed on the PC and backs up what it replaces. Add a check there when `kb/` gains a promise.
- Everything: Josh runs `Run checks.bat` (installed files, repo checks, all golden squads). `record` re-saves the
  reference; do it only when the placements are right.
- Prefer numbers to pictures: gate on distances, send a sheet to Josh, look at one yourself only for a new frame.

## The add-on

`addons/tiow_inbox.py` is what gets delivered. Edit `addons/tiow_inbox_src/NN_*.py` (find the function in
`INDEX.md`), run `tools/build_addon.py`, bump `bl_info` version, deliver to `addons` and `bridge` (old copy to
`bridge\old-<version>\` is no longer needed: apply backs it up).

## TIOW Inbox versions since 1.17

- 1.17 squads from the page (model + socket per request); 1.17.1 the page writes into `<library>\_builder\inbox`;
  1.17.2 bases rise to the feet, Save Correction (Fix the Part -> fit + `exact`; Fix the Socket -> host socket,
  `tiow_corrected`).
- 1.17.3 a corrected socket is trusted: belt bits on it aren't rocked, only settled.
- 1.17.4 `Loincloths` type, the only one on Belt Front; belt bits on Hip R/L and Belt Back.
- 1.17.5 `Wings` bring their connector (`Wing Mounts`): the wing's sidecar `adaptor` (library path) goes on the
  pack's `Wing Mount R/L`, the wing hangs from the connector's `Wing R/L`; a request for a socket the model hasn't
  got yet keeps its side.
- 1.17.6 hip plates and the buckle host parts: `Hip Plates` on the legs' `Plate R/L` (right = mirror variant),
  `Plate Accessories` (holsters/sheaths) on the plate's `Plate Hang R/L` (bring the plate), `Buckles` on `Buckle`,
  `Tabards` on the buckle's `Tabard` (bring the buckle), `Trophies` on `Trophy R/L` first. Legs with the spots: Mar Fil Assault (16), Intercessor (25 + mirrors),
  Techmarine (4), all Turtle Ninja (465).
- 1.17.7 `Chest Equipment` on the torso's `Chest Equip R/L` (right = mirror variant), `Neck Guards` on `Neck Guard`; only
  the Old Style Space Knight MK8 torsos have the spots. Page steps Neck guard (6), Chest equipment (7).
- 1.17.8 `Chest Inserts` on the torso's `Chest Insert`; only `MarFil Assault - Torso 2 Insert` (Josh's cut of Torso 2) has it. Page step
  Chest insert (8).


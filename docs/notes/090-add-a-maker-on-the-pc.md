**Add-a-maker runs on the PC: one command, a recipe per maker, "Add parts.bat" (Nov 13; item 1 of the order in notes 089).**

Why: `kits/creator/add_creator.py` only ran in the container (staged archives, `/home/claude` paths, a bpy venv with
scipy / PIL / fast_simplification). Sessions now run on the PC, and Josh wants to add a maker's new parts himself.

- **How it runs there.** Inside the installed Blender, which has all it needs:
  `blender --background --factory-startup --python kits/creator/add_creator.py -- add RECIPE [--src FOLDER] [--dry]
  [--yes] [--force] [--no-open] [--no-record] [--task NAME]`, `finish TASK`, `recipes`. Nothing is downloaded or
  installed: no scipy (the matching searches with Blender's `mathutils` KD tree), no PIL (the sheet's labels are
  Blender text, the two views stay two PNGs; the test's renders stay one PNG a view), no fast_simplification (previews
  by Decimate, as Prepare makes them on the PC). The container commands (`unpack`, `go`, ...) are unchanged.
- **What `add` does**: survey in place (`on_pc.survey`, roots from `tools/kb.py roots`) -> plan, leaving out every
  file whose source path is already in `_sources.csv` ("nothing new" ends the run and removes its own task folder) ->
  the new files with mesh faults listed (`caliper_swap.py`'s test; for Caliper Repair afterwards) -> sheet -> fit ->
  three test marines through the installed TIOW Inbox -> asks -> build (index updated in place, previews) ->
  `on_pc.apply --check`, then apply (lists backed up in `_backups\TASK\before`) -> `record` into the clone. Work
  files in `D:\Kitbash Library\_backups\TASK\work`. A failed test check is shown and asked about (Pad 11 / 13 style
  cuts go in and are put right with Save Correction); with `--yes` it stops unless `--force`.
- **Recipe** = the per-maker config that was already there (`kits/creator/<maker>.json`); `--src` gives the folder of a
  new drop (inside `D:\new cults`), the task name is `<recipe>-<date>[-n]`. Only `wargame-exclusive` exists: each
  other maker needs one written from its file names the first time (a file no type matches stops the plan).
- **`Add parts.bat`** (repo root, runs from the clone): drop the folder, pick the recipe by number, the sheet and
  test pictures open, answer Y.
- **`kb/fit.py`** (new): the head and pad rules lifted from `kits/rw_spr/common.py`, `heads.py`, `pads.py` (same
  numbers, same seeds), library root passed in. **`kb.geo.kdtree`**: scipy's cKDTree, or `_BlenderKD` with the same
  `query` / `data`. Changed for the PC only where they had to: `kits/creator/on_pc.py` (`set_roots`),
  `kits/wg/padlift.py` (roots as arguments), `kits/creator/sheet.py`, `tests/creator/t_creator.py` (on the PC the
  installed add-ons through `read_homefile` + `addon_utils`, as the golden run; its test inboxes are put back).
- **Tested** (no change to the real library). (1) Dry run of the WarGame Exclusive recipe on the real library, and
  the .bat with recipe 1: 74 STLs surveyed, 68 already in the library, nothing new. (2) The whole flow into a scratch
  library and maker folder without those 68 (`KB_ROOT_LIB`, `KB_ROOT_NC`): 39 fits in 582 s (about 15 s a part with
  Blender's KD tree), heads match 0.086-0.192 mm, pads 0.160-0.249 mm, 13 pushed out, Pad 11 / 13 flagged as on Nov 9;
  test marines: every part placed, the same two pads fail the 0.65 mm cut; 68 parts built and applied, all md5s
  match. Against the real library's Nov 9 result: same 68 names, files, categories, fit keys, `_sources.csv` rows and
  index entries (previews median 106 KB both); fits differ by 0.003 mm median, 0.13 mm / 0.12 deg at most (the
  32-bit KD tree picks a different nearest point now and then). Golden run afterwards: all 140 where they were.
- **Not tested**: a real new drop into the real library (none was to hand; Josh to pick the first), `record` on the
  PC (the test ran with `--no-record`), the container path after the `kb.fit` change (same code, not re-run there).
- **Also Nov 13 (Josh's Caliper decisions)**: the 3 kept-back Turtle Ninja files keep their originals:
  `_caliper_keep.txt` at the top of the library (a library path per line), read by `caliper_repair.py` so they are
  not sent again; their unused Caliper folders moved to `_backups\caliper-2026-11-13\caliper-output\`. The swap's 5%
  triangle rule stays.

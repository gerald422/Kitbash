**Caliper Repair.bat (Nov 13; Josh: "a .bat to load up Caliper, run the tool and export").**

Why: Caliper had never been run over `D:\Kitbash Library` (no `_repaired.csv`, no `caliper-*` backup), and its batch
window takes one folder at a time; the library has 1,119 folders with STLs. A read-only sample of 300 parts with
`caliper_swap.py`'s fault test: 65 (22%) have faults, mostly Turtle Ninja - Heresy (27 of 51), Old Style Space Knight
(8 of 8, about 292 open edges each: one shared piece?), Marta (17 of 99); Springles 0 of 42. Half of the 65 have 20 bad
edges or fewer.

- **Caliper 0.9.1 has a command line** (`Caliper.exe --help`): `--batch-repair <repair-backend.cfg> <folder>
  <export parent> [--timeout s] [--jobs-root path]`. No window; a JSON report on stdout (per file: status, destination,
  triangles before / after); exit 0. It takes the folder's direct STL files only, 256 at most, repairs every one of
  them (clean ones too: Caliper's window skips those, the command line doesn't), and writes
  `<export parent>\Caliper-repaired-<GUID>\<n>-<name>_repaired.stl`. Adding `--no-updates` makes it answer "Invalid
  batch arguments". 4 torsos: 4 s.
- **`library-tools/caliper_repair.py` + `Caliper Repair.bat`** (installed beside Caliper Swap in the page folder): drop
  a folder. Per folder under it: fault test on every STL (the same `load` / `faults` as the swap, imported), the ones
  with faults copied 256 files / 1.5 GB at a time into `%TEMP%\caliper_work\in` (see below; short paths too: Caliper
  has no long-path support),
  Caliper run on that, its output folder moved beside the originals as `Caliper-repaired-<first 8 of the id>`. Nothing
  is replaced. Then the .bat asks (Y / N) whether to run Caliper Swap on the same folder. `all` sends every STL,
  `--dry` only lists the faults. A file with a repaired copy already waiting is left out, so a stopped run carries on.
  Stops before a batch if the temp drive has less than three times its size plus 1 GB free, and at the first batch
  Caliper refuses outright (the rest would go the same way). Log `caliper_repair_log.csv`
  beside the swap's.
- **`caliper_swap.py`**: its run section is now `main()` so the functions can be imported; nothing else changed
  (same output on the test folder).
- **Tested** on copies in a temp folder (9 files, 3 folders, one `_` folder): dry run lists 6; run repairs 6 into 2
  folders; a second run leaves all 6 out; the .bat with Y swaps 5 and keeps 1.
- **Found: the swap's triangle rule keeps back Old Style torsos.** Caliper took `Torso A5` from 53,578 to 46,662
  triangles (-13%) and `Torso F1` from 38,876 to 45,894 (+18%); both passed the position checks and failed only
  "triangles within 5%". Ask Josh before loosening it (the surface checks already guard the shape).
- **Baseline recorded, then Turtle Ninja - Heresy done (Josh: "go ahead with both").** `tests/golden/run.py` runs in
  his Blender as it is: 140 parts recorded in 25 s (`golden.json`, TIOW Inbox 1.17.8), a second run "all 140 parts
  where they were" (Hard Ops / Snap Measure / Panel Stitcher print errors in background mode; harmless). The Nov 13
  run without a result had only been stopped. Then `caliper_repair.py` on the maker folder: 1,192 files, 612 with
  faults (51%), all 612 repaired by Caliper in 11 min; swap: 609 swapped, originals in
  `_backups\caliper-2026-11-13\` (4.4 GB), `_repaired.csv` 609 rows (copied to `library/`). Golden run afterwards:
  all 140 where they were (13 of its parts are among the swapped files).
- **Kept back, for Josh to look at in Caliper** (their Caliper folders are still beside them): the three
  "Kitbash Files (Rigging Required)" parts `TN Mk6 Addon - Mk6 Torso` (149,908 -> 92,004 triangles),
  `TN Mk6 Addon - Mk6 Legs` (611,824 -> 355,832, surface moved up to 0.6 mm) and `TN Mk6 Assault - Lightning Claws`
  (124,888 -> 92,596): Caliper removes a third of each, probably inner or doubled shells.
- **Not done**: the other makers (Old Style Space Knight and Marta next by the sample; a whole-library run is about
  25 min of checking plus the repairs). The swap's 5% triangle rule vs the Old Style torsos is still Josh's call.

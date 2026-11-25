# 142 - Arms batch 2 written; the TN / Redwarden legs redone (Nov 25)

## Arms batch 2 written

Josh: "these are all good" for `03 Stage 3 - Mar Fil Power Fists, Outrider and Techmarine arms (2026-11-25).blend`.
It was unchanged, so every start (the arm's old seat) is approved.

**Written** (`batch.py write`, half "fit"):
- The Shoulder R fit of 23 arms: 15 Assault Power Fists, 6 Outrider arms with handles, Techmarine Arms 4 and 5.
- The mirrored Shoulder L fit in each Power Fist's mirror variant (15).
- Each new fit is 0.006 mm / 0.04 deg from the old one.
- Every joint placed from the library (socket . fit) matched the file at 0.0000 mm.
- The old sidecars are in `_backups\batch write 2026-11-25 1212`.
- The batch file went to the Recycle Bin.

## The TN legs redo

Josh chose to re-fix the TN legs (notes 141): his Nov 24 change turns Legs 1A 18.5 deg against every TN torso, so
the legs, and the base under them, lean about 11 deg. Mar Fil's legs stand flat.

**The file** is `02 Stage 2 - TN and Redwarden legs redo (2026-11-25).blend`, built by `make_legs_redo_batch.py` with
`batch.py build --then legs_floor.py`. It has three columns:
- Torso 2 as written, all locked: the target.
- TN Mk2 Upper A1, the torso his TN change was made on.
- Redwarden's Prime Techmarine torso, kept separate as Josh asked.

Each torso is stood by its upright, as TIOW stands it. Its spacer, Arm 2B R, guide, pad, helmet and backpack are
locked. Legs 1A is movable and starts at its written seat. A thin flat floor sits under each column's legs, at their
lowest point, so a lean shows as one foot down. One shared floor height doesn't work, because Redwarden stands
17 mm lower.

**Writing it:** his move is that torso's Waist (half "socket"). The Waist is already his (`kb_josh`), which Rule 1
protects. A spec write marked `"redo": true` lets `batch.py write` replace a kb_josh socket of that type on that
host, and the write log says so. Nothing else can replace one.

A `--check` dry run on the unchanged file gives 0.000 mm on both Waists.

**Then:** the TN move (as a change in the Waist's axes) is carried to the other 53 TN torsos' Waists. Josh checks those
in a file before they are written.

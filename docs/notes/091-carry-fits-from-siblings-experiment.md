**Item 2 (fits for arms, legs, torsos): the experiment is done, the fitter is not built yet (Nov 13; stopped at Josh's usage limit).**

Idea: a new part gets its fits / sockets from the already-fitted parts beside it in its library folder, instead of
one reference part per type. Tested by leave-one-out on the library (`tests/kb/loo_carry.py`, numpy + scipy, read
only, about 5 s a part: hide a fitted part's sidecar, carry each joint from up to 4 siblings, compare with the truth;
"right" = within 0.5 mm and 3 deg).

- **Torso sockets** (Shoulder R / L, Neck, Back, Waist), first version (whole-shape ICP from 24 turns + the kit frame,
  then the region within 7 mm of the joint): 115 joints on Mar Fil and Old Style torsos, median 0.01 mm, worst
  0.18 mm, 0.2 deg: all right. Only kit-frame folders were in the sample; Marta has no socketed torso at all and
  Turtle Ninja - Heresy 64 of 466, so the 703 unsocketed torsos still need a cross-folder reference (not tested).
- **How a folder's fitted parts relate decides how to carry** (from the sidecars alone): `same` = every sibling has
  one matrix (a kit frame: Mar Fil 27% of arms, TN Heresy 40%); `turn` = same turn, different place (all 144
  Springles arms, about half of Marta's and TN Heresy's); `rigid` = neither (most legs).
- **Results by mode** (12 parts a maker, 5 makers):
  - arms `same` (copy the matrix): 9 of 9 right, worst 0.04 mm.
  - arms `turn` (move the 6 mm shoulder region without turning it): 71% right; kept only where the region matches
    within 0.12 mm: 13 of 28 kept, all right (worst 0.13 mm). At 0.20 mm: 21 kept, 85% right (worst 0.76 mm, 1 deg).
  - arms `rigid`: 60% right and the region match does not separate them (turns of 20-170 deg at 0.08-0.20 mm). Right
    only when it is nearly the same arm: region <= 0.07 and whole shape <= 0.10 mm gave 12 of 13.
  - legs `rigid` (13 mm pelvis region): 56% right; kept at region <= 0.12 mm: 27 of 57, all right (worst 0.35 mm,
    0.2 deg). Turtle Ninja legs 100%; Mar Fil / Marta legs 25-30% (they fail the gate: by-eye or their own rule).
- **So the fitter to build** (`kb/carry.py`, a `"fit": "like"` type in `kits/creator/add_creator.py`): references =
  the fitted parts of the same type in the folder the new part is filed in; mode from those; gates: `same` copy
  (check the joint lies on the new part as on its siblings), `turn` region <= 0.12, `rigid` legs / torsos region
  <= 0.12, `rigid` arms only the near-identical case; anything else is filed without a fit and logged with the
  number. Record the mode, reference and match in the sidecar (the fit-quality score in the backlog).
- **Legs' sockets**: the belt ones (Hip, Belt Front / Back, Buckle, Plate, Trophy) sit within 15 mm of the waist
  joint, so they go with the pelvis match; Base (24 mm away, under the feet) and Shin do not: Base needs the flat-legs
  rule (`kits/cr/dev/flatlegs.py`: lowest 0.6 mm of the file, Z up, Y front), to be lifted into `kb/`.
- **Not done**: `kb/carry.py`, the add_creator wiring, mirrored references for the other side, the Base rule, a
  Blender test, and the coverage count for the parts without a fit (item 3).

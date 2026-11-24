# Open items

**The plan is `docs/PLAN.md` (agreed Nov 24, replaces the Nov 16 plan): read it first; where an item below is
covered by its stages, the plan wins.** This file holds only what is open outside the plan. The list before
Nov 16 is in `docs/archive/` (history, not to be followed). When an item is done, delete its line (the notes entry
is the record).

## Waiting on Josh

- **For the plan** (`docs/PLAN.md`, "What Josh provides"): the Springles spacer, one arm per pattern and the wrist
  cut in the reference. Marta legs, then Marta arms, next (notes 115).
- **Mar Fil joints written Nov 19** (notes 116): `Run checks.bat` will show the Mar Fil changes; `Run checks.bat
  record` once they look right. 124 near fits show "check it" in the Squad Builder until corrected. Undo:
  `Write joints.bat restore`.
- **New reference** (notes 117): TO CUT fits in the main file and the Turtle Ninja / Springles / Marta setup files;
  check Jump Chaplain Legs D and Intercessor Legs 22's shin spots (moved in run 26).
- **Squad Builder is cut-only** (notes 116): only the parts and joints the cuts made are on the page (`_builder\cut_only.json`,
  `"on": false` + Prepare shows everything again).
- **Springles arms** (notes 114): 14 arms in `arms.blend` have the shoulder flat 0.2-0.4 mm off the origin (use the
  measured flat? Josh not sure yet). The rest of Springles - Heresy (heads, backpacks, toppers, accessories, plate
  accessories, grenades) is still at 1.1: Josh will check each against Mar Fil before the 3% (by the median size,
  the helmets are already 9-14% bigger than Mar Fil's). Springles - Weapons has 98 sidecars at 1.1 and 360 with no
  scale (guns, not used for now): which is right?
- `Run checks.bat` will show 3 Springles arms in the baseline 3% bigger (Nov 18, on purpose): `Run checks.bat record`
  once they look right.
- **The fits written Nov 15 from old-fit examples** (Mar Fil weapon hands and backpacks, BBoosty, Turtle Ninja, Marta
  Weapons and Bits hands; notes 105, 107, 108) are in the library until the plan redoes them. Each run's backup is in
  its `_backups\connectors-2026-11-15-NN\before`.
- `_backups\origins-2026-11-15\before` holds the 478 original STLs (4.7 GB) from the Nov 15 origin move; his to
  delete once he is happy (`Move origins.bat restore` needs it). The later moves (heads / jump packs, two-handed,
  held weapons, backpacks) have their own `origins-2026-11-15-N\before`.
- After the origin move: `Restart share server.bat` before sharing again (previews are no longer cached for a day).
- **Placement baseline: recorded Nov 13** (notes 088; `tests/golden/golden.json`, 140 parts, TIOW Inbox 1.17.8). A
  snapshot, not a sign-off: `Run checks.bat record` again when the builder looks right; `Run checks.bat` after any
  change. Another clone needs `git clone -c core.longpaths=true` (9 paths are too long).
- **Caliper over the library** (notes 088, 090): Turtle Ninja - Heresy done Nov 13. The other makers are his to
  run: drop the maker folder on `Caliper Repair.bat` (page folder), say Y, then `Run checks.bat`, then tell Claude
  (or run `Export sidecars to repo.bat`) so `_repaired.csv` is committed. Decided: the 3 kept-back files keep their
  originals (`_caliper_keep.txt`), the 5% triangle rule stays.
- Springles / Redwarden batch (Nov 9, 323 parts): run Prepare, look them over. 150 have no fit (notes 074).
- Chest inserts (Nov 9): check the 44 in the builder; Iron Gorgon 01 / 07 have winged emblems (hide?). (075)
- WarGame Exclusive: PAD_11 / PAD_13 cut 1.1-1.3 mm, Fix the Part if they look sunk. (077)
- Never-set-up kits: which go in (`kits/nofit/setup-kits/never_set_up.json`: Mar Fil 20 kits, Iron Hands 27,
  Springles mk6 cybernetics, TN Primus Medicae / WGBL). (071)
- Tilt shields: his placement is saved in `Desktop\Tilt shields - place by eye.blend`, not read yet. (068)
- Loincloths: same tuck as May 3 for the other banded ones? TN Librarian Buckle / Bottle: is the buckle a front piece?
- 'Torso hasn't followed the legs' roll': not reproduced; what should it follow? (072)
- Which Chaplain / Techmarine "hip armour" files he meant. Captain with Jump Pack belt plates to review.
- Files on his Desktop from Nov 14: `TIOW Blender bridge\shells\` (superseded by his connectors; `old-averaged\`,
  `old-first-try\` are his to delete); `pad-masters-sheet.jpg`, `pad-now-vs-master.jpg`, `item3-test-sheet.jpg`.
- Page: "Other way round" in the Adjust panel (notes 095): the turn itself not yet tried on a model.
- Share server: cloudflared + adding people (passwords never pass through Claude) (066); first Save fit through the
  shared page (the `/correct` route has only run in tests); a removed user stays signed in up to 12 h unless the
  server is restarted. Sharing was stopped on Nov 15 (all servers and tunnels closed).
- Hosted demo: the older public "Squad Builder" artifact; ask before republishing to it.

## Outside the plan, to do

- Waist adapters (Josh, Nov 20): the Bits adapters `Bits/Adapters/lower_body_(torso)_1..6` (flat-topped waist
  spacers: fit Waist, socket Flat Waist) are all options, #3 the default. Rule for the page / TIOW Inbox: a Mar Fil
  torso on flat-topped legs (every Turtle Ninja and Marta legs) goes on the adapter; a non-Mar Fil torso (flat
  bottomed) on flat-topped legs needs none; a non-Mar Fil torso on Mar Fil legs sinks further down onto the legs'
  waist, into its solid bottom. Their cuts come from the maker setup files (adapter #3 + Torso 2, and each TN /
  Marta legs on #3), then this needs building.
- Finalise: export step, a peg test piece (pegs have never been printed).
- Pauldrons (Nov 22-23, notes 118-119): the print fix is in Finalise 0.3.4. Placement: Josh's guide seats on 21 arms
  (`~\Desktop\mar fil connectors\Pauldron adapter - seat and cut (2026-11-23).blend`) are read by the reader (pad joint
  from the guides) and proved on the Assault arms; not written to the library yet: arms' `Pad R` sockets and pads'
  fits go together, from one run. Open: the Marta legs waist auto cut (through adapter 3); TN `Pauldron A 1` not in
  the library; Marta Gurls `arm-4-cloth` is a left arm without L in its name.
- Housekeeping: retire the TIOW-FTRP bridge (he no longer uses TIOW-FTRP: `bridge/`, the bridge template, the
  bridge's installed files: deletes on the PC, ask first).
- Recipes per main maker for `add_creator.py` (only `wargame-exclusive.json` exists): the plan's intake needs them.
- Builder errors from Nov 6 (notes 072) not covered by the plan: loincloth seating (the Belt Front spot is right,
  the loincloth's own seat is wrong); hip / belt-back bits stand upright on every legs but Assault 4B; scenic bases
  (legs into the wall, base rise skipped); Save Correction scopes (part / folder / every host of a kit).

## Backlog

- **Bionic legs: start again from scratch** (Josh, Nov 10). Branch `bionic-1.18` (TIOW 1.18, Finalise 0.3.2) is
  abandoned: kept for reference, never merge or deliver it. Inputs: `Desktop\Bionic plug - place by eye.blend`, the SM
  Mechanical Legs kit in `D:\new cults\legs-mechanicals-hand-sm-iron20240827-1-jr2qoj\`, notes 045, 046.
- Holsters / sheaths from the Nov 9 batch onto the hip plate (`kits/plates/hol_fit.py` rule).
- Hip plates on more torsos / legs; chest, pack and pauldron anchors (necklace, book, ornaments, ribbons). (057)
- Mechadendrite tails and mechadendrites (spec: 079; assets `Desktop\tubes, pipes, chains\`).
- New bits next month: capes, tabards, arms, a shield (sheets seen Nov 4).
- Marta mark tidy-up; 5 stale Marta sidecars in the repo the library no longer has (check against the PC).
- Bladeguard Volkite A/B right-hand fit; Plasma Incinerator 3A/3B by eye; BBoosty / CyberBrush accessories without fits.
- TN Mk5 Helmet 10 sits 0.82 mm off its fit in query.blend (he didn't mention it; left alone).
- Stale page tests `t_wings_step.js` / `t_belt_step.js` (step index).
- Old kit scripts (`kits/`, `tests/v1xx`) still use `/home/claude/...` paths: history, don't extend them; lift what a
  new task needs into `kb/`.
- A fit-quality score per fit (the match residual), so audits are a query.

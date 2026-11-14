# Open items

Short and current. Detail for most lines: `docs/notes/084-open-items-in-full-nov-9.md`, or the notes entry named.
When an item is done, delete its line (the notes entry is the record).

## Order agreed with Josh (Nov 13, notes 089)

1. Done Nov 13 (notes 090): `add_creator.py add RECIPE --src FOLDER` and `Add parts.bat` run on the PC. **Still to do:
   a recipe for each main maker** (only `wargame-exclusive.json` exists), written when its next drop arrives; the
   first real drop is Josh's to pick.
2. Done Nov 13 (notes 091): a recipe type with `"fit": "like"` carries arms, legs and torsos from the fitted parts
   in their library folder (`kb/carry.py`); what it keeps was right in the check, about half of arms and legs are
   dropped for by-eye placing. Still open: torsos in folders with no socketed torso (Marta, most Turtle Ninja).
   Parts with no fit can now be placed on the page: they are dropped on their socket, flagged (notes 092).
3. Fit the parts that have none: **carrying done Nov 14 (notes 093)**: 80 Turtle Ninja torsos got sockets, 1 arm a
   fit; legs, pads, heads and the other 564 torsos cannot be carried (no fitted part like them). **Josh, Nov 14:
   Marta's torsos are not being done; heads are skipped for now, he comes back to them** (then: one Marta head placed
   by eye, her 250 share a frame, `carry.like(mode="turn")`). **Turtle Ninja's posed torsos are out too** (Josh,
   Nov 14, as on Oct 20, notes 026: one pose a torso, the straight one, usually 1 or 9 of a letter): the 338 without
   sockets stay so (`OUT` in `kits/nofit/carry_library.py`); the 80 socketed on Nov 14 are posed copies and stay
   (his call, Nov 14). Still without a fit and needing a reference each: 80 arms, 51 legs, the pads the
   pad rule did not take (notes 094). Not run: held weapons and accessories (fits with `offHand` / `pivot`).
   **Pads by their inside only** (Josh's idea, Nov 14, notes 094: `run` / `loo --inner`, `families`): works where
   insides coincide; the 57 unfitted pads have no fitted twin (45 families among them: TN Mk4 pauldrons are 2), so
   each family wants one placed by eye, then `run --inner`. It also showed fitted pads with the same inside and
   different fits (Marta, WargamesPrint, CyberBrush): item 4.
4. Shared causes of bad snaps, worst first by his account: **pauldrons, necks, accessories**; then the Nov 6 list
   below; a standing audit and a fit-quality score.
5. Origins at the joint (below). 6. Finalise: export step, a peg test piece (pegs have never been printed).
7. Housekeeping: retire the TIOW-FTRP bridge (he no longer uses TIOW-FTRP: `bridge/`, the bridge template, the
   bridge's installed files); share server POST check (sharing is only for testing and limited printing).

## Waiting on Josh

- **Shells (Nov 14, notes 094 / 095)**: Josh's design: the shell of a joint lies at the centre of a scene (= the
  socket), a part is moved to it and mated there, ONE fit a shell a creator, his to set. **Origins are to be moved
  for real** (his decision, Nov 14), so a part that hangs off something needs no fit of its own. Made: 47 shells
  (pauldron and shin pad shells; head, backpack, arm and hand connectors) and `shells.blend`, on his Desktop in `TIOW Blender bridge\shells`;
  "Other way round" in the page's Adjust panel (installed; the turn itself not tried on a model).
  **Waiting on him**: one example a type a creator placed in `shells.blend`; whether heads and hands shells are
  his to cut by hand (they are rough); where re-origined files go (the STLs have no backup).
  **To build**: reading his examples from the file; the seating for heads / packs / arms / hands (pads:
  `masters.py one`); the turn of parts lying another way in their file; the origin move itself and "no fit =
  origin is the joint" in TIOW Inbox and the page.
- The 80 Turtle Ninja torsos socketed Nov 14 (posed copies, notes 093 / 094): **stay as they are** (Josh, Nov 14);
  no more posed ones are to be fitted. (A Marta head by eye: later, when he comes back to heads.)
- **Placement baseline: recorded Nov 13** (notes 088; `tests/golden/golden.json`, 140 parts, TIOW Inbox 1.17.8). It is
  a snapshot of what TIOW does today, not a sign-off: `Run checks.bat record` again when the builder looks right.
  `Run checks.bat` after any change. Another clone needs `git clone -c core.longpaths=true` (9 paths are too long).
- **Caliper over the library** (notes 088, 090): Turtle Ninja - Heresy done Nov 13. The other makers are his to
  run: drop the maker folder on `Caliper Repair.bat` (page folder), say Y, then `Run checks.bat`, then tell Claude
  (or run `Export sidecars to repo.bat`) so `_repaired.csv` is committed. Decided: the 3 kept-back files keep their
  originals (`_caliper_keep.txt`), the 5% triangle rule stays.
- Springles / Redwarden batch (Nov 9, 323 parts): run Prepare, look them over. 150 have no fit (notes 074).
- Chest inserts (Nov 9): check the 44 in the builder; Iron Gorgon 01 / 07 have winged emblems (hide?). (075)
- WarGame Exclusive: PAD_11 / PAD_13 cut 1.1-1.3 mm, Fix the Part if they look sunk. (077)
- Terminator / Gravis torsos have no sockets: reference placements needed. (076)
- Never-set-up kits: which go in (`kits/nofit/setup-kits/never_set_up.json`: Mar Fil 20 kits, Iron Hands 27,
  Springles mk6 cybernetics, TN Primus Medicae / WGBL). (071)
- Tilt shields: his placement is saved in `Desktop\Tilt shields - place by eye.blend`, not read yet. (068)
- Loincloths: same tuck as May 3 for the other banded ones? TN Librarian Buckle / Bottle: is the buckle a front piece?
- 'Torso hasn't followed the legs' roll': not reproduced; what should it follow? (072)
- Mirror on the fly: auto-mirror single-side parts, or a checkbox on every slot?
- Which Chaplain / Techmarine "hip armour" files he meant. Captain with Jump Pack belt plates to review.
- **A backup for the STLs**: D: is one external exFAT drive and the library (65 GB) is nowhere else. He will put it
  in cloud storage (Nov 13); not done yet.
- cloudflared + adding people for the shared page (passwords never pass through Claude). (066)
- Hosted demo: the older public "Squad Builder" artifact; ask before republishing to it.

## In progress: placement without by-eye work (Nov 10-12, notes 085)

- Done: Adjust on the page (move / turn / snap / seat, Save fit, `_builder\\corrections.jsonl`).
- Done: handle at joint or middle, torso turns on the legs, owner's saves from the shared page (`/correct`).
- **Next, Josh's long-standing ask: origins at the joint in Blender.** TIOW Inbox keeps the maker's file origin (the
  middle of the scene for kit-frame parts), so turning a part in Blender swings it about a far point. Put each
  part's origin on its joint at import (keep the offset on the object so fits are still read in file coordinates).
  Needs Blender and the golden run; touch Save Correction, anchors, variants, Finalise.
- Installed Nov 12 (page, README, `share_server.py`, `Restart share server.bat`); sharing restarted with the new
  server. Waiting on Josh: first Save fit through the shared page (the `/correct` route has only run in tests).

## Next up (builder errors, Nov 6 diagnosis: fix shared causes, not pieces; notes 072)

1. **Loincloth seating** (the Belt Front spot is right; the loincloth's own seat is wrong; tabards are fine there).
2. Hip / belt-back bits stand upright on every legs but Assault 4B (the Oct 30 tilt stayed on one legs; rock is 8 deg).
3. Packs centred by bounding box (Backpack 1 Sword 1.9 mm off).
4. Scenic bases: legs into the wall, base rise skipped.
5. Save Correction scopes (part / folder / every host of a kit).
6. 9 borderline arms from the pad fix (073).

## Backlog

- **Bionic legs: start again from scratch** (Josh, Nov 10: not happy with the earlier work). Branch `bionic-1.18`
  (TIOW 1.18, Finalise 0.3.2) is abandoned: kept for reference, never merge or deliver it. Inputs for the restart:
  his plug example `Desktop\Bionic plug - place by eye.blend`, the SM Mechanical Legs kit in
  `D:\new cults\legs-mechanicals-hand-sm-iron20240827-1-jr2qoj\`, what he asked for (notes 045, 046).
- Holsters / sheaths from the Nov 9 batch onto the hip plate (`kits/plates/hol_fit.py` rule).
- Hip plates on more torsos / legs; chest, pack and pauldron anchors (necklace, book, ornaments, ribbons). (057)
- Mechadendrite tails and mechadendrites (spec: 079; assets `Desktop\tubes, pipes, chains\`).
- New bits next month: capes, tabards, arms, a shield (sheets seen Nov 4).
- 623 torsos without sockets (Marta 277, Turtle Ninja 338 after Nov 14's 80, BBoosty 5, Mar Fil 3): torso /
  left so on purpose (Marta: no torsos; Turtle Ninja: only the straight pose of each; Josh, notes 026 / 094). 238 parts in types with no page step.
- Marta mark tidy-up; 5 stale Marta sidecars in the repo the library no longer has (not the 8 `Arms` / `arms`
  duplicates removed Nov 13; check against the PC).
- **Share server: refuse POSTs from other sites** (Nov 13 review, notes 086): `/correct` and `/send` don't check
  `Origin` / `Content-Type`; about five lines in `share_server.py`, then deliver and restart sharing. Also: a removed
  user stays signed in up to 12 h unless the server is restarted.
- Fit coverage (Nov 14, after notes 093): 2,292 of 6,887 parts have no fit (torsos counted by sockets: 623 of 877).
  Most: Two-Handed Held 332 / 446, Heads 287 / 657, Hand-less Weapons 238 / 262, Accessories 105 / 199, Unsorted 86 / 86.
- Bladeguard Volkite A/B right-hand fit; Plasma Incinerator 3A/3B by eye; BBoosty / CyberBrush accessories without fits.
- TN Mk5 Helmet 10 sits 0.82 mm off its fit in query.blend (he didn't mention it; left alone).
- Stale page tests `t_wings_step.js` / `t_belt_step.js` (step index).
- Old kit scripts (`kits/`, `tests/v1xx`) still use `/home/claude/...` paths: history, don't extend them; lift what a
  new task needs into `kb/`.
- A fit-quality score per fit (the match residual) in sidecars, so audits are a query.

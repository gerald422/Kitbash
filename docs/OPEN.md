# Open items

Short and current. Detail for most lines: `docs/notes/084-open-items-in-full-nov-9.md`, or the notes entry named.
When an item is done, delete its line (the notes entry is the record).

## Order agreed with Josh (Nov 13, notes 089)

1. **Add-a-maker on the PC, a recipe per maker**: `kits/creator/add_creator.py` without the container (no staging), one
   saved config per maker so new parts from a maker already in the library go in with one command. New makers are rare;
   new parts from the same makers are frequent.
2. Automatic fits beyond heads and pads: arms (Nov 12 prototype, notes 085), legs, torsos.
3. Fit the parts that have none (he wants all of them fitted up front): match against the same maker's fitted parts.
4. Shared causes of bad snaps, worst first by his account: **pauldrons, necks, accessories**; then the Nov 6 list
   below; a standing audit and a fit-quality score.
5. Origins at the joint (below). 6. Finalise: export step, a peg test piece (pegs have never been printed).
7. Housekeeping: retire the TIOW-FTRP bridge (he no longer uses TIOW-FTRP: `bridge/`, the bridge template, the
   bridge's installed files); share server POST check (sharing is only for testing and limited printing).

## Waiting on Josh

- **Placement baseline: recorded Nov 13** (notes 088; `tests/golden/golden.json`, 140 parts, TIOW Inbox 1.17.8). It is
  a snapshot of what TIOW does today, not a sign-off: `Run checks.bat record` again when the builder looks right.
  `Run checks.bat` after any change. Another clone needs `git clone -c core.longpaths=true` (9 paths are too long).
- **Caliper over the library** (notes 088): Turtle Ninja - Heresy done Nov 13 (609 of 612 swapped, golden unchanged).
  His to look at: the 3 kept back (Mk6 Torso, Mk6 Legs, Lightning Claws: Caliper drops a third of their triangles);
  the swap's 5% triangle rule also keeps back Old Style torsos (-13%, +18%). Next makers: drop the folder on
  `Caliper Repair.bat` (page folder), say Y, then `Run checks.bat`. The work folder must not be on D: (exFAT).
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
- **A backup for the STLs**: D: is one external exFAT drive and the library (65 GB) is nowhere else. Where to?
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
- 703 torsos without sockets (TN other poses, Marta): torso / flat-torso rules. 238 parts in types with no page step.
- Marta mark tidy-up; 5 stale Marta sidecars in the repo the library no longer has (not the 8 `Arms` / `arms`
  duplicates removed Nov 13; check against the PC).
- **Share server: refuse POSTs from other sites** (Nov 13 review, notes 086): `/correct` and `/send` don't check
  `Origin` / `Content-Type`; about five lines in `share_server.py`, then deliver and restart sharing. Also: a removed
  user stays signed in up to 12 h unless the server is restarted.
- Fit coverage (Nov 13 count): 2,547 of 6,887 sidecars have no fit (877 are torsos, which need none). Most: Two-Handed
  Held 332 / 446, Heads 287 / 657, Hand-less Weapons 238 / 262, Accessories 105 / 199, Unsorted 86 / 86.
- Bladeguard Volkite A/B right-hand fit; Plasma Incinerator 3A/3B by eye; BBoosty / CyberBrush accessories without fits.
- TN Mk5 Helmet 10 sits 0.82 mm off its fit in query.blend (he didn't mention it; left alone).
- Stale page tests `t_wings_step.js` / `t_belt_step.js` (step index).
- Old kit scripts (`kits/`, `tests/v1xx`) still use `/home/claude/...` paths: history, don't extend them; lift what a
  new task needs into `kb/`.
- A fit-quality score per fit (the match residual) in sidecars, so audits are a query.

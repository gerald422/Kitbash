# Open items

Short and current. Detail for most lines: `docs/notes/084-open-items-in-full-nov-9.md`, or the notes entry named.
When an item is done, delete its line (the notes entry is the record).

**New chat, start here (Nov 15):** the current work is item 5 (connectors, origins at the joint): read it, then
`docs/notes/100`-`101`. Mar Fil arms, legs, shoulder pads and shin pads are seated by connectors (notes 100; Josh:
"looked good") and their **origins are moved onto the joint for real** (notes 101, `Move origins.bat`; `restore`
undoes). Next is 5 (d), then the other part types and makers.

## Order agreed with Josh (Nov 13, notes 089)

1. Done Nov 13 (notes 090): `add_creator.py add RECIPE --src FOLDER` and `Add parts.bat` run on the PC. **Still to do:
   a recipe for each main maker** (only `wargame-exclusive.json` exists), written when its next drop arrives; the
   first real drop is Josh's to pick.
2. Done Nov 13 (notes 091): a recipe type with `"fit": "like"` carries arms, legs and torsos from the fitted parts
   in their library folder (`kb/carry.py`); what it keeps was right in the check, about half of arms and legs are
   dropped for by-eye placing. Still open: torsos in folders with no socketed torso (Marta, most Turtle Ninja).
   Parts with no fit can now be placed on the page: they are dropped on their socket, flagged (notes 092).
3. Fit the parts that have none. **Carrying done Nov 14** (notes 093): 80 Turtle Ninja torsos got sockets, 1 arm a
   fit. **Left out on purpose** (Josh; `OUT` in `kits/nofit/carry_library.py`): Turtle Ninja posed torsos (only the
   straight one of each, usually 1 or 9 of a letter; the 80 posed ones socketed Nov 14 stay), TN "Rigging Required"
   folders, Marta torsos; Marta heads later; **weapons without a hand (wrist) are not used** (Josh, Nov 15, as
   Marta's torsos: `Hand-less Weapons` and "No Hand" / handless files get no fit, no cut, no connector work). Pads: one master a maker folder, every pad seated on its inside
   (`kits/nofit/masters.py one`; Josh accepted the master's fit, "purple", Nov 14; nothing written yet; notes 094).
   **The rest (80 arms, 51 legs, 57 pads, heads, held weapons) now goes through connectors (item 5).**
4. Shared causes of bad snaps, worst first by his account: **pauldrons, necks, accessories**; then the Nov 6 list
   below; a standing audit and a fit-quality score. **Accessories: last, on purpose** (Josh, Nov 15: they still
   need work and he is leaving them till the end).
5. **Connectors and origins at the joint (the current work, notes 094-096; read 096 first).** Decided by Josh,
   Nov 14:
   - **The torso stays on its sockets** (standardised; everything else matches onto it).
   - **Josh cuts the connectors himself**, one per connector DESIGN, as open surfaces in place on a reference part
     (`~\Desktop\mar fil connectors\`: Mar Fil arm disc, neck, jump pack mount, chainsword grip). **Legs next**,
     the same way; he offered the arm's **pad spot** (do this first: pauldrons snap worst) and **wrist**.
   - **Pauldrons and shin pads mate by their inside (a shell)**, the same way; shin pads need no examples where a
     fitted master exists (Mar Fil 80, Marta, Old Style); only WargamesPrint's 3 and a few Marta ones have none.
   - **Origins are to be moved for real**, so a part that hangs off something needs no fit of its own.
   - **He fixes turns himself** (round connectors don't fix the turn); a fix is stored per connector, never per part.
   What the test showed (`kits/nofit/connector_try.py`, 25 parts a connector): a part with the same connector
   matches at <= ~0.045 mm and gets its library fit back (necks 11/11, arms 7/7 with the turn kept as in the file,
   jump packs 2/2); other designs do not match (Veteran/Bladeguard necks, backpacks, guns). Round connectors (neck,
   disc, grip) fix place and tilt, not the turn: keep the turn the part has in its file (Mar Fil exports in its kit
   frame), else his fix.
   **Done Nov 14 (notes 097):** his pad spot (one for the A and B arms), wrists A / B and legs waist are exact on
   their parts and found at the library's joint on every part of the same design (legs: all 88 Mar Fil). The pad
   spot sets a pad's seat, not its place on the dome (that stays with the pad master / inside). Josh: go ahead.
   - **Pauldrons and shin pads, two-sided** (Josh, Nov 14): arm side = his pad spot; pad side = the pad's inside,
     **cut by Josh** from MarFil Assault Shoulder Pad 1 as it sits on Arm 1A; shin: the leg side cut from Legs 1B's
     right shin, the pad side from Assault Shin Pad 1 as it sits on Legs 1B. Each pair is joined once, as on the
     reference; whether the pad's inside fixes its turn is to be tested.
   **Done Nov 14 (notes 098):** the search from scratch, `kb/connect.py` (`find`, `find_all`, levels sure / look /
   none), test `tests/kb/t_connect.py`, check `kits/nofit/connector_search_check.py`: on all 220 Mar Fil arms and
   88 legs a sure answer was never wrong where the library agrees with the shape.
   **Done Nov 15 (notes 099):** his recut (Arm 1B disc / pad spot / wrist B, keyed wrist A, Legs 2 waist and shin
   spot, Shoulder Pad 1 and Shin Pad 1 placed); pad insides cut from his placed pads (no hand cut needed); search
   fixes (tie window, round test, exact file turn). Arms, pauldrons, shin pads right with their turn; legs placed
   right, heading loose (8 of 88 back to front): **Josh turns those by hand**. No cut can key the turn (nothing
   round the disc / waist is shared); a kit exported turned (Outrider, Jump Chaplain arms ~9 deg) needs a per-kit fix.
   **(b) done Nov 15 (notes 100):** `Seat connectors.bat`; run `_backups\connectors-2026-11-15-8` written Nov 15
   (Josh: test in the Squad Builder, then `Run checks.bat`; record the golden squads only if they look right). What follows was its spec.
   **(c) done Nov 15 for Mar Fil arms, legs, shoulder pads, shin pads (notes 101):** `Move origins.bat`
   (`kits/connectors/origins.py`, `kb/origin.py`): 478 files moved by their own fit (joint on the origin, the fit
   kept as identity), sidecar / preview / index with them, originals in `_backups\origins-2026-11-15\before`;
   268 of 272 test parts exactly where they were (the 4: hip plates on moved legs). A moved sidecar keeps
   `origin.from_file`; `seat.py`, `kb.carry` and the golden run read it. **Heads and jump packs done Nov 15 (notes
   102):** 59 sure fits by his neck / jump-pack connectors (`seat.py --sure`), 88 files moved, 326 test parts where
   they were. **Two-handed / heavy weapons and (d) done Nov 15 (notes 103):** 121 seated by the disc, 169 moved;
   44 took the left arm's disc and kept their library fits (`find_all` to prefer the right one: no cut needed);
   TIOW Inbox 1.17.9 / the page index read `origin.joint` as the fit. **Cuts still needed: `docs/cuts-needed.md`**
   (`kits/connectors/cuts_needed.py` regenerates it). **Weapons with a hand, Nov 15 (notes 104-105):** no cut; one
   example per hand design placed by its library fit (`kits/connectors/hands.py`): Mar Fil 324 of 345 in 16 groups,
   dry runs only. **Waiting on Josh:** look at the 39 chainsword-hand ones on the page and at the 20 that came out
   flipped (Bladeguard swords / hammers / shields), then `seat.py write TASK --sure --near 2` per group and move.
   17 are left (12 have only Hand L: they need a left wrist cut or the mirror). **Still to do:** backpacks, hands and weapons (they need connectors and a `fit` entry in the config; `upright` / `offHand` / `pivot` /
   `scale` / `types` are not handled by the move yet, such parts are left and listed); the other makers.
   What follows was the spec. **In order:** (b) a
   production seating script (a `.bat`, Blender in the background, no Claude): every part of a maker searched with
   all its type's connectors (`find_all`); sure = fit written (`kb.sidecar.merge`, backed up), look = written and
   flagged, none = listed; fit = connector's fit moved by the match, turn fixes per connector, and a list of unmatched parts grouped
   (= which connector to cut next). It reads his blends (`connector_export.py`'s way), cuts pad insides as notes 099,
   searches the shin spot on both shins (R / L by side) and lists every look leg so he can turn it; (c) the origin move, **in place in the Kitbash Library** (Josh, Nov 15:
   files being adjusted in the library may be updated there; no STL backup for now, he can get them all again from
   MMF / Discord). Keep each run's originals in its `_backups` folder so `restore` works; (d) "no fit = origin is the joint" in TIOW Inbox and the page. Torsos, and what hangs
   off arms and legs, keep their sockets until then.
6. Finalise: export step, a peg test piece (pegs have never been printed).
7. Housekeeping: retire the TIOW-FTRP bridge (he no longer uses TIOW-FTRP: `bridge/`, the bridge template, the
   bridge's installed files: deletes on the PC, ask first). Share server POST check done Nov 15 (notes 103).

## Waiting on Josh

- **Connectors**: received Nov 14 (notes 097). Still to cut for Mar Fil, when he likes: pad spots for the
  Intercessor, Bladeguard and Techmarine shoulders; the Veteran / Bladeguard neck (27 heads, notes 102); a backpack
  mount (32 backpacks); Captain with Jump Pack heads, pack and legs; grips for guns, swords, spears. Turtle Ninja / other makers only after Mar Fil proves out.
- **Turn of round connectors** (notes 099): no recut can key it. Per-kit turn fix for Outrider and Jump Chaplain
  arms (~9 deg) when he likes; legs he turns by hand. Captain with Jump Pack legs need their own waist cut. Wrist A
  (hands) is weak (11 deg median, 19 look wrong): a better hand cut if hands snap badly.
- Assault Legs 3's library fit looks 0.5 mm / 9 deg off against the waist connector (notes 097): a look when he can.
- Library sockets that look wrong by shape (notes 098), to check by eye: Pad sockets of Outrider Arm Wight Handle
  A1 L, B1 L, B2 L and Arm With Handle B R; Veteran Arm B's Hand socket. No Forearm socket on Assault Arm 8B / 8C and
  Jump Chaplain Arm A-D, where wrist B is an exact copy.
- **After the origin move** (notes 101): `Restart share server.bat` (previews are no longer cached for a day; until
  then, and for previews a browser fetched before, moved parts can sit wrong on the SHARED page: clear its cache);
  a look at a few moved parts in Blender (turning an arm, a pad: the pivot is the joint now; a pad's or shin pad's
  file lies in its spot's frame, legs lean as on the waist); `Run checks.bat record` when it looks right
  (`golden.json` is still Nov 13's, from before the connector run).
- **Hip plates on moved legs** (Jump Captain Hip Plate With Pouch / Holster) sit 0.1-2.2 mm from where they did:
  rock / settle taking other samples, believed (notes 101). With accessories, last.
- **No fit for their joint, so not moved** (5): Captain with Jump Pack Arm 3 L and Legs, Bike Chaplain Shoulder Pad
  1 R / 2 R / L. Seat by eye (Save fit) or cut their connector, then `Move origins.bat` again.
- `_backups\origins-2026-11-15\before` holds the 478 original STLs (4.7 GB): his to delete once he is happy
  (`Move origins.bat restore` needs it).
- Files on his Desktop from Nov 14: `TIOW Blender bridge\shells\` (Claude's automatic shells: the pauldron and
  shin pad shells are usable, the head / backpack / arm / hand ones are superseded by his connectors;
  `old-averaged\`, `old-first-try\` are his to delete); `pad-masters-sheet.jpg`, `pad-now-vs-master.jpg`,
  `item3-test-sheet.jpg`. Work data (family lists, matches): library `_backups\pads-rule-2026-11-14\work\`.
- Page: "Other way round" in the Adjust panel (installed Nov 14, notes 095): the turn itself not yet tried on a model.
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
- cloudflared + adding people for the shared page (passwords never pass through Claude). (066)
- Hosted demo: the older public "Squad Builder" artifact; ask before republishing to it.

## In progress: placement without by-eye work (Nov 10-12, notes 085)

- Done: Adjust on the page (move / turn / snap / seat, Save fit, `_builder\\corrections.jsonl`).
- Done: handle at joint or middle, torso turns on the legs, owner's saves from the shared page (`/correct`).
- **Done another way for Mar Fil arms / legs / pads (Nov 15, notes 101): the files themselves are moved (item 5 c);
  the rest of the library follows there, so the import-time idea below is dropped unless item 5 stalls.**
  Josh's long-standing ask was origins at the joint in Blender. TIOW Inbox keeps the maker's file origin (the
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
- Share server: a removed user stays signed in up to 12 h unless the server is restarted.
- Fit coverage (Nov 14, after notes 093): 2,292 of 6,887 parts have no fit (torsos counted by sockets: 623 of 877).
  Most: Two-Handed Held 332 / 446, Heads 287 / 657, Hand-less Weapons 238 / 262, Accessories 105 / 199, Unsorted 86 / 86.
- Bladeguard Volkite A/B right-hand fit; Plasma Incinerator 3A/3B by eye; BBoosty / CyberBrush accessories without fits.
- TN Mk5 Helmet 10 sits 0.82 mm off its fit in query.blend (he didn't mention it; left alone).
- Stale page tests `t_wings_step.js` / `t_belt_step.js` (step index).
- Old kit scripts (`kits/`, `tests/v1xx`) still use `/home/claude/...` paths: history, don't extend them; lift what a
  new task needs into `kb/`.
- A fit-quality score per fit (the match residual) in sidecars, so audits are a query.

**Open items in full, as of the Nov 9 handover** (the short live list is `docs/OPEN.md`; this is the detail behind it).


- **WarGame Exclusive (Nov 9; notes entry): delivered**, 68 parts (`kits/wg/`): 20 heads, 19 pads with fits; PAD_7 and the shields,
  necklaces, arm/knee/leg plates without (no spots yet). PAD_11 / PAD_13 cut ~1.1-1.3 mm: Fix the Part if they look sunk.
- **Armour dropdown (Nov 9; notes entry): delivered.** Page header Armour = Tacticus / Terminator / Gravis from the mark folder;
  325 Marta thicc/termi/heavy parts re-filed under Terminator / Gravis (`library-tools/move_marks.py`); leftover picks with no spot
  are taken off and never sent. Open: no Terminator or Gravis torso has sockets yet (ask Josh for reference placements); the BBoosty IH
  pad on CyberBrush Axe Arm 1 cuts ~2 mm; stale page tests `t_wings_step.js` / `t_belt_step.js` (step index).
- **Chest inserts (Nov 9; notes entry): delivered**, TIOW 1.17.8. 44 inserts (Josh's scale baked into the library files) on the
  one torso with the spot. Josh to check them in the builder; Iron Gorgon 01 / 07 have winged emblems (his call to hide).
  More torsos with the spot: cut each like his Torso 2, then the same socket rule (`kits/inserts/build.py`).
- **Springles additions + Redwarden Techmarine kit (Nov 9; notes entry).** 323 parts filed in the library with sidecars (helmets, pads,
  vox packs, belt bits, Prime torso). Waiting on Josh: run Prepare, look at the parts in the builder. 150 have no fit yet: the 50
  holsters / bolter holsters / sheaths could take the Nov 3 holster rule (`kits/plates/hol_fit.py`) onto the hip plate; arm computers /
  augery scanners, iron halo / nuncio vox / vexilla (Backpack Toppers), unhelmeted heads, belt connectors need Josh's reference placement.
- **Builder errors (Nov 6, Josh's `Desktop\example issues.blend`; diagnosis in the notes).** Fix shared causes, not pieces.
  - **Pads: done Nov 8** (`kits/pads/`, notes entry): every arm's Pad socket in Josh's 62 convention, BBoosty/CyberBrush pad fits moved
    off the old 'dome' sockets. 9 borderline arms listed in the notes.
  - **Loincloth: next.** Josh: the Belt Front spot is right, the loincloth's own seating is wrong (tabards fit the same spot correctly).
  - Still open: hip / belt-back bits stand upright on every legs except Assault 4B (Josh's Oct 30 tilt stayed on that one legs; TIOW rocks
    belt bits only 8 deg); packs centred by bounding box (Backpack 1 Sword 1.9 mm off); scenic bases (legs into the wall, base rise skipped);
    'torso hasn't followed the legs' roll' - not reproduced, asked Josh what it should follow; a headless audit over part families; Save
    Correction scopes (part / folder / every host of a kit).

- **Parts filed without fits (Nov 6, `kits/nofit/`; Josh: nothing missed, everything without a fit logged).** 2,257 new
  library parts: Marta two-armed batch 41, Marta weapons/arms 144, leftovers in kits already set up 2,072 (every type).
  Prepare run by Josh Nov 6 (index `88ed6e38`, 6,451 parts). Of the 2,257: **136 have fits** (29 from the batch, 107 from
  Prepare's hand and shield rules); **1,180 are in `no_fit.txt`**; **703 torsos have no sockets** (mostly TN's other torso
  poses and Marta torsos - nothing attaches to them until they get the torso / flat-torso rules); **238 are types with no page
  step** (Unsorted, Accessories, Cloaks, ammo belts, Plate Accessories, Wings, bikes, servo arms). All 2,121 without a fit:
  `kits/nofit/no_fit_all.csv` (type, status, path, how the type was found); everything left out and why:
  `kits/nofit/setup-kits/log_all.csv`, `kits/nofit/marta/skipped.txt`. Types are best guesses - Josh retypes as he goes.
  - **Waiting on Josh:** which never-set-up kits go in (`kits/nofit/setup-kits/never_set_up.json`: Mar Fil 20 kits, the
    Iron Hands folder 27 kits plus its `Iron bits`, the Techmarine Conversion Kit (its `(1)` copy's pads, helmets and Prime
    torso went in Nov 9), Springles mk6 cybernetics, TN Primus
    Medicae / WGBL). File them with `classify_all.py` (add the tops to `MAKERS`), same delivery, then one Prepare.
  - The repo has 5 Marta sidecars the library no longer has (old paths of parts since moved; `sync_sidecars.py` reports
    them, not pruned).
- **Holsters on the hip plate (Nov 3): installed** - 45 holsters, pouches and grenades are Plate Accessories (plates only,
  `kits/plates/hol_*.py`); backups `_backups\holsters-2026-11-03\old\`. They only place on legs with plate spots
  (Mar Fil Assault, Intercessor, Techmarine and Turtle Ninja legs).
- **Hip plates on more legs (Nov 4).** Rule: `kits/plates/tn_seat.py` (contact seat, top edge on the belt, 26 deg roll, level
  top edge; buckle by contact; trophies by the belt rule) through `kits/plates/legs_frame.py` (Waist or Flat Waist legs, mirror
  variants as `<path>#v<i>`), then `tn_sidecars.py` (adds Plate R/L, Buckle, Trophy R/L, keeps the rest), `tn_sheet.py` /
  `tn_render.py` check sheets for Josh, index sockets updated in place. Tests `tests/plates/t_tn_plates.py` (TIOW) and
  `squad-builder/test/t_tn_step.js` (page, takes a torso + legs list).
  - **Installed:** all 465 Turtle Ninja legs (backups `_backups\tn-plates-2026-11-04\before\`); Mar Fil Intercessor (25 + their
    mirror copies; a copy's plates are the mirror image of its file's) and Techmarine (4) (backups
    `_backups\marfil-plates-2026-11-04\before\`).
  - **Left out (Josh):** Jump Chaplain (doesn't match up because of its sculpted tabard; never installed), Mar Fil Assault B
    legs, Veterans and Bladeguard (sculpted tabard he doesn't like), Outriders (on the bike); the other makers' legs aren't
    in the builder.
  - **Marta: installed Nov 5** on 178 legs (rule seats; backups `_backups\marta-plates-2026-11-05\before\`). Left out (Josh):
    Terminator armour - the 9 legs in the Terminator folders and the 30 Thicc/Termi legs filed under Tacticus.
- **Shin spots on Marta legs: installed Nov 5** on 38 legs (the sets Marta sold with shin pads, minus Techmarine V2 Legs 4/5
  whose robe hides the shins), carried from Josh's by-eye pads (`kits/shin/`); backups `_backups\marta-shins-2026-11-05\before\`.
  Oct 2026 Heavy Legs 1's spots are wrong (pads at the back; kicked-back pose) - Josh fixes them with Fix the Socket; he
  adjusts the rest by hand where needed. Other older Marta legs with bare shins: Josh may name more from the lower-leg sheets.
- **Sharing the page (Nov 4, Josh: own username and password for him + 2 people, builds land on his PC for printing):**
  `squad-builder/share_server.py` (stdlib; Blender's bundled Python or miniconda), listens on 127.0.0.1:8765 only, PBKDF2
  passwords in `share_users.json` beside it (never in the repo), Basic auth over a cloudflared quick tunnel (https, new
  trycloudflare address each start), serves only the page, index, previews and `_hidden.txt`; `?share=1` page mode hides
  the folder setup and Hide parts and POSTs `/send`; sends checked against the index and saved to
  `_builder\received\<name>\<time>\` (model ids prefixed with the name); `Build received models.bat` moves the newest set
  into the inbox. Tests `squad-builder/test/t_share.js` + curl probes (401/429/404/413/400). Josh still has to install
  cloudflared (winget) and add the people himself (passwords never pass through Claude). The .bat files weren't run on
  Windows itself: if one can't find Python, fix the python.exe paths at the top of the three .bat files. Old page in `old-1.17.7-share\`.
- **Bionic legs: resuming soon (Nov 4).** Plug example blend `Desktop\Bionic plug - place by eye.blend` (Assault Legs 2 =
  old 29-Legs-2, the 1.18 tests' main marine, and 3A = old 37-Legs-3-A, under Torso 1, his plates locked, one LINK_LEG
  each to move; read the plug's matrix, a scale on it is the kit size). Josh places it by eye. The SM
  Mechanical Legs kit is at `D:\new cults\legs-mechanicals-hand-sm-iron20240827-1-jr2qoj\WargamesPrint\legs-mechanicals-hand-sm-iron\`
  (identical copies in `... (1)`, `(2)`, `(3)`). Then merge `main` into `bionic-1.18` and carry on from the notes.
- **New bits next month (Josh's preview sheets, Nov 4):** bionic legs, five capes (2-5 share a notched top that goes under
  the power pack; 1 has straps), ten tabards (their own top plate, so they sit over the buckle), arms, a shield with a
  knife. Suggested reference placements: cape 4 (cloth with two mechadendrites) under the pack on Torso 1 with his usual
  jump pack; tabard top row 5th (gear plate, skull, tubes) on Mar Fil Assault 4A; then carry across each set. No aquilas,
  seals or scrolls seen.
- **Hosted demo:** private artifact "Squad Builder demo (Nov 3)" (`squad-builder/make_demo.py`, previews fetched as one tar).
  The older "Squad Builder" artifact is public; ask Josh before republishing to it (low-poly copies of paid parts).

- **Old Style Space Knight MK8 (Nov 3): delivered** (72 collarless torsos in the Mar Fil frame with Torso 1's sockets, 5 chest
  equipment L + mirror R, 8 neck guards + the collar, Shin Pads A-C; TIOW 1.17.7, page steps). Josh hides designs he doesn't
  want himself. Temp files deleted (Josh's OK); `_backups\mk8-torsos-2026-11-03\` keeps the old index and `_sources.csv`.
  Delivery tip: commit chunks of 14 MB, not 28 MiB (refused).

- **Accessory anchors (Nov 3): first base delivered (1.17.6) on the Mar Fil Assault legs** - plates, buckle, sheaths,
  CB tabards and trophies; data and scripts `kits/plates/` (`marfil_assault_plates.json` holds every placement Josh
  checked). Next (Josh: build in parts): Marta's legs (above); then chest, pack and
  pauldron anchors (necklace, **tilt shields**, book on the torso back, pack ornaments, pad ornaments, topper ribbons, wrist ornaments).
  Marta's loincloths left out for now (stay on Belt Front). Josh's missing-files check: later.
  - **Tilt shields (started Nov 4; Josh saved his placement in the blend, not read yet):** four spots - torso Upper Chest L/R and a spot on each
    pauldron (tier 2, like the pad's front ornament); never all four at once, but no blocking rule. Parts: the 24 in
    `D:\new cults\Tilt Shields\Tilt Shields\` (one export orientation: X wide, Y out, Z up). Josh places Tilt Shield 1 on
    the chest and on the pad in `Desktop\Tilt shields - place by eye.blend` (`kits/tilt/mkblend.py`; Mar Fil Assault Torso 1,
    Arm 1A R, Pad 1; origins at the shield's back centre; a scale on them = the set's size); then Upper Chest R/L on the
    torsos, the pad spot on the pauldrons, sidecars for the 24, TIOW + page, Mar Fil Assault first. Notes: Nov 4-5 entry.

- **Marta weapons on the page (Prepare, Nov 5)** (Nov 2: 613 one-handed parts; Nov 5: 33 the Nov 1 scan missed, `kits/marta/missed/`):
  all 646 indexed, previewed and anchored; Pad anchors on 236 of the 269 new arms (33 without - by eye if needed). Josh
  saw a few misidentifications: he fixes them in the final build. `_builder\no_fit.txt`: 49, none of them Marta. The two-armed sets, unmatched
  strapped shields, hand-less blades, Lion Knights shoulder shields and Oct 2025 heavy forearm pieces went in on Nov 6
  (above; 27 two-armed sets seated, the rest without fits). New parts checked for aquilas/seals by name only.
  Marks (Josh): heavy = Gravis, thicc = Terminator, phobois/phobia = Phobos; `plan_library` files Oct 2025 heavy under
  Tacticus and thicc under Gravis - a Marta mark tidy-up (rename_library has --undo) is for later. Backups/tools
  `_backups\marta-1h-2026-11-01\`, `_backups\marta-missed-2026-11-05\`.

- **Mirror any part on the fly (Josh, Nov 6; deferred - "Let's do martas two hand sets first"):** keep one plain file
  per part and mirror it in both the page and Blender (TIOW 1.17.8 + a page checkbox on two-armed parts and legs) instead
  of maker's left copies / mirror variants. Feasible; open questions put to Josh: auto-mirror single-side parts when
  placed on the other side, or a checkbox on every slot.
- Bladeguard Volkite A/B: right-hand fit to check.
- Captain with Jump Pack belt plates: Josh to review; mirrored copies for the other hip; his chest plate and cape.
- Mechadendrite tails and mechadendrites (spec in the notes; assets in `Desktop\tubes, pipes, chains\`); the TN Mk6
  Universal pack now has `Mechadendrite L/R` sockets from Josh.
- BBoosty and CyberBrush accessories without fits; Plasma Incinerator 3A/3B by eye.
- Which Chaplain / Techmarine "hip armour" files Josh meant.
- Loincloths: offered to give the other banded loincloths (Marta May 1-8, Jul 1-6, Ghostrider 1-2, Thicc 1) the
  same tuck as May 3 (Fix the Part, Whole Folder per set) - waiting for Josh. TN Librarian Buckle and Bottle had
  only a Belt Front fit and no longer place - ask whether the buckle counts as a front piece.
- query.blend: TN Mk5 Helmet 10 sits 0.82 mm off its fit; Josh didn't mention it, left alone.
- Wings: only the TN Mk6 Universal has Wing Mounts (Josh's choice); the other Techmarine connectors (Cables,
  Exhaust, Pivot Base, Semi-Sphere, Sphere, Sideways joints) and Malal3D's own JumpPackCore aren't in the library.

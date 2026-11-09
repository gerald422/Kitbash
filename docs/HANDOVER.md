# Kitbash build: handover (9 Nov 2026)

Everything needed to pick this work up in a fresh Claude session. The full history, with every measured value and
decision, is `docs/project-notes.md` (the Project doc `claude/part-sockets-tiow-integration.md` is an older copy: from Nov 3 the repo file is the current one).
How to make sidecars is the skill `.claude/skills/kitbash-sidecars/SKILL.md` (copy in the Project at
`claude/skills/kitbash-sidecars/SKILL.md`).

## What the build is

Josh's Warhammer 40K kitbashing pipeline, three pieces that share one part library:

- **Kitbash Library** (`D:\Kitbash Library` on Josh's PC): every printable part as an STL with a
  `<part>.sockets.json` sidecar (sockets, fits, variants). `_sources.csv` lists every part and where it came from
  (`D:\new cults\...`), `_hidden.txt` hides parts from the page (renegade chapter: no aquilas, purity seals or
  scrolls, plus Josh's own hides), `_builder\index.json` + `_builder\previews\` feed the page, `_backups\` holds a
  dated folder per change.
- **TIOW Inbox** (Blender add-on, `addons/tiow_inbox.py`, now **1.17.8**): imports parts sent from TIOW-FTRP or the
  page, rebuilds their sockets, snaps them onto the model (rock/settle for belt bits, base rise, adaptors and
  connectors), Save Correction (Fix the Part / Fix the Socket).
- **Squad Builder** (`squad-builder/`, one offline HTML page): pick parts step by step (Base, Legs, Torso, Arms
  R/L/Two-handed, Head, Neck guard, Chest equipment, Chest insert, Back, Wings, Shoulder pads, Weapons, Shin pads, Loincloth, Belt), see them placed from the
  index, send the squad to Blender through `<library>\_builder\inbox`.
- Also: **Kitbash Finalise** (`addons/kitbash_finalise.py`, 0.3.3, booleans a model into print pieces) and
  **Part Sockets** (Josh's own add-on, 6.2.0 in the container; it is not in this repo).

## Git

- Repo: <https://github.com/gerald422/Kitbash> (public: sidecars and scripts only, never STLs/OBJs/blends/npz/
  previews - `.gitignore` blocks them; the makers' files are paid).
- Branches: `main` = what is installed on Josh's PC. `bionic-1.18` = TIOW Inbox 1.18 bionic legs + Finalise 0.3.2,
  on hold (Josh: don't deliver it); it predates 1.17.1-1.17.5, so merge `main` in when it resumes.
- Latest commits: armour dropdown + Marta marks re-filed (`library-tools/move_marks.py`), chest inserts + TIOW 1.17.8 (`kits/inserts/`), `96b651b` Springles additions + Redwarden Techmarine kit (323 parts, `kits/rw_spr/`), `ffdcce2` pad fix (458 arm Pad sockets + BBoosty/CyberBrush pad fits, `kits/pads/`), `816bbc1` builder-errors diagnosis (`kits/audit/`), `943f7be` parts filed without fits (2,257, `kits/nofit/`), `ddb2537` Marta shin spots, `28a6168` Marta hip plates, `c079870` Marta missed parts + tilt blend, `3215109` Squad Builder sharing (`share_server.py`), `8daa52e` Mar Fil Intercessor + Techmarine plates,
  `74573a8` plates seat for any legs (`legs_frame.py`), `f3e5c81` TN plates installed (465 legs), `f567bd6` Old Style Space Knight MK8 + TIOW 1.17.7, `57c09ac` / `5aeeb9a` plates, buckle, holsters, tabards, trophies (TIOW 1.17.6), `0954800` Marta one-handed parts (613), `0ad4c92` this handover, `4568b9a` blade wings (1.17.5), `453c8f6` loincloth 3 fit, `5426f65` loincloths own type
  (1.17.4), `be69b80` query.blend corrections (1.17.3).
- Commit messages end with:

      Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
      Claude-Session: https://claude.ai/code/session_01PSw3X7t6mtZweYW1a5LiqE

  (a new session uses its own session link). Push straight to `main`; no PRs so far.
- Layout: `addons/` (TIOW Inbox, Finalise), `bridge/` (bridge README, `_library.json` template, TIOW-FTRP patch),
  `squad-builder/` (`src/` + `build_page.py` -> `Squad Builder.html`, `build_index.py`, `prepare_builder.py`,
  `test/` page tests), `library/` (every sidecar, `_sources.csv`, `_hidden.txt`, byte-for-byte incl. CRLF),
  `library-tools/` (plan/build/rename/fold/sync), `kits/` (one folder of build scripts per kit or task),
  `tests/` (Blender checks), `tools/setup_container.sh`, `docs/`.

## Starting a fresh session

1. Attach the repo with push access (`add_repo` gerald422/Kitbash, push) and clone to `/home/claude/kitbash`.
2. Make sure the session is linked to Josh's PC (the remote-devices tools). A new session starts with **no folders
   connected**: request them once with `device_request_folder_access` (`~\Desktop`, `D:\`,
   `~\AppData\Roaming\Blender Foundation\Blender\5.1`, `~\AppData\Local\TIOW-FTRP`).
   Then md5-check the "Installed now" list below against the PC. Stage `~\Desktop\part_sockets_6.2.0.zip`.
3. `bash /home/claude/kitbash/tools/setup_container.sh` - venv `/home/claude/bpyenv` with bpy 5.1.2, numpy, scipy,
   pillow; Part Sockets, TIOW Inbox and Finalise in the container Blender's add-ons; the old working paths
   (`/home/claude/kits`, `/real`, `/test` ...) that the scripts import from.
4. Stage the library files a task needs (below) and work from `/mnt/user-data/uploads/d/Kitbash Library/...`.

## Josh's PC (through the device tools)

Connected folders: `~\Desktop`, `D:\` (and `D:\new cults`), `~\AppData\Roaming\Blender
Foundation\Blender\5.1` (and its `extensions\user_default\part_sockets`), `~\AppData\Local\TIOW-FTRP`.

| What | Where |
|---|---|
| Library | `D:\Kitbash Library\` |
| Maker downloads | `D:\new cults\` |
| Bridge folder | `~\Desktop\TIOW Blender bridge\` (`tiow_inbox.py`, `README.txt`, `_library.json`, `old-<version>\`) |
| Page | `...\TIOW Blender bridge\Squad Builder\` (`Squad Builder.html`, `README.txt`, `build_index.py`, `prepare_builder.py`, `Prepare Squad Builder.bat`) |
| Blender add-ons | `~\AppData\Roaming\Blender Foundation\Blender\5.1\scripts\addons\` (`tiow_inbox.py`, `kitbash_finalise.py`) |
| Josh's working blends | `Desktop\query.blend` (his correction file), `Desktop\Operation Marine\*.blend` (large: base_jumpack.blend 191 MB) |
| Mechadendrite assets | `Desktop\tubes, pipes, chains\` |

**Installed now (md5, first 8):** TIOW Inbox 1.17.8 `688d6f96` (bridge + Blender add-ons), bridge README
`256a6a0f`, `_library.json` `c43457c7`, page `86e7d95b`, page README `3ed66060`, `share_server.py` `fdd1c5d1` + `Share Squad Builder.bat` / `- people.bat` / `Build received models.bat`, `build_index.py` `81b27aee`, `prepare_builder.py` `47521b31`,
`_builder\index.json` `aca76380` (6,496 parts, all with previews; Prepare run by Josh Nov 6, pad fix Nov 8, the 45 insert parts and the 325 re-filed Marta parts Nov 9 written in place; ASCII-escaped compact JSON), `_builder\no_fit.txt` 1,229 parts, `_sources.csv` `4422836b` (6,819 rows: +323 Springles / Redwarden Nov 9, not in the index until Josh runs Prepare; +45 inserts), `_hidden.txt` `8360ab52` (Josh's edits),
Finalise 0.3.3 `5aea4027`, `Caliper Swap.bat` + `caliper_swap.py` (page folder, `aaa99390` / `0f51acbf`). Josh restarts Blender after an add-on change.

## How the work is done

- **Staging:** `device_stage_files` copies into `/mnt/user-data/uploads/<d | Desktop | new cults ...>/...`. At most
  7 folder levels below a connected folder: for deeper files, `tar czf` them (device_bash) into a connected folder
  (e.g. `D:\Kitbash Library\_backups\<task-date>\`) and stage the archive. Large blends: stage only when needed.
- **Disk:** the container allowance is ~44 GB. On "no space left on device" delete your own old outputs (test
  `.blend1` copies, renders), never Josh's files.
- **Delivering:** write the files under `/mnt/user-data/outputs/<task-date>/...`; first check on the PC that the
  files you will replace still have the md5 you based the work on (Josh edits `_hidden.txt` from the page);
  back up (`_backups\<task-date>\` in the library, `old-<version>\` in the bridge folder); `mkdir` new folders with
  device_bash; `device_commit_files`; md5-check every file on the PC.
- **The page index:** update `_builder\index.json` in place so Josh needn't run Prepare: changed parts get
  `build_index.part_data(new sidecar)` (fits, sockets, exact, adaptor); new parts come from
  `build_index.build(minilib)` (a folder with their files and a `_sources.csv`), merged in with their previews;
  write it back compact (`separators=(",", ":")`, `ensure_ascii=True` since Prepare's Nov 6 run; check it round-trips
  byte-identically first, `kits/inserts/merge_index.py`). Previews need `fast_simplification` (pip) or they come out holed.
- **Josh's corrections in a blend** (`kits/corrections/query-*`): list the parts (`list_src.py`), rebuild the same
  model with TIOW in the container and compare each part to his relative to the torso (`rebuild.py`), so TIOW's own
  rock/settle/base rise isn't mistaken for his moves; then save with TIOW's `correct_socket` / `correct_part`
  (`both=False`, `folder=False`, `correct.py`) and rebuild again to confirm 0.00 mm.
- **Tests: a subset only** - the parts a change can affect, a few Blender models (`tests/<task>/t_*.py`, run with
  `/home/claude/bpyenv/bin/python t.py -- args`) and the page tests for the steps touched
  (`squad-builder/test/t_*_step.js` against a served test library: `_builder/index.json` staged from the PC, the
  previews it needs, `_hidden.txt`).
- After each task: commit + push, add an entry to `docs/project-notes.md` (top of the dated list), copy it to the
  Project doc `claude/part-sockets-tiow-integration.md`.

## Josh's standing rules

- STLs never go in the repo; sidecars yes. No mesh-derived caches (npz, bin, previews) either.
- Test only a subset of the parts a change affects; don't re-run every suite (usage).
- Never write TIOW's `config.json`.
- Delete only your own temp files or files Josh approves; deletes on the PC need `device_request_delete_permission`.
- Stage each delivery under a new path and md5-check it on the PC.
- Never `pkill -f`.
- Bionic legs are on hold: don't deliver 1.18 or Finalise 0.3.2.
- Ask clarifying questions before heavy work when that saves effort; ask Josh to save smaller files rather than
  copying huge blends.
- Renegade chapter: no aquilas, purity seals or scrolls (the hidden list; sculpted-in aquilas get added by path).
- Keep usage low: Josh is on a usage budget.
- The repo is public: nothing that identifies Josh in it (no surname, Windows username or other personal details; home
  paths as `~\...`, which the device tools accept). The claude.ai Project and memory are private.

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

## Open items (oldest first)

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

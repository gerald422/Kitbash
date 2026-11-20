# 117 - The new Mar Fil reference; the reader takes the file's structure (Nov 19-20)

**What was wrong.** Josh's checks of the cut-only marines (bionic wrists, combi weapons, Assault type-a arms, the
Intercessor wrist, pauldrons on one arm type, some shin pads upside down) came from the reference, not the search:
parts had been moved / reused after their cuts were taken (15 cuts with no part under them, 6-80 mm away), and the
"put back under cuts" copies Claude added on Nov 19 were read as Josh's placements on one side of each joint only.
Each cut's turn on its own part is fixed (2 deg); the wrong joints were the pairings.

**The new reference** (`~\Desktop\mar fil connectors\Kitbash reference NEW (starter 2026-11-19).blend`, Josh's):
- `PARTS - edit here`: maker > part folder (the part, each once, seated on the others) > `<part> cuts` (its cuts,
  parented to it: move the part and its cuts follow).
- `FIT CHECKS - show one`: joint > one folder per fit = locked collection-instance views of the two part folders; the
  status in the name (done / CHECK / TO CUT). A fit check = show one folder. Views only show: edit the PART.
- Built from the old file (read only) by `starter.py` (scratchpad): every cut's part put under it by the cut's own
  triangles; checked: the reader reads it as the old file (25/29 joints identical, the 4 pad joints 0.055 mm / 0.15 deg).
- Josh's fixes (Nov 20) were made on the views (hammer seated, Intercessor pad turned): baked into the parts; the pad
  split into one per arm (`(on Arm 2B R)`, `(on Intercessor Arm 5 R)`); the bionic cut tidied (`Bionic weapon wrist`).

**Reader** (`reference.py`, commits caf5193e, 7d50a3b2, 302cecac, abab127f):
- Claude's put-back collection is never read. A cut's part is the part it is parented to; a cut whose part was moved
  gets its file found under the cut (in memory). A cut takes its joint only from a part seated within 0.5 mm, or the
  other part of its fit check (up to 3 mm, noted over 0.5). Placed pads / weapons are read from the copy in a fit with
  the joint's main host. Shin sides from the legs' own frame.
- `--ref "main.blend;setup.blend;..."` reads several files as one; part names / types from `_sources.csv` and the
  sidecars, so a cut-only page index hides nothing.
- Next run's joints ready: hip plate (`legs plate spot`), plate hang (`hip plate hang spot`), buckle (`legs belt
  front`), backpack topper (`backpack top`); two-handed guns / melee and heavy weapons on the shoulder.

**Squad Builder cut-only** (notes 116): `_builder\cut_only.json`. prove.py takes its part list from the page index,
so a run switches cut-only off for the minute it reads the list (`cutonly_switch.py off/on`, scratchpad).

**Run 26** (the new reference, all of Mar Fil, 859 parts, left files too): the same matches as run 25 (the cuts are
the same), the pairings fixed. Written Nov 20 02:29: 724 sidecars, 123 near flagged; backups
`_backups\connectors-joints-2026-11-20\before`. Changes against run 25: wrist frame 5.4 deg on both sides (sockets and
fits together), necks 1.2 deg, pads up to 1 deg, the Intercessor pad and bionic weapons new; three legs' shin spots
moved (Assault Legs 4A's left shin was on the right; Jump Chaplain Legs D and Intercessor Legs 22: check).

**Set up for Josh to cut** (TO CUT fit checks): in the main reference (two-handed Bladeguard / Veteran, Techmarine
backpack, hip plate, plate hang, buckle, backpack topper), and three setup files (Turtle Ninja per armour mark 74
fits, Springles 11, Marta 10: `Kitbash reference - <maker> setup (TO CUT 2026-11-20).blend`, built by
`build_maker_setup.py`, scratchpad). Read with the main file via `--ref "main;setup"`.

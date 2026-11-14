**Item 3 (fit the parts that have none): `kb.carry` run over the library's own unfitted arms, legs, torsos, heads and pads (Nov 14). 80 Turtle Ninja torsos got their sockets and 1 arm its fit; the rest cannot be carried and need a reference each.**

Count first (Nov 14, the library itself): 6,887 sidecars, 2,373 with no fit (torsos: no sockets). The five types tried
here hold 1,191 of them (Chests 703, Heads 287, Arms 84, Legs 58, Shoulder Pads 59); 1,112 have their STL beside the
sidecar and were run.

- **Runner**: `kits/nofit/carry_library.py` (its docstring is the procedure): `ext` and `shapes` (box sizes and
  surface samples of the 2,502 fitted parts, kept on C: so many Blender processes can share them), `run` (the unfitted
  parts: folder-mates first, then the same maker's fitted parts elsewhere, heads then the head rule), `again`, `loo`
  (leave-one-out through the same code), `report`, `test`, `build`. Shards (`--shard I/N`) run side by side; a
  stopped run carries on. Blender's KD tree makes a maker-wide match about 150 s a part: the whole run was 12 CPU-hours
  (about an hour on 21 processes). Results stay in the work folder as `run-*.jsonl` (every part, what was tried, why not).
- **`kb/carry.py` changes**: any fit type can be carried (not only arms / legs: `joints`, `RADIUS` Heads 4 mm,
  Shoulder Pads 8 mm, others 6); the whole-shape match is worked out once a reference and reused for each joint;
  `like(..., mode="rigid" | "turn")` carries every joint that way whatever the references' own relation says;
  `Ref.mirrored()` keeps a subclass. `tests/creator/t_creator.py`: `"check"` (library parts to measure too: what hangs
  on a new torso).
- **Leave-one-out, which source can be trusted** ("right" = within 0.5 mm and 3 deg of the library's own; the note 091
  check left out every torso with `upright`, i.e. all of Turtle Ninja's):
  | source | kept joints | right |
  |---|---|---|
  | torsos, folder-mates (TN `turn` 60, TN `rigid` 18, Mar Fil / Old Style `same` 114) | 192 | 192 |
  | torsos, same maker elsewhere | 24 | 24 |
  | TN torsos, every joint forced `rigid` (folder-mates) | 224 | 224 (worst 0.24 mm, 0.4 deg; `upright` worst 0.2 deg) |
  | legs, folder-mates | 25 | 25 |
  | arms, folder-mates | 65 | 62 (wrong: a CyberBrush fist 5.6 deg, two Marta arms 11.9 deg and 18.5 mm) |
  | pads, folder-mates `same` / `turn` | 9 | 9 |
  | pads, folder-mates `rigid` | 53 | 43 |
  | heads, folder-mates | 35 | 34 |
  | arms / heads / pads / legs, same maker elsewhere | 5 / 9 / 12 / 1 | 4 / 4 / 7 / 1 |
  | head rule (helmet 1's neck ring) on the library's fitted heads | 50 | 27: right on Redwarden, Springles, WargamesPrint (the makers it was built on), wrong on every TN, BBoosty and CyberBrush head and on Mar Fil's bare heads |
  So `POLICY` in the runner uses: torsos from folder-mates or the same maker; arms and legs from folder-mates; pads
  from folder-mates in `same` / `turn` only; no head source at all. Arms from folder-mates are 95%, not the "every
  time" of note 091: look at a carried arm once.
- **Posed torsos** (`again`): a Turtle Ninja torso beside its folder's one-pose torsos first got only its waist
  (`turn`: the shoulders and neck sit turned on it). The missing joints are matched once more with turning (`rigid`,
  region <= 0.10 mm, references agreeing): 58 torsos went from 2 joints to 6, 22 more to 4-6. `upright` comes from the
  reference, moved with the waist joint, so legs under a posed torso stand straight and the chest keeps its pose.
- **A torso is used only with both shoulders, the neck and a waist** (nothing can be built on fewer): 80 are; 92 more
  Turtle Ninja torsos got 1-3 joints (53 only `Back`) and are left as they were.
- **Result, what was written**: 80 torsos (Turtle Ninja - Heresy 76: Mk7-8 46, Mk6 Assault Addon 17, Mk2 / Mk3 / Mk6
  13; Turtle Ninja - Tacticus Mk10 4; 76 from folder-mates, 4 from the same maker), region match median 0.085, worst
  0.118 mm; 1 arm (`Marta Sep 2026 - Thicc Arm 9 Fist Open`, `turn`, 0.05 mm). Nothing for legs (52), pads (56),
  heads (277), the other arms (82), 564 torsos.
- **Why the rest got nothing.** Marta has no socketed torso (259 tried) and no fitted head (250) to carry from; many
  of her "arms", "legs" and "pads" without a fit are accessories filed by folder (BA Accessories, holsters, packs),
  and the real ones are no near-copy of a fitted mate; BBoosty torsos (5) likewise. The remaining 338 Turtle Ninja
  torsos nearly all sit beside socketed ones but match none of them within the gate (other designs and poses).
- **Marta's heads share one frame** (sheet of 22: Y up, face to +Z, a ball for a neck, not a ring; one was a whole
  figure filed as a head): the head rule turned them to any heading (259 "passed" its 0.30 mm gate; within a folder
  the fits were 5 to 178 deg apart), so none was used. One Marta head placed by eye (Adjust on the page, Save fit)
  is enough to carry to the rest without turning: `carry.like("Heads", ..., mode="turn")` with that head as the
  reference.
- **Blender** (`test`: TIOW Inbox as installed, 8 torsos = the 4 loosest and 4 across the range, each with Mar Fil
  Legs 1A, Arm 1A R, Arm 7B R and Helmet 1 on it; the arm on Mar Fil Torso 1): every part placed and touching
  (closest 0.00-0.25 mm), no failures; sheet looked at.
- **Delivered** (`carry-nofit-2026-11-14`, `kb.py apply`: 83 files, md5s match, backups in
  `_backups\carry-nofit-2026-11-14\before`): 81 sidecars merged with `kb.sidecar.merge` (each carried joint's note
  names its reference, mode and match), the index updated in place, the arm's line out of `no_fit.txt`. Sidecars
  exported to `library/` (with 7 of Josh's own changes since the last export); `installed.json` recorded.
- **Not done / limits**: no full `Run checks.bat` (golden squads use none of these parts); the 80 torsos have not been
  seen by Josh on the page; add-a-maker's `"like"` does not write a torso's `upright` or do the `again` pass yet (the
  runner does); a pad rule pass over the 56 pads (pad 62 with scale) was not tried; types other than the five (Two-
  Handed Held 332, Hand-less Weapons 238, Accessories 105, ...) were not run: their fits also carry `offHand` /
  `pivot`, which `kb.carry` does not move.
- **Next for "all fitted up front"**: references, not more matching. In order of parts unlocked: a Marta torso rule
  or one socketed Marta torso a family (259 torsos, and everything that hangs on them); one Marta head by eye (250
  heads); the Turtle Ninja flat-torso rule (`kits/tn`) on the 338 that match no socketed folder-mate, or a few more
  socketed by hand as references and `run` again.

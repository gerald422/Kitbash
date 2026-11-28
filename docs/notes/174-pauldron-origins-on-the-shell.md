# 174 Every pauldron's origin on the shell (Nov 26-28)

**Outcome:** all 273 pauldrons Josh kept are written. Each STL's origin is now the shell's crown, which is Arm 2B R's Pad R frame, and its fit is none (identity). Every pauldron therefore shares the same point and roll.
- **Right pauldrons:** Pad R (227).
- **Left-only pauldrons:** Pad L (46), the mirror image of how Josh set them.
- **Read-back:** each pauldron was placed from the library on Pad R and compared with his file. The worst error was 0.0004 mm, on Springles files whose original origin was about 1.3 m away.
- **Backups:** `_backups/origins-pads-2026-11-28` (5-part trial) and `-2` (268). Undo with `kits/connectors/origins.py -- restore <task>`.

## How we got there
1. **Carrying a fix across a pack** (`kits/seat/carry_by_shape.py`).
   - Adding Josh's move (`batch.py apply --delta`, plus the new `FROM_ID@KIT` option) failed. Each maker's STL has its own origin, so the same turn lands differently on every file. Mar Fil works only because a pack shares one origin.
   - His contact patch against the whole pauldron failed: inside points snapped to the outside, and a dome patch slides.
   - The top of the pauldron (outside) failed on Chains and Dots.
   - **What worked: the inner surface.** Faces looking at the dome's centre and seeing it, matched inner to inner, scored both ways. One way under 0.025 mm also counts: one inside containing the other.
   - Pauldrons of a type share the inside curve, with details sculpted on top. Matches were 0.000-0.03 mm, and "Alt" versus plain Iron Hands are two insides.
   - Josh seated one per row in two passes, giving 50 seats. The rest were carried and he checked them.
2. **Mating origin from shape alone** (`kits/seat/mate_frame.py`): centre and +Z from the inner surface, spin from its outline.
   - It agreed with the inner-surface carry on only 48 of 120. The misses were 180 or 90 degree spins: pauldron insides are near round (axis ratio 1.04-1.11).
   - Part Sockets' Set Origin at Flat has the same limit; its roll is arbitrary.
   - So the spin comes from Josh's seats, not the shape.
3. **One arm** (`kits/seat/one_arm.py`).
   - Every pauldron went into the one shell on Arm 2B R, each keeping its place in its own shell to 0.0001.
   - Accessories and the Lion Knight shoulder shields were left out.
   - Each pack has its own collection, all off, to switch on one at a time.
   - Josh hand-checked every one. He deleted 31 that he will never use or that were heads.
   - His rule: "everything needs to be seated from this file only". The only fit kept as it was is Mar Fil Assault Shoulder Pad 1, the reference. Every other one was unlocked, including the earlier-written Marta Jul 2025 Pad 1, and rewritten.
4. **The write** (`kits/seat/pads_origin.py`: plan, then write, then check).
   - **Fit:** each pauldron's fit is its place in that file against 2B R's written Pad R (as `on_written_socket`). New fits only: older pad fits, notes and the Outriders' old `check` lists were dropped.
   - **Origin:** the file is moved by its fit (`kb.origin`), the same as origins.py, notes 101.
   - **Scale:** `kb.origin.move` takes `scaled=True` for parts with a `scale` (62: BBoosty, Springles). Fits and `from_file` stay in scaled coordinates, and the STL moves by `raw_move` (the shift divided by the scale). Page previews are scaled, so they move by G.

## Notes
- **Golden run:** `tests/golden/run.py` reports 111 of 140 parts differ, including arms, legs, heads and bases this run never touched. Its snapshot predates the stage 1-4 rewrites, so it needs a new baseline before it can judge changes.
- **Josh's plan from here:**
  - A new pauldron is matched once to the shell, or to a seated pauldron with the same inside, and takes the origin.
  - Arms carry the shell's place per arm type (Pad R, from the arm-type file).
  - The same pattern follows for shin pads, wrist armour, torsos and other hung parts.
- **Still open:**
  - Arms' Pad R per arm type. Only 2B R's is written, so pauldrons sit right on 2B R and its same-shoulder arms first.
  - The 31 deleted pauldrons are still in the library with their old fits (hide list or heads stage: Josh's call).
  - The shields.

# 161 - BBoosty to heresy scale; Josh's Springles move on every Springles arm (Nov 25)

**BBoosty x1.1.** Josh: "bboosty and springles are both heresy scale so would need to go up by 10% if they havent
already been adjusted".
- Springles already was: its sidecars carry `scale` (1.1, arms 1.133 after the Nov 18 +3%, notes 029, 114), and the
  batch builder applies it.
- BBoosty had no scale. `tools/rescale_maker.py "BBoosty - Heresy" 1.1`: all 256 sidecars (library and repo mirror)
  get `scale` 1.1. Every socket's, fit's, offHand's and pivot's move goes x1.1 with it (245 positions), and so do the 10
  mirrored accessory variants' own sidecars, since TIOW reads a variant's scale from the variant. Each joint keeps
  its place on the mesh and the part grows about it; a `notes.Scale` line says so. Backup:
  `_backups\BBoosty - Heresy scale 2026-11-25 2158\before`. The golden baseline's BBoosty parts will show as changed.
- The first BBoosty files (21:51) were built at the old size. They are replaced by `... BBoosty right arms
  (2026-11-25 b)` (24) and `... left arms (2026-11-25 b)` (14). The arm builder starts from the library fit, now
  scaled, so each arm grows about its old shoulder joint.

**Josh's Springles move.** Josh: "i have just adjusted one arm in this set. Can this change be applied to all of the
springles sets". He moved Pattern C Duel Melee Arm 1 R by 0.82 mm, (0.30, 0.52, 0.56) in Torso 2's axes, no turn.
With the 0.32 mm pre-set the starting shift is now (0.62, 0.52, 0.56) on every Springles arm (`--shift`):
- `... Springles right arms 1 (2026-11-25 b)`: pattern C right, 25. Duel Melee Arm 1 matches his file to 0.0001 mm.
- `... Springles pattern P right arms`, `... pattern S right arms`: 25 each.
- `... Springles pattern C / P / S left arms`: 23 each, as mirror images.

That is all 75 right and 69 left Springles arms. Renders: 5 columns each of BBoosty right b and Springles S left sit
at the shoulder.

A check gotcha: a built part's object sits on its pivot with the start baked into the mesh, so compare placements as
`matrix_world @ kb_own_in_obj`, not `matrix_world`.

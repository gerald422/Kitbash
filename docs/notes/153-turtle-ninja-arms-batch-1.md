# 153 - Stage 3: Turtle Ninja arms, batch 1 (a spread) (Nov 25)

Josh: "Turtle Ninja arms".

**What's left to do (Tacticus and Heresy):** 94 right and 71 left plain arms without an exact fit. Excluded: none
hidden, none in Rigging Required, nothing on `not_arms.txt`. The 28 two-handed parts wait for the two-armed stage.

| Sets | Right | Left |
|---|---|---|
| Mk10 Assault Intercessor + Jumppack (Tacticus) | 50 | 10 |
| Mk4 Tactical Squad Weapons | 21 | 23 |
| Mk7-8 Assault Intercessors | 12 | 6 |
| Mk6 Addon 1 (poses A-C, 3 each side; its Arms folder 21 left) | 9 | 30 |
| Legion Moritat | 1 | 1 |
| Librarian Custom | 1 | 1 |

**Batch 1:** `03 Stage 3 - Turtle Ninja right arms 1 (2026-11-25).blend`, 25 right arms spread across the sets
(Moritat 1, Librarian 1, Mk4 5, Mk6 poses 3, Mk7-8 5, Mk10 10). Each starts at its old seat. As with Marta (notes
149-152), Josh's fixes here show whether one repeated move can be carried to the rest (`apply --delta`, then
`make_arm_batch --shift`).

**Renders:** all 25 sit at the shoulder. "Mk4 Tactical - Merged Bolter D1 Arm D2 R" is an arm and bolter sculpted as
one piece, and its live mirror crosses in front of the chest. It may be one for `not_arms.txt` if Josh removes it.

## Marta's offset on every TN arm (Josh, Nov 25)

Josh: "can you give all TN arms the same offset that the marta arms got please".

His TN file had no saved change (read: all 25 unchanged). So it was left alone, because he may have it open (notes
148), and a new file was built instead: `03 Stage 3 - Turtle Ninja right arms 1 (2026-11-25 b).blend`. It has the
same 25 arms with `make_arm_batch --shift 0.32,0,0`, Marta's 0.32 mm outward on the spacer (notes 150-152).

A dry-run write gives every fit 0.307-0.334 mm from its old one. Every later TN arm file (69 right, 71 left) gets the
same `--shift`.

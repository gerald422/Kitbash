# 123 - Stage 2: the Assault torsos batch (Nov 24)

First torso batch, for Josh to fix:
`~\Desktop\mar fil connectors\batches\02 Stage 2 - Assault torsos (2026-11-24).blend`.
Spec `kits/seat/batches/02-assault-torsos.json`, made by `kits/seat/make_torso_batch.py`.

**Layout.** Each torso stands in its own column, 80 mm apart:
- **Reference column** (x = 0): Torso 2 with Josh's reference pieces, all locked.
- **The other columns:** Torsos 1, 2 Insert, 3, 4, 5, 6.

On each torso:
- **The spacer** on `Shoulder R`, which Josh moves. Arm 2B R rides on it by its written fit, and the guide and Shoulder
  Pad 1 ride on the arm by theirs. The left side is the live mirror across that column's own torso.
- **Helmet 1, Back Pack 1 and Legs 1A** on `Neck`, `Back` and `Waist`, which Josh moves. Each is carried by its pose
  on Torso 2 in the reference file, his own placement.

This is a socket batch (PLAN Rule 3). The pieces and their fits are known-good, so a piece's move is that torso's
socket. `batch.py write` gained halves:
- `half: socket`: socket = the moved pivot;
- `half: fit`;
- `half: both`.

The reference column is written as `both`: Torso 2's Neck, Back and Waist stay as they are, marked as Josh's, and each
piece's fit becomes his reference placement. The library's old fits are off that placement by 1.2 deg (helmet),
0.1 deg (pack) and **9.5 deg / 0.67 mm (Legs 1A, an 80% "look" cut fit)**. So every socket is judged with the fits
that will be in the library.

**Where each piece starts (Claude's seat).** Josh's Torso 2 cut surfaces in the reference file (`Assault Torso
Shoulder / neck / waist`, `Assault torso back`) are fitted onto each torso by trimmed ICP, and Torso 2's socket is
carried by that fit. This matches the cut's shape only.
- **Torsos 1 and 3-6:** every cut lands at rms 0.000-0.002 mm, so it is the same sculpt there. Shoulder, Back and
  Waist come out within 0.01 mm and 0.07 deg of their old rig ("3rd attempt") sockets. **Neck is 0.11 mm / 2.5 deg
  off the old one on all five:** Josh's neck cut disagrees with Mar Fil's rig there.
- **Torso 2 Insert:** no cut lands (rms 3-6 mm). It keeps its own sockets, which were cut sockets already. Its helmet
  starts 0.4 deg off Torso 2's.

**Checks.**
- Every mesh matches its recorded frame (worst 0.0013 mm over 56 pieces).
- The reference column matches the reference file at 0.00.
- On Torsos 1 and 3-6, every piece sits as on Torso 2 (0.00-0.01 mm).
- A front render was looked at (`02 check - reference and Torso 1.png` beside the batch).
- `write --check` on the untouched file lists the expected socket writes.

The first build had the reference column and Torso 2 Insert both as id `t2`: the mirrors were doubled and the carry
used the wrong torso. It was caught by the render. That file went to `batches\_superseded\`, and `build` now refuses
duplicate ids.

Next: Josh fixes it, then `read`, then `write`. Then the other torsos (Intercessor, Veteran, Bladeguard, Outrider,
Chaplains, Techmarine; Redwarden; Turtle Ninja straight), and the new sockets (Chest Insert, Neck Guard, cloak).

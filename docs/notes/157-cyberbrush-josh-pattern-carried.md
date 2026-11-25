# 157 - CyberBrush arms: Josh's pattern carried (Nov 25)

Josh, on the CyberBrush left-arms file: "there is a pattern of changes ive been doing can you try and replicate it
across all the arms please and also give the marta spacing as well please".

**His changes** (saved 18:11), each in the arm's seat frame (the same as its own pivot frame here):

| Arms | Change |
|---|---|
| Claws 1 (1)-2 (3) (7) | turn 2.4-5.2 deg about seat -Y, lift 0-1 mm along seat Z (median: 3.4 deg, 0.58 mm) |
| Fists 1 (1), 1 (2), 2 (5), 3 (1), 3 (3), 3 (4), 4 (2) | a spin about seat X, the spacer axis, of 22-92 deg each |
| Fists 1 (5), 2 (1), 2 (2), 2 (4), 4 (5) | a spin, the claws' tilt and lift, or both |

**The repeated part:** the claws' tilt and lift. The fist spins differ from arm to arm, so there is no one value to
copy. So the change copied is Claw 1 (4)'s, which is the median, 0.580 mm / 3.40 deg. Per arm it goes in the seat
frame, new = on . C . on^-1 . old, and only on arms Josh hadn't moved:
- `03 Stage 3 - CyberBrush left arms (2026-11-25 b).blend`: the 16 untouched left arms (Claw 2 (4), Fist 1 (4),
  Guns, Knives, Shields). His 19 placements are kept.
- `03 Stage 3 - CyberBrush right arms (2026-11-25 b).blend`: all 38 right arms (same right spacer, same frame).

**Marta's spacing:** both files were built with `--shift 0.32,0,0` (notes 156), so every arm already has it and
the copied change goes on top. The originals are left alone in case either is open.

**Renders:** in the left b file, the carried arms sit like his claw, and the guns, knives and shields are at the
shoulder.

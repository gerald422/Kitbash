# 155 - TN right arms 2 written; Josh's Mk10 fist change carried (Nov 25)

Josh: "right arms are fine. on the left arms can you make the same changes that I have made to the power fist but
also make sure the offset is the same as the others".

**TN right arms 2: written.**
- The Shoulder R fit of 61 arms, with the 0.32 mm pre-set.
- 62 sidecars, with Torso 2 unchanged.
- Every joint read back at 0.0000 mm.
- Backup: `_backups\batch write 2026-11-25 1631`.

**His change in the left file** (saved 16:29): only Power Fist 1 moved, 7.96 mm and 161.4 deg in its seat frame,
from the start it had been given at Power Fist 6's seat (notes 154).

**Carried** (scratch script, the same maths as `apply --delta`): into
`03 Stage 3 - Turtle Ninja left arms (2026-11-25 b).blend`.
- His change C, taken in the seat frame, goes on Power Fist 2-5 and Power Fist Relaxed 1-5, the ones that started
  the same way: new = on . C . on^-1 . old.
- Then "the offset the same as the others": 0.32 mm outward along Torso 2's X on all ten fists, Power Fist 1
  included. His original file is untouched.

**Renders:** fists 1-5 and Relaxed 1-5 now all hold the fist forward the same way.

**Open:** Power Fist 6 and Relaxed 6, filed with a proper left fit, still look the way Power Fist 1 did before his
fix. Fist 1 started from 6's seat and needed the 161 deg turn, so 6 and Relaxed 6 are probably the wrong way round
too. They are unchanged until Josh says.

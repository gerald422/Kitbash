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

## Power Fist 6 and Relaxed 6 too (Josh: "Yes, add them")

The same change C, taken from his file, plus the 0.32 mm outward, now also goes on Power Fist 6 and Power Fist Relaxed
6. They are in a new file, `03 Stage 3 - Turtle Ninja left arms (2026-11-25 c).blend`, built from b. The b file and
his original are left alone in case either is open.

Renders: all twelve Mk10 fists now hold the fist forward the same way.

So 6 and Relaxed 6, filed with a "proper" left fit, were the wrong way round as well. The whole Mk10 fist set was
filed wrongly: fists 1-5 with a right fit, and 6 with a left fit that was turned wrong.

## TN left arms written (Josh: "i have made some amends to the fists. They are ready to go now")

His amends were in the c file (saved 17:14). The twelve Mk10 fists moved from where they were built: 7-8 mm and
161-179 deg for fists 1-5 and Relaxed 1-5, and about 0.5-0.8 mm with the 161 deg turn for 6 and Relaxed 6. He fine-
tuned 3, 5 and Relaxed 2-5 on top of the carried change. The other 69 arms were unchanged.

**Written:**
- The Shoulder L fit of all 81, each the left image of its placement.
- The 10 wrong-side Shoulder R fits dropped (fists 1-5, Relaxed 1-5).
- 82 sidecars, with Torso 2 unchanged.
- Every joint read back at 0.0000 mm.
- In the library, Power Fist 1, 6 and Relaxed 3 now have only `Shoulder L`, in `exact`.
- Backup: `_backups\batch write 2026-11-25 1715`.
- Every TN left-arms file (original, b, c, .blend1s) went to the Recycle Bin.

**Every Turtle Ninja plain arm is now on the spacer:** 84 right (23 + 61) and 81 left. The 28 two-handed parts wait
for the two-armed stage.

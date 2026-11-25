# 149 - Stage 3: Marta arms, batch 1 (one per set) (Nov 25)

Josh: "Marta arms" next.

**Scope:** the agreed plan (`docs/PLAN.md`, the makers table) has Marta's arms in. Nov 15 had dropped them
(`cuts_needed.py` `ARMS_FROM`), but the Nov 24 plan, "every existing part goes through the batches again", supersedes
that. `ARMS_FROM` only drives the old cuts list.

**The Marta Tacticus parts with a shoulder fit (none hidden, none exact yet):**
- 107 right plain arms and 60 left plain arms.
- 25 two-handed weapons (Two-Handed Guns / Melee). These wait for the two-armed stage.

**Why a spread first:** the plan's history (item 5) says the old method took each round joint's turn from the file,
so every Marta arm came out turned wrong. If the error is one per-maker turn, Josh's fixes will repeat, and the fix
can be carried across the rest (the method in `docs/PLAN.md`). So batch 1 takes one right arm from each set, and two
from the biggest sets (GURLS, bionics, SALE August 2025): 28 arms.

**The file** is `03 Stage 3 - Marta right arms 1 (2026-11-25).blend`, built by `make_arm_batch.py`. Each arm starts
at its old Shoulder R seat on Torso 2.

**Renders:** the whole set, and close-ups of 9 shoulders. Every arm sits at the shoulder in a plausible pose, and
none is turned right round. The turn on the spacer is for Josh to judge.

**Slip on the way:** the picked list was written by Python in text mode on Windows, so every path but the last
ended in `\r`. The library lookups failed ("no old Shoulder R fit") for 27 of 28 arms. The file was rebuilt with
the `\r` stripped before it was handed over.

**Next:** read Josh's fixes. If they are one repeated turn, carry it to the other 79 right and 60 left Marta arms in
large batches. If not, go set by set.

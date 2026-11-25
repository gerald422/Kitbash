# 152 - Marta arms: the rest, with Josh's 0.32 mm pre-set (Nov 25)

Josh: "Yes, build them" (the other Marta arms, with his 0.32 mm move already on).

**The pre-set:** `make_arm_batch.py --shift X,Y,Z` puts a repeated move of Josh's, in Torso 2's own axes, on every
arm's start, and says so in the arm's note.
- His move in the file was 0.320 mm along X, with no turn (notes 150). Measured from the library it is 0.3155 mm,
  but that includes the stage-1 socket rounding every fit carries.
- So the shift is 0.32, 0, 0. For a left arm shown as its mirror image, it goes on the right side like every other
  arm.

**Two files:**
- `03 Stage 3 - Marta right arms 2 (2026-11-25).blend`: 79 right arms (the 80 without an exact Shoulder R fit, less
  DW Weapon T Ua 1, which `not_arms.txt` leaves out).
- `03 Stage 3 - Marta left arms (2026-11-25).blend`: 60 left-only arms, each shown as its mirror image on the right
  spacer (notes 147).

Sides come from the fit, not the name: some Marta files are named the opposite side (notes 146).

**Dry runs:** a `--check` write on each unchanged file gives every fit 0.317-0.324 mm from its old one: his move plus
the rounding.

**Renders:** 10 left columns look right. One is "Aug 2025 - Arm 4 Clow With Cloak L", a claw arm with a feathered
cloak sculpted on. It is an arm, so it stays in for Josh to judge.

**Still to look at:** DW Weapon T Ua 2 and 3 are in the right-arms file. If Josh removes them as weapons, add them to
`not_arms.txt`.

## Josh's answer, and what was written (Nov 25)

Josh: "belive i made one or two changes on right arm the rest on right and left arm are goof to go".

**Left arms: written.**
- The Shoulder L fit of all 60, each the left image of its pre-set placement.
- 61 sidecars, with Torso 2 unchanged.
- Every joint read back at 0.0000 mm.
- Backup: `_backups\batch write 2026-11-25 1505`.
- The file went to the Recycle Bin.

**Right arms: held.** The saved file (15:02) has no change at all: every one of its 482 objects is exactly where it
was built (0.0000 mm), and nothing was removed. His "one or two changes" are not in it, so they are probably unsaved
in his Blender. A write would lock the fits as exact (Rule 1), so it waits until he has saved, or he confirms there
are none.

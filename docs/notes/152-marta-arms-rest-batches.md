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

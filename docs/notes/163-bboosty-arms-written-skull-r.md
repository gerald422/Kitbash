# 163 - BBoosty arms written; the Skull Paragon Blade R arm left for Josh (Nov 25)

Josh: "BBoosty Praetor - Arm Paragon Blade Skull Shoulder Bolts Versio.001 are the wrong way around", "its correct in
the left arm not in the right arm", "aside from that one fix all of the others are good to go".

**Written** from the two c files (backup `batch write 2026-11-25 2216`): 23 right arms (Skull Paragon Blade R held
back, `--skip a23_arm`) and 14 left-only sculpts (as mirror images). All 37 read back at 0.0000 mm. They are at heresy
scale (x1.1, notes 161) with the 0.32 mm pre-set and Josh's 0.52 mm lift.

**Skull Paragon Blade R:** its STL is not an exact mirror of the Skull L one (213,800 against 262,486 unique vertices,
and laid out elsewhere in the file), so his left placement can't simply be mirrored across. Turning it by guesswork
failed before (notes 158), so it is in a one-arm file for Josh to turn by eye: `03 Stage 3 - BBoosty Skull Paragon
Blade R (2026-11-25).blend` (spec `03-bb-skull-r.json`, 0.32 mm pre-set; the lift isn't on it).

With this, every plain arm in scope (Mar Fil, Marta, Turtle Ninja, CyberBrush, BBoosty, Springles) is on the spacer
but that one. Next in PLAN.md: the two-armed weapons on the spacer (with `kits/seat/not_arms.txt`), then stage 4,
the arms' sockets.

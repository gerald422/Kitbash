# 175 The shell on each arm type by shape (Nov 28)

**Josh's ask:** "try to do a shape match or similar rather then working off of my setups". The shell is every pauldron's origin since notes 174.

**Method:** `kits/seat/shell_on_arms.py`. Its only reference is Arm 2B R's written Pad R (stage 1).
1. **Start:** the shell sits on the torso where 2B R's does. Pads sit on the torso the same whatever the arm (Nov 23), and every arm is on the one spacer (stage 3).
2. **Shape step:** the shell slides along its own +Z until it touches this arm's shoulder the way it touches 2B R's (the 10th percentile of signed distance, -0.52 mm on 2B R).

**Why not the seeded shells:** the arm-types b file's 18 shells seeded from the Nov 23 seat file are 10-85 degrees off this. Rendered with Shoulder Pad 1, the seeded ones were tipped while the torso-relative ones stood upright and consistent, so the seat-file carry is not trusted.

**Result:** `~/Desktop/mar fil connectors/batches/04 Stage 4 - Arm types, shell placed by shape (2026-11-28).blend`
- All 66 shells placed, with lifts -1.7 to +2.6 mm. Josh's own move on Assault 3B R (t5) is kept.
- Two hit the +-4 mm limit: DW Weapon T Ua 2 (a weapon, stage 5) and Aug 2025 Craw Arm 7. Both need checking.
- Not written yet. Josh checks it, then the arms' Pad R is written per type and carried to same-shoulder arms.

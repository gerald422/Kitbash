**Springles arms checked and made 3% bigger; mirrored left side on the sheets (Nov 18).**

- Josh's `~\Desktop\Operation Marine\arms.blend` (all 74 right arms set on the origin, a Springles spacer, the
  `Springles wrist connection` cut) read: 72 arms are their library file moved only (no turn), shoulder flat facing
  -Y. 58 have the flat exactly on the origin; 14 sit 0.2-0.4 mm toward the torso (pattern C duel melee 1, 3, 4, 5,
  heavy 1, 3, 5, ranged 4, 5; P heavy 2, 3, 5, ranged 3; S ranged 5), likely slips. The C and S helmet-hold arms
  match no library file there (no flat on the origin; maybe mirrored). The spacer is a disc 3.9 mm across, from
  y +0.61 (arm side) to -2.08 (torso side). The wrist cut lies on the pattern P unsheathing right arm. Pattern C / S
  slung arm+hand have no `Hand R` socket. Josh's choice: only the spacer, one arm per pattern and the wrist cut go
  into the reference (smaller file); `arms.blend` stays as the check.
- Scale: shoulder flat to wrist cup, straight line, the longest Springles arm (C melee 2) 11.6 mm; Mar Fil Assault
  Arm 1A / 1B shoulder joint to wrist 12.2 mm. The Springles arm is bent at the elbow, so held out it is about 12 mm;
  the two wrist points are not defined quite alike. Josh: add 3%. All 144 Springles - Heresy arm sidecars (library
  and repo `library/`): `scale` x1.03 (1.1 -> 1.133, pattern C 1.1002 -> 1.133206), every socket's and fit's move
  x1.03, so each joint keeps its place on the mesh and the arm grows about it; a `notes.Scale` line says so. Pads,
  helmets and the rest of Springles stay at 1.1. Backup: `_backups\springles-arms-scale-2026-11-18\before`. The
  golden baseline has 3 Springles arms (C Melee 2 L, P Heavy 1 L, S Melee 3 R): they will show as changed.
- `sheets.py`: each marine also gets its left arm, pad and weapon, the right ones mirrored about the torso's waist
  frame (as the left shin pads are), so only right arms need placing. `--types Arms,Melee` renders only those types.

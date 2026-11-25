# 159 - CyberBrush arms written (Nov 25)

Josh: "all now good to write apart from CyberBrush Bug Hunters - Spear Arm 1 in right arms as its two handed which is
why it doesnt fit".

**Written** from the two b files (`kits/seat/batch.py write`; backup `batch write 2026-11-25 2144`):
- **Right:** 37 arms as Shoulder R fits. Spear Arm 1 was held back (`--skip a30_arm`).
- **Left:** 35 left-only sculpts as Shoulder L fits, each fixed as its mirror image on the right spacer.
- **Read-back:** all 72 joints placed from the library (socket . fit) match Josh's files at 0.0000 mm / 0.000 deg.

**Spear Arm 1** is the glaive. It is two-handed, which is why it never seated as a one-arm part; note 158 had taken
Spear Arm 2 to be the glaive. Spear Arm 1 is now in `kits/seat/not_arms.txt` for the two-handed weapons stage.

**Fist 4 (1) and Fist 4 (4)** (right) went in as they were in the b file: only the carried claw change (3.4 deg,
0.58 mm). Josh passed them as good to write. If they turn out to face the wrong way, a new batch with `redo` replaces
them.

All CyberBrush arm batch files (originals, b files, .blend1) went to the Recycle Bin.

Every CyberBrush plain arm is now on the spacer. Next: BBoosty and the other makers' arms, with `--shift 0.32,0,0`.

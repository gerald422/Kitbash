# 154 - TN right arms 1 written; the Mk10 Power Fists are left arms (Nov 25)

Josh, on `03 Stage 3 - Turtle Ninja right arms 1 (2026-11-25 b).blend`: "the mark 10 power fists look like an
incorrectly mirrored arm as its the wrong way around. The rest are good on tn right arms 1".

**Written:**
- The Shoulder R fit of the other 23 arms, with Marta's 0.32 mm (notes 153).
- The two fists (Power Fist 1, Power Fist Relaxed 1) were held back with the new `write --skip ID,ID`.
- 24 sidecars, with Torso 2 unchanged.
- Every joint read back at 0.0000 mm.
- Backup: `_backups\batch write 2026-11-25 1525`.
- Both TN right arms 1 files went to the Recycle Bin.

## The Mk10 Power Fists

In the Mk10 Assault set:
- Power Fist 1-5 and Power Fist Relaxed 1-5 were filed with a Shoulder R fit.
- Power Fist 6 and Relaxed 6 have a Shoulder L fit.

Josh saw 1 and Relaxed 1 the wrong way round on the right, so all ten are taken as left sculpts with a wrong-side fit.

**The tools:**
- `make_arm_batch --left`: an arm with no Shoulder L fit but a Shoulder R one is taken as a left sculpt filed with a
  right fit. Its mirror image starts at that old seat, and its write gets `"drop": "Shoulder R"`.
- `batch.py write`: after the merge, a dropped fit is removed from `fits`, `exact` and `notes`, and the log says so.
  The new Shoulder L fit is written as for every left arm (notes 147). TIOW then mirrors it for the right side.
- That old seat was a poor start: fists 1 and 3 and Relaxed 1 sat low and out of place. So each fist starts at its
  set's properly filed one instead: Power Fist 6's seat for 1-5, Relaxed 6's for Relaxed 1-5. Renders put them at the
  shoulder like 6.

**Files rebuilt** (built 15:21 and 15:23, never opened by Josh):
- `03 Stage 3 - Turtle Ninja right arms 2 (2026-11-25).blend`: 61 right arms, without fists 2-5 and Relaxed 2-5.
- `03 Stage 3 - Turtle Ninja left arms (2026-11-25).blend`: 81 left arms, the 71 plus the 10 fists.

Both have the 0.32 mm pre-set. Dry runs: every right and left fit is 0.30-0.35 mm from the old one, and the 10
wrong-side fits are dropped.

# 144 - Stage 3: the Intercessor arms batch (Nov 25)

Josh: "Yes, build it". The file is `03 Stage 3 - Mar Fil Intercessor arms (2026-11-25).blend`, built by
`make_arm_batch.py` like batches 1 and 2. Each arm starts at its old seat, because Josh made no correction in the
earlier batches.

**In it:** the 32 right arms in the Intercessor kit's "Arms" folders that don't yet have an approved (exact)
Shoulder R fit:
- Arms 1-6 R
- the 19 single bolter arms (Bolter-Individual)
- Desolator 1
- Plasma Incinerator 4A R, 4B R, 5 R and 6
- Pyreblaster 7 and 9A

None has a mirror variant, so only Shoulder R fits are written.

**Not in it:** about 70 more Intercessor parts have a Shoulder R fit but sit in the "Two-Handed Guns" and "Heavy
Weapons" folders: the two-handed bolters and the Desolator, Plasma and Pyreblaster heavy weapons. They belong to the
two-armed weapons stage.

**Checked:** front renders of Arm 1 R, Bolter A1 R, Desolator 1, Plasma Incinerator 4A R and 6, and Pyreblaster 7.
- Each sits in the shoulder as before.
- Desolator 1 holds its weapon across the body, so its live mirror overlaps it. Judge it by its right side.

After this batch, the arms still to do are the Veterans and Blade Squad (27), the Chaplains (6, by eye) and the
left-only sculpts.

## Written (Nov 25)

Josh: "all changes made good to go". He fixed 4 arms, all grenade bolter arms. Their old seats were turned right
round:

| Arm | Move | Turn |
|---|---|---|
| Bolter A Grenade 3 R | 25.7 mm | 137.6 deg |
| Bolter B Grenade 3 R | 24.4 mm | 178.2 deg |
| Bolter C Grenade 3 R | 26.5 mm | 175.5 deg |
| Bolter C Grenade 1 R | 10.0 mm | 158.8 deg |

The other 28 were unchanged (old seat approved). The four changes are not the same move, so there is nothing to
carry across.

**Written** (`batch.py write`, half "fit"):
- The Shoulder R fit of all 32 arms.
- 33 sidecars, because Torso 2 was loaded and saved unchanged.
- Every joint placed from the library (socket . fit) matched the file at 0.0000 mm.
- The old sidecars are in `_backups\batch write 2026-11-25 1308`.
- The file and its .blend1 went to the Recycle Bin.

**Worth checking later:** the same grenade sculpts' two-handed versions (Two-Handed Guns) may carry the same
turned-round seat when the two-armed stage reaches them.

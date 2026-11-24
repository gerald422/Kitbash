# 125 - Stage 2: the Intercessor torsos batch (Nov 24)

Second torso batch, for Josh to fix:
`~\Desktop\mar fil connectors\batches\02 Stage 2 - Intercessor torsos (2026-11-24).blend`.
Spec `kits/seat/batches/02-intercessor-torsos.json`, made by `kits/seat/make_torso_batch.py` with Intercessor Chests
1-5. The layout is the same as batch 02 (notes 123): a locked Torso 2 reference column, then one column per chest.

**Where each piece starts.** Josh's Torso 2 cuts land on all five chests (rms 0.000-0.002 mm), so they are the same
sculpt as Assault Torso 2 at the shoulder, neck, back and waist.
- **Chests 1-4:** as on Assault Torsos 1, 3-6. The shoulder, back and waist are within 0.01 mm and 0.08 deg of their
  old sockets. **The neck is 0.11 mm / 2.46 deg off the old one.**
- **Chest 5:** the neck is only 0.6 deg off, and the rest within 0.11 deg.

**Checks.**
- Every mesh matches its recorded frame (worst 0.0013 mm over 48 pieces).
- The reference column matches the reference file at 0.00.
- Every piece sits as on Torso 2 (0.00-0.01 mm).
- Renders: `02i check - reference and Chest 1.png` and `02i check - Chest 4 and Chest 5.png`, beside the batch.
- `write --check` lists 25 socket writes and nothing else.

**Generator change.** The first `write --check` stopped: the reference column still asked to write Torso 2's Neck,
Back and Waist, which batch 02 made Josh's (Rule 1). The generator now leaves out a reference piece's write once
Torso 2's socket is protected, so the reference column is written once only. Only the spec changed (`write` reads the
spec), so the built file stands.

`_hidden.txt` hides Chests 1-4 but not Chest 5, which has the eagle. This was left for Josh.

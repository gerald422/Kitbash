# 131 - Stage 2: Turtle Ninja batch 2, with Josh's legs change pre-set (Nov 24)

Josh: "use the legs change". His Turtle Ninja legs fix from batch 1 (notes 129, 130) starts every legs piece in this
batch. It is taken from the library: Mk2 A1's new Waist against its old one (backup `batch write 2026-11-24 2136`),
`D` = 0.616 mm / 18.47 deg. That is identical on every TN torso written (Mk10 agrees to 2e-5).

**Batch:** `~\Desktop\mar fil connectors\batches\02 Stage 2 - Turtle Ninja torsos 2 (2026-11-24).blend`, 17 torsos:
- the Mk7 and Mk8 Jump Pack torsos (A9);
- Mk8 Torso A1-H1;
- Mk8 Torso Short A1-F1;
- Upper 1 L.

Batch 3 is the Mk7-8 Uppers A-Q (16).

`make_torso_batch.py --preset SOCKET=<16 numbers>` puts such a fix on every piece on that socket, using `build`'s
existing `preset`:
- the pivot is `socket . D`;
- the piece is coloured pink and labelled "pre-set" in the file.

If Josh leaves a pre-set piece alone, `read` lists it as changed by D, and `write` writes `socket . D`.

**Where the rest starts.** No Mar Fil cut lands, so every other piece starts on the torso's own sockets, as in batch 1.

**Checks.**
- Every mesh matches its recorded frame (worst 0.0013 mm over 144 pieces).
- The 17 pre-set legs are exactly `D` (0.00000).
- `write --check`: the 17 Waists move by `D`; nothing else moves beyond the mirrored left shoulders' usual
  0.05 mm.
- Renders `02t2 check - ...png` beside the batch.

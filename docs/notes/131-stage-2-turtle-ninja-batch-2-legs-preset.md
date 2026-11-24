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

**Josh's one fix: raise the helmet.** On the Mk7 Jump Pack torso (t1) he raised Helmet 1 by 0.39 mm (0.36 up,
0.14 forward, no turn) and asked for it on the rest of the batch. His Blender now is the instance the MCP add-on
drives, so it was done live in his session, with no on-disk edit or reload:
- each other helmet got `own(torso) . start . D`, to 0.00004 mm;
- then the session was saved (the previous save is the `.blend1`).

`read` from disk: 17 of 17 helmets changed, "the SAME change", and the legs as pre-set. `write --check`: 17 Waist and
17 Neck socket changes, nothing else.

**Written** (Josh: "all done ready to write to library"; his Blender was closed, and the file on disk was the same as
checked). 17 sidecars, backup `batch write 2026-11-24 2144`. All 68 joints read back from the library at
0.0000 mm / 0.000 deg.
- Every Neck: 0.39 mm, no turn (his helmet raise).
- Every Waist: 0.62 mm / 18.47 deg (his legs change).
- Shoulders and Back as they were, marked as Josh's.

**Clean-up as we go (Josh, Nov 24: "remove/archive/delete unneeded files as we go").** From now on, once a batch is
written and reads back exactly, its files go to the Recycle Bin: the `.blend`, the `.blend1`, any copies or backups,
and the check renders. The library's own `_backups` keep the before-state. Josh's reference, setup and working files
are never included. This time: both Turtle Ninja batches' files, 10 items, 2.4 GB. `batches\` is empty.

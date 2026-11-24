# 126 - Stage 2: the Intercessors written, and the rest of the Mar Fil torsos in one batch (Nov 24)

**Intercessor Chests 1-5 written.** Josh said "all good" to batch `02 Stage 2 - Intercessor torsos` (notes 125), and
`read` found every piece unchanged. `write` wrote 5 sidecars (backup `batch write 2026-11-24 2047`), and every joint
read back from the library at 0.0000 mm.

**The big batch.** Josh asked for a bigger next batch with all the remaining Mar Fil torsos:
`~\Desktop\mar fil connectors\batches\02 Stage 2 - Other Mar Fil torsos (2026-11-24).blend` (about 535 MB). Spec
`kits/seat/batches/02-other-marfil-torsos.json`. It holds 22 torsos:
- Veteran Chests A-E;
- Bladeguard Chests 1-2;
- the Techmarine Chest;
- the Jump Chaplain Chest;
- the 13 Outrider Torsos (A, B, BA, BT, DA, DW, IF, IH, RG, SW, Sal, Ultra, WS).

The generator now lays the columns out in rows of 8, each row 120 mm below the last. The reference takes the first
slot. A torso with nowhere to start is left out.

**Where each piece starts.** Josh's Torso 2 cuts land on all 22 torsos (rms 0.000-0.057 mm). Compared with the old
sockets:
- **Neck:** 2.5 deg on the Veterans A-D, the Bladeguard and Outriders A and B; 3.0 deg on the other 11 Outriders;
  2.2 deg on the Techmarine; 0.2-0.5 deg on Veteran E and the Jump Chaplain.
- **Back:** 0.4 mm / 1.3-1.7 deg on all but the Jump Chaplain. The back cut lands at rms 0.03 mm, so the backs are
  slightly different sculpts from Torso 2's.
- **Shoulder:** 2.0-2.2 deg on the Techmarine and the Jump Chaplain, 0.6 deg on 11 Outriders, and up to 0.2 deg on
  the rest. The mirrored left sockets differ from the old left sockets by the same amounts, so the old sockets were
  mirror-symmetric too.
- **Waist:** 0.0-0.2 deg.

**Left out: the Bike Chaplain** (Chaplain Chest, Bike Body 1 and 2). They have no sockets and none of the cuts land
(rms > 9 mm): they sit elsewhere in their own files, and a seated rider is a different pose. They need Josh's anchor or
their own cut. Their three slots are the gap in row 2.

**Checks.**
- Every mesh matches its recorded frame (worst 0.0020 mm over 184 pieces).
- `write --check` lists the 110 socket writes and nothing else.
- Renders beside the batch: `02o check - row 1/2/3.png` and `02o check - Techmarine and Jump Chaplain.png`.

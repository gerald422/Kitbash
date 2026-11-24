# 132 - Stage 2: Turtle Ninja batch 3, legs and helmet pre-set (Nov 24)

Josh: "build batch 3 with both changes pre-set".

**Batch:** `~\Desktop\mar fil connectors\batches\02 Stage 2 - Turtle Ninja torsos 3 (2026-11-24).blend`, 16 torsos:
the Mk7-8 Uppers A1, B1, C1, D1, E9, F1, G9, H1, I9, J9, K9, M1, N9, O9, P1 and Q9. These are the last of the 55
straight Turtle Ninja torsos.

Two of Josh's repeated fixes are pre-set (`make_torso_batch --preset`), shown pink:
- **Waist:** his legs change, 0.616 mm / 18.47 deg (notes 129-131).
- **Neck:** his helmet raise, a pure move of 0.387 mm: (0.0001, 0.1424, 0.3596) in the Neck frame. It is taken from
  batch 2's written sockets (backup `batch write 2026-11-24 2144`), where it is identical on every torso to 1e-5. The
  0.01-0.03 deg turn in those sockets is float noise, so it is dropped.

**Checks.**
- Every mesh matches its recorded frame (worst 0.0044 mm over 136 pieces).
- The 16 pre-set legs and 16 pre-set helmets are exact (0.00000).
- `write --check`: 16 Waist and 16 Neck changes, nothing else.
- Renders `02t3 check - ...png` beside the batch.

**Written** (Josh: "all done ready to write to library"). The file was untouched since the build, so every pre-set was
approved. 16 sidecars, backup `batch write 2026-11-24 2152`. All 64 joints read back from the library at
0.0000 mm / 0.000 deg.
- Every Neck: 0.387 mm, no turn.
- Every Waist: 0.616 mm / 18.47 deg.

The batch file and its check renders went to the Recycle Bin (6 items, 0.32 GB).

**The stage 2 torsos are done** except:
- the Bike Chaplain (3 parts, no sockets: needs Josh's placement or a cut);
- the new sockets: Chest Insert, Neck Guard and cloak.

The 55 straight Turtle Ninja torsos and the Redwarden torso are all written.

# 138 - The no-circles cloaks get their own socket, "Cloak Plain" (Nov 25)

On the TN torsos Josh moves the two cloak styles differently. From one Cloak socket, the no-circles cloak sat 1.28 mm /
6.2 deg from his placement (points: a median of 1.8 mm off, at most 3.2 mm; notes 137). He said: "Yes needs its own
socket".

## The design

- The circles cloaks (CyberBrush 1-5) stay on `Cloak`.
- The no-circles cloaks (the 12 Marta) also get a `Cloak Plain` fit, the same matrix as their written `Cloak` fit.
  The written fit stays (Rule 1).
- When the Cloak joint is switched on (stage 6), it is
  `"Cloaks": {"socket": ["Cloak Plain", "Cloak"], "byFit": True, "exclusive": ["Cloak Plain", "Cloak"]}`.
  That is the same choice by fits as legs (`Waist` / `Flat Waist`): a Marta cloak lands on `Cloak Plain`, a
  CyberBrush one on `Cloak`.
- Every torso gets both sockets.

## Written (`kits/seat/cloak_plain.py`)

The old sidecars are in `_backups\cloak plain 2026-11-25 0924`. Read back: 0 wrong.

| What | How many | Cloak Plain |
|---|---|---|
| Torso 2 and the Mar Fil torsos | 35 | = Cloak. Josh approved both styles on the same socket there |
| The TN torsos of batch 2 | 17 | = Cloak . D1^-1 . D2. D1 and D2 are his circles and no-circles moves on Mk7 Torso Jump Pack A9, read from `TN torsos 3 (c)`, where they were applied unchanged |
| The 12 Marta cloaks | 12 | a `Cloak Plain` fit |

## The rest of the batches

- **Writing:** the TN 1 and TN 3 specs now write both sockets: the circles cloak's move is `Cloak`, the no-circles
  cloak's move is `Cloak Plain`. `make_cloak_socket_batch.py` does the same from now on. A dry run on
  `TN torsos 1 (d)` gives 22 + 22 sockets.
- **Josh's TN 1 changes:** in `Redwarden and TN torsos 1 (c)` he moved the circles cloak on the first two torsos:
  - Redwarden: 0.51 mm / 6.65 deg;
  - TN Mk2 Upper A1: 0.67 mm / 6.7 deg.

  Redwarden stays separate. The Mk2 Upper A1 change went on the other 20 TN torsos' circles cloaks (exactly), in
  `Redwarden and TN torsos 1 (2026-11-25 d)`. The no-circles cloaks keep his TN 2 change.

## Written: Redwarden and TN torsos 1 (d)

Josh: "all good". All 22 torsos got both sockets: the circles cloak's move is `Cloak`, the no-circles cloak's move is
`Cloak Plain`.
- The old sidecars are in `_backups\batch write 2026-11-25 0945`.
- All 44 joints matched the file: 0.0000 mm.
- The c and d files went to the Recycle Bin.

Left with Josh: `TN torsos 3 (c)`, the last cloak batch.

# 124 - Stage 2: the Assault torsos written (Nov 24)

Josh checked batch 02 (`~\Desktop\mar fil connectors\batches\02 Stage 2 - Assault torsos (2026-11-24).blend`,
notes 123) and said "all good". The file is unchanged, so every start was approved as it is (PLAN Rule 3).

`batch.py read`: all 24 movable pieces unchanged. `batch.py write`: 10 sidecars, backup
`D:\Kitbash Library\_backups\batch write 2026-11-24 2041\before\lib`. Repo `library/` mirrored.

What is in the library now, all marked as Josh's (`kb_josh`, kept by every merge):
- **Torso 2:** `Neck`, `Back` and `Waist` as they were (0.00 from the old ones), now protected. (Its shoulders were
  written in stage 1.)
- **Torsos 1, 3, 4, 5, 6:** `Shoulder R` / `L`, `Back` and `Waist` within 0.01 mm and 0.07 deg of the old ones.
  **`Neck` moved 0.11 mm / 2.46 deg** to match Josh's Torso 2 neck cut.
- **Torso 2 Insert:** its own sockets kept (0.00). `Shoulder L` is now the exact mirror of `Shoulder R` (it moved 0.07 deg).
- **Fits, in `exact`:**
  - Helmet 1 `Neck`: 1.24 deg from the old fit.
  - Back Pack 1 `Back`: 0.08 deg.
  - **Legs 1A `Waist`: 9.47 deg / 0.67 mm**, replacing the old 80% "look" fit.

The read-back check places every written joint from disk (socket . fit) against the batch file: 0.0000 mm / 0.000 deg
on all 27.

Knock-on until their own batches: these three fits now also place on every other torso's old Neck / Back / Waist
sockets. So Legs 1A on an Intercessor or Veteran torso turns 9.5 deg from before, until that torso's stage 2 batch
writes its Waist.

Next: the other stage 2 torso batches (Intercessor, Veteran, Bladeguard, Outrider, Chaplains, Techmarine; Redwarden;
Turtle Ninja straight), and the new sockets (Chest Insert, Neck Guard, cloak).

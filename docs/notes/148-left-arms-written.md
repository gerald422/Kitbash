# 148 - Stage 3: all Mar Fil left-only arms written (Nov 25)

## Batch 1: the 24 Assault left arms

Josh: "all good to go". The file was unchanged.

**Written:**
- Each arm's own Shoulder L fit, as the left image of its placement (notes 147).
- 25 sidecars, with Torso 2 unchanged.
- Backup: `_backups\batch write 2026-11-25 1321`.

## Batch 2: the other 84 left arms, as one batch (Josh)

Josh: "im happy to have that last lot as one big batch". The file was
`03 Stage 3 - Mar Fil other left arms (2026-11-25).blend`, 1.6 GB, 84 columns. It held the Intercessor, Outrider,
Bladeguard, Veteran, Techmarine, Captain with Jump Pack and Chaplain left arms. A `--check` dry run on it gave each
arm's old left fit back (82 at 0.008-0.009 mm, two at 0.011 and 0.030 mm, all 0.06 deg).

**The grenade bolter arms:**
- The renders showed Bolter C Grenade 3 L hanging down the leg, like its right version before Josh turned it
  (notes 144).
- The A, B and C Grenade 3 L sculpts are near-mirrors of their right ones (triangle counts within 0.1%).
- Placed with the right arm's approved fit, each mirrored left sculpt lands within 0.5-1.7 mm of the right arm (C
  Grenade 3: 6.7 mm, a slightly different pose). So I started those 4 at their right arm's fixed seat and rebuilt
  the file.

**But Josh already had the first build open.** He had made his fixes there, and he saved over my rebuild (his file:
built 13:24, saved 13:32; my rebuild became the .blend1). His save won, so nothing was lost. The spec on disk still
carries the 4 changed starts, but the write only takes the spec's write targets and reads each final placement from
his file.

**Lesson (saved to memory):** never rebuild or delete a batch file once it is handed over. Build a new "b" file
instead.

**His fixes:**

| Arm | Move | Turn |
|---|---|---|
| Bolter A Grenade 3 L | 25.8 mm | 151.9 deg |
| Bolter B Grenade 3 L | 25.3 mm | 146.3 deg |
| Bolter C Grenade 3 L | 26.7 mm | 179.6 deg |

He left Bolter C Grenade 1 L at its old seat. The other 80 were unchanged.

**Written:**
- The Shoulder L fit of all 84 arms.
- 85 sidecars, with Torso 2 unchanged.
- Every joint read back at 0.0000 mm.
- Backup: `_backups\batch write 2026-11-25 1333`.
- The file and its .blend1 went to the Recycle Bin.

## A slip in my read-back filter, and the recheck

For the Intercessor, Veteran / Blade Squad, Chaplain / Captain / Outrider and Assault left batches, I filtered the
write's check lines with awk field `$4`. That field is the "R" / "L" of "Shoulder R", so a mismatch would never
have shown.

I copied those four files back from the Recycle Bin and placed every written joint from the library again
(socket . fit), against each file. All 97 joints were at 0.0000 mm / 0.000 deg, so the earlier reports were right.
The filter now reads the distance ($5) and the angle ($7).

## Where stage 3 stands

Every Mar Fil arm on the spacer is approved: 119 right arms and 108 left-only arms (24 + 84), with mirror fits on
the arms that have mirror variants. Still to come in later stages: the two-armed weapons, other makers' arms, and the
Techmarine double arms. Other makers (Marta, TN, CyberBrush ...) have not started stage 3.

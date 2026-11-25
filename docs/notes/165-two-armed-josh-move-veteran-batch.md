# 165 - Two-armed weapons: Josh's move carried; batch 2, 40 Veteran (Nov 25)

Josh: "ive made one change can that be applied to all of the arms in this particular set please. Can we go for the
next batch being a bit bigger if possible".

**His change:** Assault Eviscerator 1A moved 0.23 mm along -X in its seat frame (back in, against the 0.32 mm
pre-set), no turn. `batch.py apply ... a1_arm ... --delta` put it on the other 23:
`03 Stage 3 - Two-armed Mar Fil Assault melee (2026-11-25 b).blend`; read back, all 24 carry exactly that move.

**Batch 2, bigger (40):** the whole Mar Fil Veteran Squad set, 36 two-handed guns and 4 heavy weapons:
`03 Stage 3 - Two-armed Mar Fil Veteran guns and heavy (2026-11-25).blend`, `--two`, with his move pre-set
(`--shift 0.09,0,0` = 0.32 - 0.23; the seat frame's axes are Torso 2's). Render of 5: both arms at the shoulders.

Left after this: Mar Fil 105 (Intercessor dual bolters 61, Blade Squad melee 27, Intercessor heavy 15, Techmarine 2),
Marta 36, Turtle Ninja 28, CyberBrush 8.

**Written** (Josh: "both are good to go, write them"; backup `batch write 2026-11-25 2228`): the 24 Assault melee
from the b file and the 40 Veteran guns and heavy as built. All 64 read back at 0.0000 mm. The batch files went to the
Recycle Bin. Two-armed left: 177.

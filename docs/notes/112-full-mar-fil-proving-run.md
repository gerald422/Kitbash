# 112: The full Mar Fil proving run (Nov 18)

Run 16 (`~\Desktop\mar fil connectors\proving 16 full`): every eligible Mar Fil part of every joint type, 580 parts,
56 min on 10 workers. Techmarine arms are now left out too (`NOT_ARMS`, Josh). Hidden parts (`_hidden.txt`: the
aquila torsos) are not searched, so only 6 torsos. Two-handed weapons have no joint yet and are not in the run.

New `kits/connectors/sheets.py`: per type, a sheet of reference marines (Assault Torso 2, Arm 2A, Legs 1A, Chain
Sword 1, Shoulder Pad 1, Shin Pad 1, Bladeguard Helmet 3A, Intercessor Back Pack 1) with only the tested part swapped
in, its name and result under it; "working" and "flagged" sheets, front and side (the marine turned to show its
right); `sheets.txt` lists every part not working and why.

| Type | Parts | Sure | Placed, flagged | Not placed |
|---|---|---|---|---|
| Torsos | 6 | 5 | 1 (Veteran Chest E back near) | 0 |
| Arms | 96 | 23 with every joint sure | 73 (mostly weapon arms with no wrist) | 0 |
| Legs | 46 | 1 | 44 (waist near) | 1 (Intercessor Legs 10) |
| Heads | 74 | 21 (Veteran, Bladeguard) | 51 (neck near, 0.016-0.021 mm) | 2 (Veteran Helmet A, B) |
| Jump packs | 6 | 6 | 0 | 0 |
| Backpacks | 32 | 13 | 14 (Veteran, Bladeguard: near) | 5 (Mk10 Hellblaster packs) |
| Shoulder pads | 39 | 28 | 4 | 7 (Bladeguard 1-5, Bike Chaplain 2) |
| Shin pads | 61 | 52 | 4 | 5 (4 Bike Chaplain bits filed as shin pads; Veteran Shin Pad M) |
| Melee | 135 | 90 | 45 (Bladeguard 28) | 0 |
| Pistols | 61 | 12 | 49 (Intercessor bolters 35) | 0 |
| Hands | 10 | 9 | 0 | 1 (Bike Chaplain) |
| Shields | 14 | 2 | 12 | 0 |

What the sheets show:

- Near written parts that look right: heads, Veteran / Bladeguard backpacks, the near shoulder pads, legs.
- Near written parts that look wrong: Intercessor bolters (pointing every way: the weapon wrist cuts don't fit their
  hands), Bladeguard shields (held at every angle), some Bladeguard melee rolls.
- Arms with no wrist found: power fists, bolter / plasma / pyreblaster arms, Outrider handle arms (no wrist to find),
  and the plain Intercessor Arm 1, 4, 5 (the Assault wrist cut doesn't fit them; Arm 6 near).

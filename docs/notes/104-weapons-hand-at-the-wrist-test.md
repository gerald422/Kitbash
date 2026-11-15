**Weapons with a hand mate at the wrist (Nov 15): no grip cut, the weapon's side taken from one weapon placed by its
library fit on Josh's wrist A arm. Tried on Mar Fil: exact on the same hand sculpt only, so one example per hand
design. Nothing written. Weapons without a hand are not used (Josh).**

- **Josh, Nov 15:** "Isn't grip just the wrist as it had the hand attached?" Then: "For those without a wrist I
  wouldn't use them ... the same as not using Marta's torsos. Go ahead with test." The repo had no explicit note
  of that rule (only hand-less duplicates skipped on import: notes 049, 058); it is now in `docs/OPEN.md` item 3
  and the cut list: `Hand-less Weapons` and files named "No Hand" / handless are left out.
- **`seat.py` "placed" connectors** (new kind in `read_connectors`): `{"placed": weapon, "on": arm, "socket":
  "Hand", "fit": "Hand", "blend" + "spot": the arm-side cut}`: the weapon is put on the arm's socket by its own
  library fit (both read in the maker's frame) and the weapon's triangles within 0.3 mm of the cut are its side,
  as a pad's inside is cut from a placed pad (notes 099), but from the library instead of a blend.
- **Test** (config in the session's scratch, not in the repo; dry run, deleted after): Assault Chain Sword 1 R on
  Assault Arm 1A R's wrist A (5,032 triangles), searched over Mar Fil Melee, Pistols, Hands, Shields (344; no
  Two-Handed Held in Mar Fil):
  - **sure 39** (Assault 23, Intercessor 16; Shields 1): match 0.0013-0.0047 mm, the same hand sculpt. Their new
    fit is 0.42-0.54 mm (median) / 3-5 deg from the library fit, at most 0.8 mm. Library hand fits came from
    TIOW's hand rule (a reference fist, approximate), so the connector is likely the better one; not written
    until Josh has looked.
  - **look 187**: other hand sculpts (Intercessor 88, Bladeguard 46, Assault 31, Veteran 12, Techmarine,
    Outrider, Chaplain, Captain) at 0.005-0.03 mm, many turned 70-175 deg: wrong. **none 118** (Bladeguard 69,
    Veteran 26, Intercessor 15, Outrider 7, Bike Chaplain 1).
- **So:** one weapon per hand design gives that design's side, taken from its library fit (no work for Josh as
  long as one weapon of the design is fitted right); the arm side needs a wrist cut per arm design (wrist A is
  Assault's). The cut list (`kits/connectors/cuts_needed.py`) now shows weapons with a hand as "hand at wrist", no
  cut: 11 groups, 1,450 weapons; the totals are 62 cuts and 16 pads to place over 15 maker folders.
- **Next for this:** pick one example per hand design (the kits above), check the 39 sure ones against their
  library fits on the page, then write and move them like the other types.

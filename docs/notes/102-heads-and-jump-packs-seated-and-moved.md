**Mar Fil heads and jump packs (Nov 15): seated by Josh's Nov 14 neck and jump-pack connectors (sure fits only),
then their origins moved onto the joint. 59 fits written, 88 files moved, all 326 test parts where they were.**

- **Josh, Nov 15:** "yes" to heads and jump packs next, with the connectors he already cut (notes 096).
- **Config** (`kits/connectors/marfil.json`): `Heads` = `neck` (`marfil nck.blend`, object `1-Helmet-1.001`, cut on
  Assault Helmet 1, fit `Neck`); `Jump Packs` = `jump pack mount` (`mar back pack.blend`, `55-JumpPack-1.001`, Assault
  Jump Pack 1, fit `Back`). Both sit on their reference (0.0003 / 0.0000 mm).
- **Search** (`connectors-2026-11-15-9`, 91 parts, 1 min): a clean split.
  - sure 59: Assault 23, Helmets Update 21, Intercessor 11, Techmarine 1, Bike Chaplain 1 (its first fit), Jump
    Chaplain 2; match 0.0007-0.0031 mm; moved from the old fit 0.03 mm / 0.3 deg at most, except the Jump Chaplain
    jump pack, 1.6 mm / 5.7 deg (an exact copy of the mount, match 0.0010: the old fit was the odd one out).
  - look 27, every one a Veteran or Bladeguard head, match 0.0175-0.0199 mm, turned up to 98 deg from their fits:
    another neck design (as on Nov 14). **Not written**: `seat.py --sure` (new, on `run` and `write`) writes the sure
    fits only. They keep their library fits until Josh cuts that neck.
  - none 5: Captain with Jump Pack Beakie Helmet, Helmet and Jump Pack; Veteran Helmet A / B (the `Accesories`
    copies).
- **Move** (`origins-2026-11-15-2`): 82 heads, 6 jump packs, by their (old or new) Neck / Back fit; origin 33.4 /
  33.8 mm median. Every head's file now lies in the torso's neck frame (turned 180 deg about Z and tilted ~22 deg, as
  that socket is), the packs in the back frame. Veteran / Bladeguard heads moved by their library fits: a recut later
  re-seats them from the maker's frame and `Move origins.bat` moves them again by the difference.
- **Checked:** 18 extra models (three heads of each Mar Fil kit, a pack each, on random Mar Fil torsos) with the 26
  of notes 101: before the move recorded, after it all 326 parts where they were. 88: index = sidecar, previews
  within 0.04 mm of the STL's box.
- **Left:** backpacks (32: Nov 14 found their mount differs from the jump pack's; a connector from Josh), the
  Veteran / Bladeguard neck, Captain with Jump Pack heads and pack.

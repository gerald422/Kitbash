**Josh's own Mar Fil connectors matched by shape (Nov 14): they find the same connector exactly and give the
library's fit back; they do not carry across connector designs, and the round ones don't fix the turn.**

- **His files** (`~\Desktop\mar fil connectors\`, Blender): one open surface each, cut in place from his reference
  parts: `arm connector` (Assault Arm 1A R's shoulder disc, 0.5 x 4.6 x 4.6 mm), `marfil nck` (Helmet 1's neck,
  4.4 x 4.4 x 1.4), `mar back pack` (Assault Jump Pack 1's mount, 2.9 x 1.0 x 3.7), `marfil wrist` (Chain Sword 1 R's
  grip, 2.6 x 0.25 x 3.5). The other objects in the files are hidden BoxCutter / Bolt helpers. Open is right: a
  closed (manifold) connector would add cut faces no part has.
- **Test** (`kits/nofit/connector_try.py`, 25 Mar Fil parts a connector, a part's own fit never used to find it):
  the connector searched over the part (24 square turns x 150 places, ICP), or with `--frame` only slid over the
  part as it lies in its file; the fit = the reference's moved by the match, compared with the part's library fit.
  - **neck**: the Assault and Helmets-Update heads match at 0.025-0.033 mm and give their fit back to 0.03 mm /
    0.9 deg (11 of 11); Veteran, Bladeguard, Jump Chaplain heads match at 0.08-0.16 mm: another neck, all wrong.
  - **jump pack**: the other Assault jump packs 0.079 (as on its own part, 0.073) and right (2 of 2); backpacks
    0.09-0.14, all wrong: another connector.
  - **arm**: with the turning search, discs that match (<= 0.05 mm) land in place but turned 90 or 180 deg on half;
    keeping the turn the part has in its file, every arm matching at <= 0.045 mm is right (7 of 7: Assault,
    Intercessor, Bladeguard, Veteran; 0.02-0.6 mm, <= 2.5 deg); Outrider, Jump Chaplain, Techmarine arms and the
    Intercessor bolter arms match worse and are wrong.
  - **wrist**: hands and hammers (0.025-0.057) land within 0.35 mm, 2.5-5 deg; Techmarine Hand turned 175; guns,
    bolters, swords, spears do not share the chainsword's grip.
  - **turn**: the neck, the disc and the grip are round: turned 30 deg about themselves they still match within
    0.01 mm. They fix where the part sits and its tilt, not its turn about the joint: that comes from the file's own
    frame (Mar Fil exports in its kit frame, so it holds there), from a keyed shape on the connector, or the page's
    "Other way round". The jump pack's mount does fix its turn (0.079 -> 0.149 mm turned 30).
- **So**: one connector per connector DESIGN, not per type (Mar Fil needs several necks, a backpack mount besides the
  jump pack's, grips per weapon family, arm discs per kit); the match distance says which connector a part has
  (<= ~0.045 mm here); round connectors need the turn from elsewhere. Nothing written to the library.

**Josh's next Mar Fil connectors (Nov 14): the arm's pad spot (A and B types), two wrists and the legs' waist. All four
sit exactly on their reference parts and are found where the library already puts the joint on the parts that share
the design; the search from scratch is too weak to use yet. Josh: the approach (connectors per maker) goes ahead.**

- **His files** (`~\Desktop\mar fil connectors\`): `arms a.blend` (pad spot `76-Arm-1-R-A.001`, 5.3 x 6.4 x 2.7 mm, and
  wrist A `76-Arm-1-R-A.002`, both from Assault Arm 1A R), `arm b.blend` (the same pad spot, identical, and wrist B
  `77-Arm-1-R-B.001`, 4.2 x 4.7 x 4.2, from Arm 1B R; it has a 0.3 mm loose fleck, harmless), `legs.blend` (waist
  `34-Legs-1-B.001`, 6.4 x 8.3 x 0.7, from Legs 1B). All open surfaces, as before. The other objects are hidden
  BoxCutter / Bolt helpers. **The legs object carries an 11.7 deg turn**: its mesh data sits on Legs 1B exactly, its
  world placement 3.7 mm off; `kits/nofit/connector_export.py` writes the mesh data (file coordinates), so nothing
  needs changing in his file. The pad spot sits on Arm 1B to 0.0007 mm: one pad spot serves the A and B arms.
- **At the joint** (`kits/nofit/connector_at_joint.py`: the connector starts where the part's own fit / socket puts
  the joint and settles by shape; on its own part a connector sits at ~0.03-0.04 mm sampled, the legs at 0.08):
  - **wrist B** (Forearm socket): 32 of 32 Assault B arms, 0.01 mm / 0.3 deg.
  - **wrist A** (Hand socket): 131 of 153 arms within 0.065 (all Assault and Veteran, most Bladeguard, Outrider,
    Intercessor, Techmarine), 0.13 mm / 1.6 deg; 13 are another wrist.
  - **legs waist** (Waist fit): all 88 Mar Fil legs 0.073-0.11 (Assault and Outrider lowest, Bladeguard highest),
    0.08 mm / 2.5 deg. **Assault Legs 3** moves 0.47 mm / 9.4 deg: its library fit looks off.
  - **pad spot** (Pad socket): Assault 62 of 62, Outrider 35 of 36, Jump Chaplain 7 of 8, Veteran 12 of 17 within
    0.08 (0.07 mm / 3.5 deg; the 14 Assault Power Fists 0.051-0.063). Intercessor, Bladeguard and Techmarine arms
    have another shoulder: they need their own pad spot.
- **Pads on the pad spot** (`kits/nofit/pad_pullback.py`, 25 Mar Fil pads at their library fit on Arm 1A): the pads
  rest on it (0.05 mm median for most), and pulled from their fit they stay (0.2 mm). Knocked 15 deg / 1.5 mm off,
  they come back within 0.5 mm less than half the time: the dome sets a pad's seat and depth, not its place on the
  dome. The pad's place and turn still come from its inside / the pad master (notes 094).
- **Search from scratch** (`kits/nofit/connector_try.py`, now with `--sockets`, `--padfit`, `--need`, `--top`, `--pts`):
  too weak for production. Wrist B found on 7 of 25 arms that all have it (the rest land 100+ deg off at 0.15-0.2
  mm, a false minimum), the pad spot on 0 of 25 arms (a smooth dome matches anywhere), the legs waist on a few. The
  shapes are there (above): the search, not the connectors, is what has to improve before the seating script.
- **So**: the connectors are right; one per connector design (Mar Fil: one legs waist covers every kit, wrist A most
  arms, the pad spot the Assault / Outrider / Chaplain / most Veteran shoulder). Nothing written to the library.

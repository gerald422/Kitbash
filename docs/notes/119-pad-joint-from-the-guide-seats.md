# 119 - The pad joint from Josh's guide seats; the reader takes the auto cuts (Nov 23)

**Where the pads come from now.** The pauldron adapter of notes 118 became a guide: one shared inside shell (origin on
its crown, +Z out, +Y front) with each Tacticus pad parented in it (the pad's fit). Josh seated a guide with its pad
on 21 arms by hand (Mar Fil 9, Turtle Ninja 3, Springles 3, Marta 6:
`~\Desktop\mar fil connectors\Pauldron adapter - seat and cut (2026-11-23).blend`). Each arm's pad spot cut was taken
from his seat automatically: the arm faces the pad sees from inside (first ray hits from the dome centre, 4.04 mm under
the crown, within 75 deg of the guide's axis, plus one ring), parented to the arm, with the guide's pose on the arm
kept on the cut (`kb_adapter_in_arm`). The same cuts went into the Turtle Ninja setup files (clean, TO CUT, TO CUT lean)
for the arms that are there unchanged (Mk10 2.0, Mk6, Mk7), in an `AUTO CUTS (...)` collection.

**Reader** (`kits/connectors/reference.py`):
- Collections starting `CUTS (auto` / `AUTO CUTS` are read as cuts. A cut with `kb_joint` "Pad (pauldron adapter)"
  and `kb_adapter_in_arm` is an `arm pad spot`, its kind = the arm it was cut on; other auto cuts are left out with a
  note (the Marta legs waist auto cut goes through waist adapter 3: not wired yet).
- Files after the first may be the seat file: its `ARMS + ADAPTERS` collection and its `Torso 2 - <arm>` copies are
  read with the auto cuts. Guides (`Adapter - <arm>`, mesh "Pauldron adapter") are not parts; a pad's name drops
  `(in adapter, <arm>)`.
- When guide seats are read, the pad joint is built from them and only them: host J = the guide's pose in the arm's
  file coordinates, child J = the guide's pose in the pad's; the pad's inside cut = its faces looking at the dome centre.
  The hand `arm pad spot` cuts and placed pads are not used. With the main reference alone nothing changes; with the
  seat file added every other joint reads identically (checked: shoulder, neck, waist, back, wrist, shin).
- Maker file names typed with spaces for underscores, with "TN " in front (`TN Mk10 2.0 Arm Right A 1` =
  `Mk10_2.0_Arm_Right_A_1` = `TN Mk10 Assault - Arm A1 R`), are found.
- Read: 19 guide seats, 11 pads. Left out (noted): the Marta Gurls Arm 4 Cloth (a left arm, `arm-4-cloth.stl`, mirrored
  in the seat file to sit right: its mesh is no library file), Bladeguard arms (excluded since Nov 17), TN
  `Pauldron A 1` (Mk6 / Mk7 pad: not in the library).

**Proving** (`kits/connectors/prove.py`): a guide seat's cut covers the whole dome, so its region round the shoulder
widens by the cut's reach; and the reference arm's shoulder is found on it as on the parts proved (its shoulder disc
cut, sure), because the seat file's torso copies don't sit on their arms (11.8 mm off on Arm 2B R; the nearest copy
was ~30 mm away for the others). Run (Assault kit, `--types Arms --per 2`, main reference + seat file): shoulder 10
sure, wrist 7 sure 3 near (as before), pad spot 8 sure, 1 near (Arm 10A R), 1 none (Intercessor Arm 1 R, 71%). Pads:
Assault, Jump Chaplain, Veteran, Bladeguard Death pad sure; Outrider pads near.

**Not written yet.** The new pad frame is the guide, not the old `Pad R` socket (the new sockets are 2.6-3.1 mm /
36-51 deg from the library's), so arms' `Pad R` sockets and pads' fits must be written together, from one run.

**Mar Fil weapon hand designs found with no cuts (Nov 15): `kits/connectors/hands.py`, 20 rounds, 324 of 345
weapons with a hand in 16 groups. Dry runs only; nothing written to the library.**

- **How:** `hands.py CONFIG` (config `kits/connectors/marfil_hands.json`). Each round puts one example weapon on
  Assault Arm 1A R's wrist A cut by its library fit (a `seat.py` "placed" connector, notes 104) and dry-runs
  `seat.py run --list` over the weapons not yet covered. The sure matches form the example's group. The next example
  is a right-hand-fitted weapon from the kit with the most still uncovered. `seat.py --list FILE` limits a run to the
  listed parts. Output goes to `_backups/hands-2026-11-15/` (`report.txt`, `summary.json`, `roundNN.json/.txt`);
  each round's plan is in its `_backups/connectors-2026-11-15-NN`.
- **Result** (345 weapons, hand-less left out): the groups by size are 69 Intercessor bolter grip, 53 Intercessor
  open hand (also Assault), 39 chainsword, 38 / 28 / 26 / 16 Bladeguard axe hands (1B, 1A, 1B Bionic, 1A Bionic),
  20 Veteran gun, then 5, 5, 3, 2, 1, 1, 1, 1. Four examples matched nothing else (Shield 2B, Combat Knife 3,
  Hand 3, Power Sword C3).
  - Medians from the library fits are 0.02-0.54 mm and 0.1-6 deg.
  - 20 sure matches turned far, all about the socket Y axis:
    - 15 flipped about 155-178 deg (round 4: 7 Bionic / L swords; round 5: 8 Bladeguard swords, hammers and shields).
      The flip swaps the weapon end-for-end along the hand socket's Z; the hand band still matches at about 0.001 mm.
      Which one is right (the library fit or the new one) needs Josh's eye.
    - 5 more turned 11-14 deg (round 6 three, Volk B L) or 154 deg (Volk A L).
- **Left:** 17, stopped by the 20-round limit and not exhausted. 3 have a Hand R fit (Captain shield, Bladeguard
  Plasma B, Veteran Pistol); 12 only have Hand L (Bionic swords / hammer / spear, Volk, Techmarine, Jump Chaplain);
  2 have no fit (Shields 1C, 3C, the Bike Chaplain handle). Hand-L-only examples need a left-arm wrist cut (or the
  mirror) before they can be used.
- **Written Nov 15** (Josh: the 39 "happy"; the flipped ones "I'll sort those out in the app"): each group's task
  with `seat.py write TASK --sure --near 2`, so 288 fits were written. The 20 far ones keep their library fits; each
  task's `left_far.txt` lists them. Backups are in each `_backups/connectors-2026-11-15-NN/before`.
- **Left-hand-only weapons:** Josh: "they should be mirrored". `seat.py` already searches a left part mirrored, so
  `hands.py --resume DIR` carries on the run past the round limit.
  - Resumed for rounds 21-29:
    - Veteran Pistol +1 at 0.04 mm (written).
    - Bladeguard Sword 5A Bionic +2, both 2.1 mm / 11 deg off (not written: over `--near 2`).
    - Six examples matched nothing else.
    - Round 29 stopped: the Techmarine Hand's library fit doesn't put its wrist on the Assault wrist cut (0
      triangles), so it gives no side.
  - Final: 329 of 345 in groups, 10 alone. 5 not covered: Absolvor and Techmarine Grav Pistol (Hand L only, each
    other's only candidate), Bike Chaplain handle and Bladeguard Shields 1C / 3C (no fit). They keep what they have,
    and mirroring (notes 106) covers the other side.
- **Moved Nov 15** (Josh: "Yes"; `origins.py run kits/connectors/marfil_held_origins.json`, task
  `origins-2026-11-15-4`): 342 files (Melee 190, Pistols 125, Hands 11, Shields 16; origin moved 3-9 mm median). The 3
  with no Hand fit were left. Originals are in its `before`; `Move origins.bat restore` undoes it.
  - Check: 30 models, each with Arm 1A R on both shoulders and 60 of the moved weapons in both hands, many mirrored
    onto the other side. Built from the originals (a copy on C:) and from the library: all 150 parts are where they
    were.
  - The golden run's `maker_frame` used to read a mirror made on the spot (`tiow_variant` -1, notes 106) as the last
    variant. It now takes the file's own `origin.from_file`, mirrored.

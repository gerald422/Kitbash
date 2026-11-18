**Search tie-break; new Intercessor / Veteran / shield / Bladeguard pad cuts; run 19 (Nov 18).**

- Every cut in the reference renamed with its armour type in front (Josh asked; backups `Kitbash reference (before
  renames ...).blend`). New: `intercessor arm wrist a` (Intercessor Arm 1 R), `Assault weapon wrist shield`
  (Assault Shield R), `Veteran weapon wrist` (Veteran Combi Weapon 4A), a placed Bladeguard Shoulder Pad 1 (no cut:
  its inside is what rests on the pad spot). Hellblaster packs not worried about for now; Techmarine arms out.
- The Veteran cut did not find its own weapon (none, 75 % cover) though every corner lies on the file. Cause: the
  coarse search (48 points of the cut, every place and turn) gave 76 places on the Combi Weapon a full 48 / 48 (200
  on Chain Sword 3); only the first 12 / 36 are settled, and ties fell in file order, so its own place was never
  settled. `kb.connect`: places at (or 1 under) the best coarse score are scored again with 192 points
  (`_break_ties`, at most 600 places). Shape only, as before.
- The tie-break alone lost 4 sure fits (Outrider arms' shoulder disc, Bladeguard Sword 4B Bionic): it put a place
  0.5 mm off first and the true one was then skipped as within 0.8 mm. Both orders are now settled, each spaced on its
  own. And `choose` let a near pose (0.0019 mm, 88 %) tie with a sure one (0.0003, 100 %) and win on place: only poses
  at the best level tie now.
- Run 19 (580 parts, all of Mar Fil) against run 16: nothing worse; up: arms shoulder 87 -> 95 sure, wrist 29 -> 39
  (all 10 Intercessor arms on their own wrist cut), melee 90 -> 107, pistols 12 -> 18, shields 2 -> 4, shoulder pads
  28 -> 33 (the 5 Bladeguard pads), knee pads 52 -> 56. Heads (21 of 74) and legs waist (2 of 46) unchanged: Josh is
  cutting Assault and Intercessor head necks. 94 min with 10 workers (the PC has 32 threads: use ~24).
- `prove.py`: a run without torsos skips the test marines; `sheets.py --base OTHER/results.json` fills the reference
  marine's other types from another run.

**Josh's recut Mar Fil connectors (Nov 14-15) and the pad insides: arms, pauldrons and shin pads seat right by
shape, with the turn; the legs are placed right but their heading is loose (Josh: fine, he turns those by hand). No
more cuts are needed for the turn: nothing round the disc or waist is shared between parts. Search fixes in
`kb/connect.py` (tie window, round test, exact file turn).**

- **His files** (`~\Desktop\mar fil connectors\`, all open surfaces separated from the part, mesh data in file
  coordinates; `kits/nofit/connector_export.py` or the same read): `arms a.blend` on Assault Arm 1B R: `.001` wrist
  B, `.002` pad spot (4.7 x 4.6 x 3.8, smaller than 097's), `.003` shoulder disc (the 096 disc plus ~16% more area),
  and Shoulder Pad 1 placed on it (closed, by its object matrix); `wrist a.blend` on Arm 1A R: `.001` wrist A (now
  keyed: 0.025 mm off turned 30 deg, was 0.003); `legs.blend` on **Assault Legs 2** (`Legs\`, not 1B): `.001` waist,
  `.002` right shin spot, and Shin Pad 1 placed on it. Every cut finds itself on its part (0.0003-0.002 mm, sure).
  His two placed pads are Shoulder Pad 1 / Shin Pad 1 and sit 0.25 / 0.21 mm from the library's placement.
- **Pad insides cut from his placed pads, not by hand**: the pads rest on his spot shells (median 0.07 / 0.08 mm),
  so the inside = the pad's triangles within 0.3 mm of the spot shell, kept in the pad's own file coordinates
  (31.7 mm2 and 40.5 mm2). Scratch script; the seating script (OPEN 5 b) does the same from his blend.
- **Search fixes** (`kb/connect.py`):
  - **Tie window relative** (`tie_window`): a quarter of the best fit's gap, 0.002-0.01 mm (was a flat 0.01). With
    0.01 a 180 deg flip at 0.009 tied with the true place at 0.000 and the file frame picked the flip (left shin
    pads, Outrider pads). Pads 37 -> 59 of 60, shin pads 62 -> 73 of 75 right.
  - **Round test** `ROUND = 0.02` mm turned 30 deg (was 0.01): the new disc is 0.012 there, counted as keyed, so its
    turn was the shape's, which does not hold it (6 deg median off).
  - **The file frame's turn taken exactly, not settled again** (a settle lets a nearly round connector drift back
    a few degrees), for round connectors and for look (variant) matches within 30 deg; the level stays the shape's.
    Sure (copy) matches of keyed connectors keep their own turn; never a flip.
- **Check** (`connector_search_check.py`, now also `turn_lib` = turn against the library's joint unsettled, the
  measure for round connectors; `turn` = against the connector settled there, for keyed ones). All Mar Fil:

  | connector | sure right / sure not | look right / wrong | none (missed) | turn |
  |---|---|---|---|---|
  | shoulder disc (220 arms) | 184 / 0 | 23 / 7 | 6 (5) | 0.4 deg median vs library; Outrider, Jump Chaplain kits ~9 deg |
  | pad spot | 53 / 5 (the 5 suspect sockets, 098) | 38 / 7 | 117 (16) | 0.0 |
  | wrist A | 17 / 0 | 29 / 19 | 155 (14) | 11 deg median: weak (hands) |
  | wrist B | 32 / 11 (no Forearm socket, 098) | 0 / 0 | 177 | 0.0 |
  | pad inside (79 shoulder pads) | 34 / 0 | 25 / 1 (Captain Pad 2) | 19 (other designs) | 0.0 |
  | shin pad inside (79) | 73 / 0 | 0 / 1 (Veteran L #42) | 5 (1, Veteran M) | 0.0 |
  | shin spot (88 legs) | 65 / 23 (the left shin: an exact copy; R / L by side in the script) | 0 | 0 | 0.0 |
  | legs waist (88) | 3 / 0 | 81 / 2 | 2 (1) | heading: 41 within 2 deg, 35 at 5-30, **8 back to front** |

- **Nothing around the disc or waist is shared** (scratch `common.py`: Arm 1B's / Legs 2's surface within 6 / 8 mm
  carried onto every part at its library joint): only the joint face itself is on >= 90% of parts, in every kit.
  The arm swing and legs heading are the sculpt's pose, not in the joint's shape: no cut can key them. Maps:
  `Desktop\TIOW Blender bridge\connector previews\Mar Fil shoulder disc - what all arms share.png`, `... waist ...`.
  So the turn of a round connector is the file's (right for kits exported in the reference's frame); a kit exported
  turned (Outrider, Jump Chaplain arms ~9 deg) needs one turn fix per kit. The waist is an oval: it holds the turn
  loosely; the library's own Waist fits differ by 10-20 deg in heading between legs (Legs 1B vs 2: 11.7 deg).
  **Josh, Nov 15: reversing / turning some legs by hand is fine** if arms and pads are right.
- **Demo** (`connector_demo.py --pad-conn --pad-ref`: pauldrons by their inside): Assault arms 0.1 mm, pauldrons 0.3 mm from the
  library, pauldrons agree; Outrider legs still turned (13.6 mm, its kit frame).
- Time: arms ~50 s each (four connectors), 8 shards on the PC's 32 threads: all 220 in ~25 min.

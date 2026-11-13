**Item 2 (fits for arms, legs, torsos): `kb/carry.py` and the `"fit": "like"` type in add-a-maker (Nov 13).**

Idea: a new arm, legs or torso gets its fits / sockets from the already-fitted parts of the same type that sit in the
library folder it is filed in, instead of one reference part per type. Precision first: what the gates keep was right
every time in the check below; what they drop is filed without a fit, with the reason and number in its sidecar.

- **How a folder's fitted parts relate decides how a joint is carried** (read from their sidecars): `same` = every
  one has one matrix (a kit frame: Mar Fil 27% of arms, TN Heresy 40%, Mar Fil / Old Style torsos) -> copied;
  `turn` = same turn, different place (all 144 Springles arms, about half of Marta's and TN Heresy's) -> the 6 mm
  shoulder region is moved onto the new part without turning; `rigid` = neither (most legs) -> the region (13 mm of
  pelvis for legs, 7 mm for a torso joint) and the whole shape are matched with turning (24 starts + the kit frame).
- **Gates** (`carry.GATES`; a recipe can change them under `"gates": {"like": {...}}`): `same` the joint must lie on
  the new part as on its siblings (within 0.5 mm of their distance); `turn` region match <= 0.12 mm; `rigid` legs /
  torsos <= 0.10 mm, arms only a near-copy (region <= 0.07, whole shape <= 0.10 mm: with no convention in the folder a
  round shoulder says nothing about the arm's turn); and for turn / rigid every reference that matches within the gate
  must place the joint within 0.5 mm / 3 deg of the best one (a pose family can carry its own turn: three TN Mk10
  "Pose 3" legs sit 11 deg from their folder-mates). References: the 4 fitted folder-mates nearest in box size, out of
  all of them. An arm with fitted mates only on the other side is tried against their mirror images.
- **What a part gets.** Arms: Shoulder R or L fit (wrist and Pad anchors are TIOW's, as before). Legs: Waist / Flat
  Waist fit; Base by the flat-legs rule (lowest 0.6 mm, the reference's up and front) when the reference's base came
  from that rule, copied in a kit frame; the belt sockets within 16 mm of the waist (Hip, Belt Front / Back, Buckle,
  Plate, Trophy) moved with the waist match; Shin left to TIOW. Torsos: Shoulder R / L, Neck, Back, Waist / Flat Waist,
  each by its own region; in a kit frame also the sockets every fitted torso agrees on (Chest Equip, Neck Guard).
- **Leave-one-out on the library** (`tests/kb/loo_carry.py LIBRARY`, read only, about 5 s a part with scipy; 14 parts
  a maker, "right" = within 0.5 mm and 3 deg of the library's own):

  | | joints | kept | right | dropped |
  |---|---|---|---|---|
  | Arms | 70 | 37 | 37 (worst 0.47 mm, 0.3 deg) | 33 |
  | Legs | 70 | 26 | 26 (worst 0.36 mm, 0.2 deg) | 44 |
  | Torso sockets | 140 | 130 | 130 (worst 0.01 mm) | 10 (no fitted torso beside them) |

  By maker, kept of tried: arms TN Heresy 13 / 14, Mar Fil 11 / 14, Springles 6 / 14, Marta Tacticus 4 / 14, CyberBrush
  3 / 14; legs TN Heresy 13 / 14, Mar Fil 5 / 14, TN Tacticus 5 / 14, Marta Tacticus 3 / 14, Marta Terminator 0 / 14.
  Legs' Base: median 0.03, worst 0.14 mm. Their belt sockets are approximate (the library's were ruled on each legs'
  own surface): position median 0.06-0.22 mm, 90% within 0.2-0.7 mm, worst 2.2 mm; turn median 1-3 deg, worst 38 deg.
  Before the agreement check and the size ranking over the whole folder, 4 of 28 kept legs were wrong (11-26 deg).
- **In add-a-maker**: a recipe type with `"fit": "like"` (`like_refs`, `fit_like`, gate / sidecar notes "carried from
  X (mode): region match, whole shape"; `fits.json` keeps the result). The test builds up to two carried parts a type
  with TIOW Inbox: an arm or `Waist` legs on the Mar Fil body, a torso under the Mar Fil parts, `Flat Waist` legs under
  the maker's first torso that has that socket; they only have to be placed and touch (`nocut` in `t_creator.py`:
  arms and legs seat into the body).
- **End to end in Blender** (scratch library and maker folder, `KB_ROOT_LIB` / `KB_ROOT_NC`; two TN Mk6 arms and two
  Mk7-8 legs taken out, their 126 fitted folder-mates left): 33 s for the four fits with Blender's KD tree; both arms
  carried (`turn`, 0.002 and 0.004 mm from the library's fit) and test-built on the Mar Fil body (placed, touching);
  legs B18 carried (`rigid`, 0.29 mm / 0.12 deg, 10 sockets, median 0.14, worst 0.49 mm); legs C3 dropped (two
  references 0.5 mm apart); built and applied, md5s match. With only 14 folder-mates present the legs were dropped:
  the match needs the whole folder.
- **Not done / limits**: torsos in a folder with no socketed torso (all of Marta's, most of Turtle Ninja - Heresy's
  703) need a reference from elsewhere, not tested; about half of arms and legs are dropped and still need placing by
  eye (Save Correction, or Adjust on the page), most of all Marta's and Springles'; no recipe uses `"like"` yet (the
  next kit drop's recipe should); a real drop into the real library; the count of unfitted library parts this would
  fit (item 3: run `kb.carry.like` over the folders' own unfitted parts).

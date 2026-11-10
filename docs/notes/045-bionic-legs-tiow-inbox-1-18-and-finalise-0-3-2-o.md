**Bionic legs: TIOW Inbox 1.18 and Finalise 0.3.2 (Oct 26).** Josh asked for an automatic plug near the leg socket for bionic legs, with the old leg booleaned out at the same time and the new leg roughly following the old one (manual was acceptable). His answers: cut at the hip; the bionic leg prints as a separate piece on the plug; Mar Fil legs first. He sent the SM Mechanical Legs kit files (he has the same files on his PC). He noted it won't work on Bladeguard (tabard) and that he may want Springles legs and other leg types later.

**The kit** (each file stands up +Z, front −Y, knee hinge along X):
- LINK_LEG is the plug: a spherical cap, ball r 2.689, glue face r 2.42 sitting 0.37 above the ball's centre.
- LEG_HIGH (thigh): hip cup r 2.889 at (−0.38, −0.146, 8.831); knee fork centred at (0.005, −0.095, 2.168).
- LEG_LOW (shin): knee cog at (0.025, −0.454, 9.227); ankle ball r 1.343 at (0.026, −0.373, 1.345).
- FOOT_1–7: ankle cups r 1.37–1.43 (centres are in `BIONIC_DEFAULT`).
- Armour: KNEE, LEG_HIGH_ARMOR, LEG_LOW_ARMOR. They aren't in an assembly frame; a contact fit was unreliable, so they get placed by eye once and then saved.
- The STLs come as overlapping and touching shells, with stray faces and pin holes.

**The cut:**
- The leg's centre line is traced from mid-shin upwards. Mar Fil's shin points give the start; other makers' legs use a clicked Shin anchor's three points. Each step slices square to the leg and moves to the centroid of the loop round the current point.
- The cut goes 0.8 mm below where the section's area jumps (×1.6 against the median), i.e. where the thigh meets the hip armour or crotch.
- Cutters are three convex hulls: the thigh (its top held exactly on the cut plane), the shin and the foot.
- The foot's region is the points nearer this leg's skeleton than the other's. Its sole is the biggest flat patch at the bottom with "down" turned about the ankle axis, so back feet on their toes come out right. A foot unioned to a rock is stopped at a boot depth of 3.6 mm.
- The legs get one Boolean (collection operand, Manifold; Exact if the legs aren't manifold) and a Geometry Nodes tidy step. The tidy drops islands lying wholly within 1.5 mm of the cutters; it needed the cutters realised and the point positions fed to Geometry Proximity.

**The pose:**
- The plug's glue face sits on the cut centre, dome down the leg.
- The foot sits on the old sole, under the old ankle, turned like the old foot.
- A two-bone solve runs in the plane the old knee bends in, aiming 0.385 short along the hinge so the ankle lands exactly.
- Joints: Bionic Hip R/L socket (ball), Knee empty (only X is free), Ankle empty (ball); the parts themselves are locked.
- Follow Old Leg restores the pose; ◀ ▶ swaps the foot; armour toggles park a piece until Save Armour Places writes its fit (relative to its host) into its sockets file, mirrored for a left leg; Remove brings the old leg and its Shin anchor back; Mirror refuses a model with a bionic leg.

**Kit parts are cleaned on their first import** (`bio_clean`): split edges with more than two faces, drop fins of 8 faces or fewer and flat shells, fill holes, orient each shell, then union with Geometry Nodes (Split to Instances by island → Mesh Boolean, Manifold). They look the same; overlapping volume is counted once. Without this, Finalise's Exact output was non-manifold (1,000+ open edges).

**Finalise 0.3.2:** `BALL_JOINTS = {"Bionic Hip"}` makes the bionic leg split by default with no peg; shin and foot go with the thigh, and the plug stays with the body.

**Tests:**
- `test/v118/t_bionic.py`: about 176 checks over marine 29 R, L and both; legs 31 L, jump legs 37 R, 30 R and 32 L; plus Bladeguard 19 R, which is known not to work (tabard). It checks the joint chain to 0.01–0.03 mm, a shared hinge axis, the plug's glue face on the cut, the cut legs as one closed piece, knee locks, Follow, foot swap with the sole on the old sole, armour saved and mirrored, removing one side then both, and the Mirror refusal.
- `t_bionic_click.py`: the clicked Shin anchor path.
- `t_bionic_fa.py`: Finalise gives two pieces, both manifold, no peg.
- Overview image: `test/v118/bionic_leg_overview.jpg`.

# 172 - Pauldrons: Josh's new plan, every pauldron in the guide on one arm (Nov 26)

Josh: "place every pauldron onto a single arm. We then take get everything set on the placement pad as it already
is. Then specifically for the setup but not needed in squad builder I take a cut of the arm so you can shape match
back to the arms that have different geometry on the shoulders. That can then be stored as a setup part". Then: "all
of those in one file rather then by maker. I want to make sure the fit is good across all of them at the same time.
We would then only need one other file which is essentially each arm type once"; "use the fit as we have it
obviously and then hopefully its just adjustments"; "it should just be all arm types ... It shouldnt need to be every
single arm".

**So, two files:**
1. **Every pauldron in the general guide on Arm 2B R:** how each pauldron sits, its Pad R fit, the same on every arm.
2. **Each arm type once:** where the guide goes on that shoulder, the arm's Pad R. Josh takes a shoulder cut there,
   kept for setup only (not read by TIOW or the Squad Builder), and the cut matches the guide's place onto every arm
   of that shape.

Agreed as the method for anything swappable (accessories, shin pads, packs, heads; the wrist cuts already work like
this): fit each part once to one connector on one reference host, and place the connector once per host shape, with a
setup-only cut. The exception from earlier work stands: round joints take their turn from a landmark (the buckle) or
the file, not from shape.

**`kits/seat/make_pauldron_batch.py`** builds file 1 from every Shoulder Pads part in scope: 304 (Terminator, Gravis,
Phobos, Old Style, Rigging Required and hidden parts left out; knee pads are a separate category). Each column is
Torso 2, the spacer, Arm 2B R by its written fit and the guide on its written Pad R (stage 1, his), all locked, plus
the pauldron, which he moves. Left-only pauldrons show mirrored and are written as Pad L, like the left arms.

**Where each pauldron starts:**

| Start | Count |
|---|---|
| His Nov 22 placement on the guide master | 13 |
| Its own library fit, carried into the guide | 202 |
| Its own Pad L fit, mirrored (left-only) | 46 |
| No fit: a kit-mate's Nov 22 placement, bounding-box centred | 41 |
| Already his, locked (Shoulder Pad 1 and one more) | 2 |

"Its own fit" means where it sat on Arm 2B R's old Pad R (the Nov 20 pad spot socket, backup `batch write 2026-11-24
1723`), carried into the guide frame.

**`batch.py build`** now shares one mesh between locked pieces repeated column to column (same part, same placement),
so the file is 1.3 GB rather than several. A new pose, `in_pivot`, places a part by a given fit on its pivot.

**File:** `04 Stage 4 - Every pauldron in the guide (2026-11-26).blend` (spec `04-pauldrons-all.json`). Rows of 20,
60 mm apart. In a render of 10 across makers, every pauldron sits in the guide over the shoulder.

**Arm types:** `kits/seat/match_arm_types.py` fits his 21 auto pad-spot cuts (Nov 23 seat file) onto every written
arm, from the file frame and the torso place, with left-only arms mirrored. Each arm is graded same, near or no match.
Arms matching no cut become new types, one column per kit in the arm-type file.

The Nov 25-26 stage 4 pad files (Assault b, Pads by arm type) are replaced by these two.

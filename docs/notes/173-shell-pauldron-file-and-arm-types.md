# 173 - Pauldrons on the full-size shell; the arm-type file (Nov 26)

Josh, on the first pauldron file (notes 172): "The guiding part isnt on any of the pauldrons. I thought the plan was to
have a shell or similar. have the pauldron parented to the shell. Rotate the shell till its in position. The shell
going forward is a used part that sets the placement. that shell is then what i place on the arms as everything
should then match from that". Also: "I cant see the spacer on any of the parts" (it is there, inside the shoulder
joint, locked; the 0.6x guide is inside each pad). Then: "the idea behind the previous 15 fits was that it would cover
every style. Can we use that fit and then apply that to everything coming from the same pack ... Then if anything is
left over use the maker placement. Yes please go ahead and rebuild so its visible for now and movable". He confirmed
arm types only ("It shouldnt need to be every single arm"), and that the matching looks at the shoulder only.

**Pauldron file, c** (`04 Stage 4 - Every pauldron on the shell (2026-11-26 c).blend`, spec `04-pauldrons-all-c.json`):
- **The shell** is the full-size shared inside shape from his Nov 22 file (`Pauldron adapter - part with pads`; the
  seat file's guide is the same mesh shrunk 0.6x about (0, 0, -4.04), same crown frame). It's a movable part on Arm
  2B R's written Pad R and turns about its crown.
- **The pauldron** rides on the shell, also movable.
- **Where each sits in its shell:**
  - his Nov 22 fit (13);
  - else his fit of the pauldron from the same pack (folder) (117);
  - else from the same maker (95);
  - else Shoulder Pad 1's (77).
  
  Each keeps that fit's turn, and its bounding-box centre is put where that pauldron's is. The b file used the fit
  as-is and threw many pauldrons off the shoulder, because the files of a pack don't share a place. The b file was
  never handed over.
- **The write** (`"on_written_socket"`, new in `batch.py`): the pauldron's place against 2B R's written Pad R, whatever
  it rides on, is its Pad R fit. Left-only pauldrons go as Pad L.

**Arm types** (`kits/seat/match_arm_types.py`, 21 min): his 21 auto pad-spot cuts from the Nov 23 seat file, 18 usable
(Marta Gurls Arm 4 Cloth is a mirrored left; TN Mk6 is out of scope), fitted onto all 810 written arms (left-only
arms mirrored), shoulder cut points only.
- 96 matched the same shoulder (under 0.06 mm), 589 near (0.06-0.15), 125 none.
- Near matches aren't trusted: a dome patch lands near any dome. CyberBrush and BBoosty, which have no cuts of
  their own, "matched" Marta and TN cuts at near.
- So every arm not matched as the same becomes a candidate type, one right arm per kit (49 kits).

**Arm-type file** (`kits/seat/make_arm_type_batch.py`, `04 Stage 4 - Arm types, shell on each (2026-11-26).blend`,
spec `04-arm-types.json`): 67 columns.
- **18 seeded:** the shell where he seated the guide on Nov 23.
- **49 new:** one right arm per kit, the shell starting where Arm 2B R's sits on the torso.

Each column has Torso 2, the spacer and the arm as written (locked), the shell (movable; its place is that type's Pad
R and Pad L) and Shoulder Pad 1 riding on it (locked). He sets the shell and takes a setup-only shoulder cut under it.
Next: re-run the matching with his new cuts. Arms that match as the same shoulder get that type's Pad R, and the rest
become further types. Kits whose arms are all left-only are for a later pass.

Renders: in the arm-type file, 10 columns sit on the shoulder (raised arms are his to set). The pauldron c render had
not finished when this was written.

`batch.py build` shares one mesh between repeated locked pieces (notes 172), so these files stay at about 1.3 GB.

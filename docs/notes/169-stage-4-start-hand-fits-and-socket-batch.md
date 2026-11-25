# 169 - Stage 4 starts: the four reference hand fits and the arm socket batch (Nov 25)

Josh: "Yes, start stage 4". Asked which reference weapon checks Hand R: "we had defined there would need to be 4 fits.
there should be three variations of each marfil melee weapon. These relate to the angle wrist is at. The same applies
to Turtle ninja. For marta I may need to check these. This will also likely differe from the pistols and potentially
bionic hands as well due to the cuts on them". Forearm R: left for later (no reference forearm armour is placed).
Batch 1: the Mar Fil Assault arms. My reading, which he agreed to try ("lets give it a try"):
- one Hand R socket per arm, at the wrist;
- the reference is Arm 2A R, where he placed the four hand weapons;
- in stage 4 he moves Chain Sword 1 R in each hand; the other variants share the socket;
- pistols, bionic hands and Marta get their own fits in stage 5.

**The four reference hand fits** (`kits/seat/ref_hand_fits.py`, backup `ref hand fits 2026-11-25 2305`): Chain Sword
1 R, 2 R, 3 R (cuts `Assault weapon wrist 1/2/3`) and Shield R (`wrist shield`), each placed by Josh on Arm 2A R in
the reference file. Each Hand R fit is from his placement against 2A R's Hand R socket, kept as the frame and marked
Josh's (`kb_josh`). They were 0.02-0.11 mm and 5.2-6.0 deg from the old cut-search fits, and placed socket . fit they
match his placements to 0.0000 mm. Marked exact.

**`kits/seat/make_socket_batch.py`** builds one column per arm: Torso 2, the spacer and the arm as written (all
locked), plus two pieces Josh moves:
- **Pad R:** the pauldron guide, with Shoulder Pad 1 riding in it by its written fit. It starts where Arm 2B R's guide
  sits on the torso, since pads sit the same on the torso whatever the arm. Written like stage 2's spacer: the guide's
  pivot is the arm's Pad R (and the mirrored Pad L), with the guide's frame kept in the socket (`kb_connectors`).
- **Hand R:** Chain Sword 1 R by its new fit. It starts on the arm's old Hand R socket. Written the same way, as Hand
  R and Hand L.

Arms with the hand sculpted (`noHand`) get no sword, and arms with their own pad (`noPad`) get no guide. The head is
faint. The reference columns (Arm 2B R with its guide and pad, Arm 2A R with its sword) are locked and never
rewritten here.

**Batch 1:** `04 Stage 4 - Mar Fil Assault arm sockets (2026-11-25).blend`: the two reference columns, then the other
21 Assault right arms. The old Pad R sockets are 37-109 deg from the starts, but they are in the old pad frame, so
that is no measure. Render of 6: the pads sit on the shoulders. The swords point every way, because the old Hand R
sockets' turns differ, so the turn is his to set by eye.

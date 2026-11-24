# 133 - Stage 2: the cloak reference and the Bike Chaplain (Nov 24)

Josh, "Finish stage 2", with his answers:
- **Chest inserts and collars:** later. They only go on certain torsos, so no `Chest Insert` or `Neck Guard` sockets
  now. The only collars are Old Style Space Knight's, a maker that is parked.
- **Cloaks:** all 27 in scope (CyberBrush 5, the Mar Fil Captain's cape, Marta Tacticus 18), with a `Cloak` socket on
  every torso.
- **Bike Chaplain:** a batch he places by eye.

**Batch:** `~\Desktop\mar fil connectors\batches\02 Stage 2 - cloak reference and Bike Chaplain (2026-11-24).blend`.

**The cloak reference.** The Mar Fil Captain's cape is placed on the locked Torso 2 (`make_torso_batch --cloak-ref`).
- It starts in its rig frame, which is Torso 2's own (Mar Fil parts share it). It drapes over the shoulders and
  backpack, as on the Captain.
- Torso 2's new `Cloak` socket starts as its Back frame.
- It is written as `both`: the socket, and the cape's fit from Josh's placement.

The later cloak batches carry this socket to every other torso by their (now Josh's) Back sockets; Josh fixes per
torso.

`joints.json` is left alone until stage 6. Cloaks stay in `noJoint`, so TIOW Inbox and the Squad Builder are
unchanged until cloaks have fits.

**The Bike Chaplain.**
- Bike Body 1 and 2 are the bike (about 40 mm long), not torsos, though filed under Chests; they are left out.
- The Chaplain Chest is Torso 2's sculpt, 31 mm lower in its file. It had no sockets, so the cut fit now starts from
  the bounding-box offset (`carried`, only for a torso with no sockets). All four cuts land (rms 0.000-0.010 mm), so
  it starts like any Mar Fil torso.
- When nothing lands, `carried` now gives a rough start (Torso 2's socket moved by that offset) for Josh to place by
  eye, instead of leaving the torso out.

**Fixed: `write` on a host with no sockets** skipped the mirrored `Shoulder L`, because there was neither a top-level
one nor a mirror variant. It now writes it at the top level.

**Checks.**
- Every mesh matches its recorded frame (worst 0.0013 mm over 17 pieces).
- `write --check`: Torso 2 Cloak (new); the cape's Cloak fit (new); the Bike Chaplain's Shoulder R and L, Neck, Back
  and Waist (new).
- Renders `02c check - ...png`.

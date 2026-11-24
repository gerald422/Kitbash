# 128 - Stage 2: Redwarden and Turtle Ninja torsos, batch 1 of 3 (Nov 24)

Josh: "go ahead with the other torsos". That is the Redwarden torso and the Turtle Ninja straight torsos (PLAN scope).
Batches hold about 20-25 torsos (Josh, notes 127).

**Which Turtle Ninja torsos (`kits/seat/straight_torsos.py`).** Turtle Ninja ships each torso as 9 copies, and only
the straight one is used (notes 094). "Usually 1 or 9" was not a rule, so it is measured from the sockets alone (the
mating frames):
- A torso is straight when its old left shoulder is its right one mirrored across its own mirror plane, to 0.05 mm
  and 1 deg. The mirror plane is the waist socket's turn, through the middle of the shoulders.
- The posed copies miss by 18-26 deg. Every Mar Fil torso passes (0.007 mm).
- Exactly one copy of each letter passes, except the old Mk2-6 builder, which has a few nearly straight copies; there
  the most symmetric one is taken.

That gives 55 torsos plus the Redwarden torso. The whole-body models (Moritat, the Mk4 Tactical bodies, the Librarian)
have no Waist and are left out.

**Batch 1:** `~\Desktop\mar fil connectors\batches\02 Stage 2 - Redwarden and Turtle Ninja torsos 1 (2026-11-24).blend`,
22 torsos:
- the Redwarden Prime Techmarine torso;
- Mk2 Upper A1 and B1, Mk3 Upper A3, Mk4 Upper A1 and B1, Mk6 Upper A9 and B9;
- the Mk6 Assault Torsos A-F and Universal A-F;
- the two Mk10 Assault torsos.

Batches 2 and 3 are the Mk7-8 torsos (33).

**Where each piece starts.** Josh's Mar Fil cuts land on none of them, so every piece starts on the torso's own
existing socket. Some are visibly off, for example the Mk10 helmets sit low in the collar. Josh moves them.

**Three fixes needed for other makers' files:**
1. **Mirror plane.** Turtle Ninja files lie Y up, with the mirror plane at z = 6.4 (Mk10: x = 6.5), so the old "mirror
   across X = 0" was only right for Mar Fil. A host now carries a `mirror_frame` (`make_torso_batch.mirror_frame`).
   `build` mirrors across it with an empty, and `write` mirrors the left socket the same way
   (`SL = F MX F^-1 S MX`). Hosts without one still use X = 0, so nothing already written changes. The written left
   shoulders come out within 0.05 mm and 0.22 deg of each torso's old left socket.
2. **Stood on its waist.** Each torso gets an explicit `matrix` pose, so its waist sits on Torso 2's. Every column now
   stands upright, facing the same way.
3. **Quaternions.** The first build put Back and Waist up to 0.5 deg off their sockets, with no shift. Blender's XYZ
   Euler angles lose precision near gimbal lock, and standing a Y-up file upright puts it there. Batch objects now use
   quaternion rotation. After the rebuild, every untouched socket reads back exactly. The first file is in
   `batches\_superseded\`.

The generator's `os._exit` also hid tracebacks; it now prints them.

**Checks.**
- Every mesh matches its recorded frame (worst 0.0037 mm over 184 pieces).
- `write --check` lists only the expected socket writes: 0.000 except the mirrored left shoulders, as above.
- Renders beside the batch: `02t check - row 1-3.png`, plus close-ups of the Redwarden, Mk6 and Mk10 torsos.

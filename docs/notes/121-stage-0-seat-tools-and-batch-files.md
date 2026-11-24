# 121 - Stage 0: the seat tools in the repo, batch files, the stage 1 file (Nov 24)

Stage 0 of `docs/PLAN.md` (agreed Nov 24).

**The method moved into `kits/seat/`.** The Nov 23 seat-by-shape scripts are now modules that run inside Blender:
`geom`, `pads`, `legs`, `buckle`, `cuts`, `mirror`, `render`. They hold the same code, with objects and paths as
arguments instead of fixed names. The skill's script table now lists them (`.claude/skills/kitbash-seat-by-shape`).
The old copies stay on the Desktop as history.

Port check: the original `joint_seat` and the ported `pads.joint_seat` were run on the same objects (Josh's 2B R
guide seat carried to Intercessor Arm 5 R in the Nov 23 seat file). They give the identical seat: 0.00 mm, 0.0 deg,
same turn and cost.

That seat is 12 deg / 0.85 mm off Josh's own hand seat for that arm; the held-turn variant is 13 deg off. Carrying
2B R's seat onto 2B R itself comes back 3 deg off. So the method is a starting point and Josh's fix is the answer,
as the plan says.

**Batch files: `kits/seat/batch.py`.**
- `build SPEC`: makes one Blender file from a spec (`kits/seat/batches/*.json`). Each piece has a role:
  - host: solid and locked;
  - check pieces: solid and locked;
  - neighbours: faint, unless approved;
  - parts to fix: free, each pivoting on its joint (its origin is the joint).
- Parts hang in a chain, so whatever sits on a part moves with it.
- Every piece records where Claude put it and how its library STL (or a connector's own frame) lies in it.
- Poses can come from a source blend (the mesh is found in its library file by its edge lengths), kept relative to
  another piece, carried from a socket onto the pivot, or placed on the pivot.
- A "pre-set" repeated fix can be applied, `--then SCRIPT` runs a seat method before the seats are recorded, and an
  existing file is never written over.
- `read BATCH`: per part, what Josh changed at its joint (mm and deg, in the pivot's axes, relative to what it sits
  on). It also gives where the part now sits on its parent's frame. When parts on the same joint changed the same way
  (0.2 mm / 1.5 deg), it reports one repeated change with its 4x4 for `preset`.
- `compare A B`: the same pieces in two files, relative to the host. This is the check after a write.
- Connectors with no library file have their own frames:
  - the Springles spacer (from Josh's `Operation Marine\arms.blend`): Mar Fil axes, origin at the centre of its torso
    face, `arm seat` 2.085 mm out, where the Springles arms' flat sits;
  - the pauldron guide: its own mesh frame (crown, +Z out, +Y front).

**The trial batch is the stage 1 file (Josh's choice).** It is
`~\Desktop\mar fil connectors\batches\01 Stage 1 - reference marine (2026-11-24 b).blend`, built in 8 s.
- Torso 2 is locked.
- The spacer starts on Torso 2's `Shoulder R` socket.
- Arm 2B R is in Josh's reference pose, moved out 2.085 mm by the spacer.
- The guide and pad are his Nov 23 seat on this arm.
- Chain Sword 2 R rides with the arm.
- The helmet, backpack, Legs 1A and both shin pads are locked check pieces from the reference.
- The left side is mirrored live across the torso.
- Faint: the arm where it was before the spacer.

Checked independently:
- the spacer face is on the socket (0.00 mm);
- the arm moved 2.085 mm with no turn;
- the guide in the arm and the pad in the guide match the seat file (0.00 mm, 0.0 deg).

**Fix, same day: the first build's pad was 2.7 mm off (Josh: "the pauldrons here are wrong").** `make_mesh` stored the
mesh as K^-1 @ own instead of K @ own. That is only right when K is its own inverse (the arm's was, so it read true);
the pad's K is not. The check above compared the recorded matrices, so it could not see a wrong mesh. The new check is
the library STL placed by `matrix_world @ kb_own_in_obj` against the mesh itself (0.000 mm on every piece), plus the pad
and guide by their meshes against the seat file (the same to 0.01 mm). Rebuilt as `... (2026-11-24 b).blend`; the first
file was never touched by Josh and is left as it is (his to delete).

The reader was tested on a copy with made-up fixes: a 3 deg turn on the spacer, and the same move and turn on the
guide and the pad.
- The arm that only rode along read "unchanged".
- The same change on two parts was found as one repeated change.
- `compare` matched every untouched piece at 0.00.

**Not done yet: the write step.** After Josh's fixes, his placements go to the library with a backup:
- Torso 2's spacer socket and the arm's fit on the spacer;
- the arm's `Pad R` (the guide) and the pad's fit in the guide.

How the spacer's two frames go into TIOW's one socket x fit (the 2.085 mm on the torso side or the arm side) is
settled at that write.

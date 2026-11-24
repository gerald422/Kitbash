# 122 - Stage 1: the reference marine written to the library (Nov 24)

Josh fixed the stage 1 file (`~\Desktop\mar fil connectors\batches\01 Stage 1 - reference marine (2026-11-24 b).blend`).
`batch.py read`: he moved the **spacer 2.08 mm straight into the torso**, with no turn. The arm, guide and pad were
unchanged. So the arm rides back exactly onto his reference pose (0.00 mm from the faint "before the spacer" copy).
The spacer's torso face sits 2.085 mm inside the shoulder, and its arm seat is where the arm met the torso before.
That settles where the spacer depth goes: on the torso side, inside the socket.

**The write step: `batch.py write BATCH [--check]`.** A spec part with `"write": {"host", "socket", "mirror"}` gets its
joint written. Connectors have no library file, so they collapse:
- the socket = host -> the frame the part sits on (the spacer's arm seat, the guide's crown);
- the fit = that frame -> the part;
- each connector's own frame in the socket goes in `props.kb_connectors` (TIOW copies only `ws_` / `tiow_` props).

The mirror socket goes in the host's top level, or into its mirrored L variant if it has one. The mirror fit goes into
the part's mirrored L variant. Left = right conjugated by the X = 0 mirror, as the batch showed it and as the existing L
sockets are made.

Josh's sockets get `props.kb_josh` (the batch file's name). `kb.sidecar.protected` now keeps those, so no later write
or merge can change them (PLAN Rule 1). His fits go in `exact`, which merge already keeps.

The write stops if:
- a locked piece moved;
- a protected socket or exact fit is in the way (a second write was refused, as it should be);
- the write adds a sidecar problem. Pad 1 had no `schemaVersion` before; that stays as it was.

It backs up first, writes the library, and writes the repo copy only where it was byte-identical. Then it places each
written joint the way TIOW does (socket . fit) from what is on disk and checks it against Josh's file.

**Written (backup `D:\Kitbash Library\_backups\batch write 2026-11-24 1723\before\lib`):**

| Sidecar | What | Change from the old |
|---|---|---|
| Torso 2 | `Shoulder R` = the spacer's arm seat, spacer frame in props; `Shoulder L` mirrored | 0.005 mm / 0.011 mm 0.07 deg |
| Arm 2B R | `Shoulder R` fit; `Shoulder L` fit in variant 83-Arm-2-L-A | 0.006 mm 0.04 deg |
| Arm 2B R | `Pad R` = the guide's crown (+Z out, +Y front); `Pad L` mirrored in the variant | 2.8 mm 38 deg (new frame) |
| Shoulder Pad 1 | `Pad R` fit = the pad in the guide | 2.8 mm 39 deg (new frame) |

Check from the library: the arm on Shoulder R and the pad on Pad R come out at 0.0000 mm and 0.000 deg from Josh's file.

**Mixed until stages 4 and 5.** Arm 2B R's Pad R and Pad 1's fit are now in the guide frame, while the other
pads (228 with a `Pad R` fit, 39 of them Mar Fil) and arms (523 with a `Pad R` socket, 118 Mar Fil) are still in
the old pad-spot frame. Until their batches are written, in TIOW:
- other pads on Arm 2B R sit about 38 deg off;
- Pad 1 on other arms sits about 39 deg off.

This is the order the plan sets (stage 4 = arms' Pad R, stage 5 = pads), and nothing else was changed.

# 147 - Stage 3: the left-only arms, fixed as their mirror image (Nov 25)

Josh: "Yes, start them" (the Mar Fil left-only arm sculpts).

## How the right versions work

TIOW already makes them. Say a part of a mirror type (arms, held weapons, hands) goes on a right shoulder, but it has
only a left fit and no maker's right copy. Then TIOW Inbox brings in its plain mirror image, with mesh, sockets and
fits mirrored (`mirror_for_side`, 1.17.10). No second STL or right fit is needed.

So each left-only arm only needs its own Shoulder L fit approved on the spacer. Josh fixes it the same way as every
right arm: on the right spacer of Torso 2.

## The batch tool

- **`make_arm_batch.py --left`:** each arm is shown as its mirror image on the right spacer (spec `"mirror_mesh":
  true`). The original sculpt shows live on the left. The arm starts at the mirror of its old left seat:
  MX . S_L(old) . F_L(old) . MX.
- **`batch.py build`, `mirror_mesh`:** the STL's triangles are mirrored across own X, with the winding reversed. The
  part's own socket frames are not used.
- **`batch.py write`, `"left": "Shoulder L"`:** the part's own fit is the left image of Josh's placement:
  F_L = S_L(lib)^-1 . Pm . S . F . MX, where Pm is the host's mirror across its mirror plane. It is written as
  `fits["Shoulder L"]`, in `exact`, with a note. Nothing is written for the right side. The read-back check places
  S_L . F_L and compares it with the left image in Josh's file.

**Proof:** a `--check` write on the unchanged first file gives each arm's old Shoulder L fit back to within
0.009 mm / 0.06 deg, the same rounding the right arms showed (0.006 / 0.04).

## Batches

There are about 105 Mar Fil left-only arms. All have an old Shoulder L fit, and none has a mirror variant.

| Batch | Arms | Count |
|---|---|---|
| 1 | Assault Arms 1B-12C L (B and C) | 24 |
| 2 | Intercessor Arms 1-6 L, the single bolter L arms, Plasma Incinerator 4B L, Pyreblaster 7 L, 8 and 9B | 29 |
| 3 | Outrider Arms With Handle A1-F2 L and Arms 1A-6B L | 24 |
| 4 | Bladeguard Arms 1A-10A L and Sword Handled A-B, Veteran Arms A-E L, Gun 4A-4B L and Power Fists A-C, Techmarine Arms 1-3 L, Captain with Jump Pack Arm 4 L, Bike Chaplain Arm L, Jump Chaplain Arms A-D L | 31 |

**Batch 1** is `03 Stage 3 - Mar Fil Assault left arms (2026-11-25).blend`. Renders of 9 columns show each
mirrored right arm and its live left sculpt as a matching pair.

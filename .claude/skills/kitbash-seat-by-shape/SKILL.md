---
name: kitbash-seat-by-shape
description: Use when seating a Kitbash part onto its host in Blender by shape (pads on arms, legs on waist adapter 3, arms on torsos), when carrying one of Josh's placements across parts of the same shape, when turning legs by the belt buckle, or when taking cuts automatically from seats. The method from Nov 23 2026, with what worked and what failed.
---

# Seat a part on its host by shape

Developed Nov 23 2026 on the pauldron guide seats and the Marta / Turtle Ninja legs. It places a part the way Josh does
by hand, then checks it by eye. It is the "Claude seats as well as possible" step of the plan
(`docs/PLAN.md`): Josh fixes what it gets wrong.

## Josh's own method (what this copies)

1. Line the part's mating inside up with where it should sit on the host. Look at the host.
2. Bring the surfaces together, moving and turning until they sit right.
3. Check by eye, and turn it if it doesn't look right.

Pads don't sit flush. The inside top **rests** on the shoulder (0-0.6 mm), and the rim **stands clear** by about 1-2 mm.

## What works

1. **Same-shape transfer (best, use first).**
   - Fit the host surface under one of Josh's placed parts onto another host with ICP on the outline: what the part
     sees from inside.
   - Same sculpt means median 0.03 mm or less, p90 0.2 mm or less. Then carry his pose across exactly.
   - Similar but not the same (about 0.1 mm) carries 6-23° off, so don't. The method's job is to find **which** of
     Josh's placements shares the shape. A new shape needs Josh once per shape family.
2. **Pads, carried by the shoulder joint.**
   - Keep Josh's pad at its angle to the joint axis. Sweep only the turn about the joint, then rest-fit a small move.
   - Reproduced his Intercessor pad to 2-7° (every other try was 13-50° off).
   - Josh's pads sit the same on the **torso** whatever the arm (68-73° from the joint axis), so the torso constrains
     pads too.
   - Raised arms (the Chaplains) fail: they are by-eye jobs.
3. **Legs on waist adapter 3.**
   - Start from Josh's known seat: the Marta May 2026 Legs 1 on adapter 3 under Torso 2.
   - Map each legs' waist-top flat (the biggest up-facing flat near the top) onto that seat's flat.
   - Sweep the turn ±45° with ICP of the waist block onto the known one.
   - Sit it flush on the adapter's underside.
   - Rest step (slide, turn, lift; the smallest move) until the adapter overlaps no more than in Josh's seat
     (0.11-0.13 mm).
   - The control row gave back his seat to 0.01 mm and 0.6°.
4. **The turn of round joints comes from the buckle, not the shape.**
   - A round waist (Turtle Ninja) or a disc can't fix the turn: it was 45-97° off.
   - Belt mirror symmetry gives the axis but not front from back.
   - **Buckle template:** the belt-front outer skin of one legs whose front is confirmed, matched all round a new legs
     about the adapter axis (through the adapter's **underside centre**). Two templates agree within 3°.
   - One template per buckle style. The Turtle Ninja Mk6 round slotted buckle needs its own.
   - Leave out the Primus Medicae (Apothecary) legs.
5. **Cuts taken from seats.**
   - A cut is a copy of the part's own faces in the matched region, parented to the part with identity local, plus
     `kb_` props.
   - Arm pad spot: the first ray hits from the guide's dome centre (4.04 mm under its crown) within 75° of the guide
     axis, plus one ring. The guide's pose on the arm is kept as `kb_adapter_in_arm`.
   - Legs: the waist block under the waist-top flat (h −5 to +0.6 mm, r < 9 mm).

## What failed (don't repeat)

- ICP on the adapter cap: it locks on the dome tip.
- A world-axis roll rule: it matches the shoulder's bounding box, not the pad.
- A sphere fit of the shoulder plate: it locks on the bicep.
- Pad-inside ICP with a no-penetration lift: Mar Fil pads sink into the arm by design.
- "Flush" and even-gap costs: 13-50° off.
- A shape-only coarse search: it picks the bicep.
- The "biggest joint flat" as a turn landmark: it isn't stable across arms of the same shoulder (69-97°).
- "Sticks out most" as the front of the legs: it picked the back on 7 of 21.

## Checks (always, before reporting)

- **By eye**, from the part's own axes: outside face, front edge, under the rim. Show candidates side by side.
  - Legs: a close front render of the belt only, about 13 mm wide (at 50 mm a 12° turn is invisible), with a
    centre line.
  - Fit scores don't separate turns about a flat, so the check must be visual.
- **Numbers on every part:** right side, part-in-host overlap, pad fit.
- **A left arm in a right slot** shows as the elbow bending backwards. Mirror it front to back through the shoulder.

## Working rules

- Josh allows working in his open Blender file over MCP. Long MCP calls time out (more than about 60 s), so run heavy
  fits headless on a saved copy and apply the result live.
- Before changing a pose, keep the old one on the object as a `kb_before_<step>` prop. Back up Josh's files before
  changing them.
- A file's facing:
  - Mar Fil, Turtle Ninja and Marta: out +X, front +Y.
  - Springles `arms.blend` is turned 90°: out +Y, front −X.
  - Some raw Mar Fil arm files are in no marine frame (Intercessor Arm 5 R): start from all six sides.
- Searches match the shape of Josh's mating surfaces only, never whole meshes (`CLAUDE.md`).

## Scripts (`kits/seat/`, run inside Blender)

Moved into the repo in stage 0 (Nov 24): the same code as the Nov 23 scripts, with objects and paths as arguments.
The old copies stay in `~\Desktop\mar fil connectors\_method scripts (2026-11-23)\` as history (one-off probes too).

| Module | What it does | From |
|---|---|---|
| `geom.py` | shared geometry: world vertices, BVH, probe, ICP, flats, sphere fit, the pad inside, angles | `seat_shape2`, `flats`, `legs_core` |
| `pads.py` | the guide on an arm: `outline_seat` (outline ICP), `rest_cost` / `nudge_rest` / `profile`, `joint_seat` and `joint_seat_held` (pads carried by the joint), `swing_fit` | `seat_live6`, `seat_rest`, `profile`, `swing`, `joint_seat`, `joint_run2` |
| `legs.py` | legs on adapter 3: `Known` (Josh's seat), `seat`, `rest`, `clash` | `legs_seat`, `legs_rest`, `legs_check2` |
| `buckle.py` | the buckle template (`template`, `find_buckle`), belt symmetry, `turn_legs` | `tmpl_core`, `tn_tmpl`, `belt_sym`, `buckle_core`, `buckle_apply` |
| `cuts.py` | cuts taken from seats: `pad_spot_cut`, `legs_waist_cut` | `cut_take`, `cut_take_arms` |
| `mirror.py` | `twist_check` / `twist` (a left arm in a right slot), `mirror_live` (the left side shown live) | `cloth_flip` |
| `render.py` | check renders from a part's own axes: `pad_views`, `belt_views`, `shoot` | `render_cmp`, `render_belt`, `buckle_apply` |
| `batch.py` | **batch files**: `build` a batch from a spec (`kits/seat/batches/*.json`), `read` what Josh changed, `compare` two files (docstring) | new |

A seat method runs on a batch with `batch.py -- build SPEC --then SCRIPT.py`: the script gets `objs` (id -> object)
and moves the parts before their seats are recorded.

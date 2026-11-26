# 171 - Stage 4 pads: the two-guide split, one column per arm type (Nov 26)

Josh, after the Assault b file (notes 170): "pauldrons have the same issue" (pad angle, clipping, guide off the
shoulder: "multiple of the above"); "I care more about the pads ... I'd rather get those right now"; then: "I think we
might need to combine the general guide with a maker/type guide. so the existing one sets how the pauldron sits and
the second sets where its placed on the arm". And: "try and lets see".

**The split, as stored:**
- **General guide to pauldron** (how it sits): each pauldron type's Pad R fit, the same on every arm.
- **Type guide** (where it goes on the arm): where the general guide's crown sits on each arm type. That is the
  arm's Pad R socket, shared by the arms of that type through the same-shape transfer.

**`kits/seat/make_pad_batch.py`** builds from his Nov 23 seat file (`Pauldron adapter - seat and cut (2026-11-23).blend`).
Each arm type gets a column with Torso 2, the spacer and its arm as written in stage 3 (locked), and:
- the guide where he seated it on that arm (`Adapter - <arm>`), movable; its place is the arm's Pad R / Pad L;
- that type's pauldron in the guide as he placed it, movable the first time that pauldron appears (its fit); locked
  where it repeats, or where it's already his (Shoulder Pad 1, stage 1).

Pauldrons in his guide master (Nov 22) with no arm type get a column on Arm 2B R's written guide (locked), the pad
movable: CyberBrush Shoulder Pad Set 1 (1), Redwarden Mk6 Techmarine Pad, WargamesPrint BL Pad 1. Seat-file names were
mapped to the library through `_sources.csv`: TN Mk10 2.0 Arm Right A 1 is `TN Mk10 Assault - Arm A1 R`, and Mk7 Arm
Single A 1 is `TN Mk7-8 Assault - Mk7 Arm Single A1`.

**Left out:**
- TN Mk6 Arm Right: in a "Rigging Required" folder, out of scope.
- Marta Gurls Arm 4 Cloth: a left arm mirrored in the seat file; later.
- TN Pauldron A 1: from the new cults download, not in the library. The Mk7 column shows the Mk10 TN pauldron
  instead, which works since the general guide makes pauldrons interchangeable.

**File:** `04 Stage 4 - Pads by arm type (2026-11-26).blend`, spec `04-pads-by-type.json`. 23 columns: the locked
reference, 19 arm types, and the 3 pauldrons on 2B R's guide. Render of 8 columns close up: the pads sit on the
shoulders as he seated them.

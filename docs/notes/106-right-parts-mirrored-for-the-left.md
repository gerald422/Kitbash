**Right parts mirrored for the left by default (Nov 15): TIOW Inbox 1.17.10 and the page.** Arms, held weapons and
hands are offered and placed for either side, as their mirror image when they are fitted for the other side only.

- **Josh, Nov 15:** "I think the default should be mirroring. The same with the arms hands weapons etc. I think we
  should be using right arms and weapons and just mirroring everything."
  - Asked about the roughly 610 left arm and weapon files with their own sculpt and no exact right twin, he chose to
    keep them as extra designs. So they stay, and are offered on the right as their mirror image too.
- **Rule** (the same on the page and in TIOW Inbox): this applies to a part of a type marked `"mirror": true` in
  `joints.json` (Arms, Pistols, Melee, Shields, Hands). If it goes onto side S, has no fit for `<socket> S`, has a fit
  for the other side, and has no maker's copy for S (a folded variant), it comes in as its plain mirror image.
  - Its mesh, sockets and fits are all mirrored, the same as the Mirror button, but nothing is saved.
  - A moved file's `origin.joint` counts as its fit, and folder fits count too.
  - Parts with no fit for either side are unchanged: the hand rule still places a fitless weapon.
  - Pads keep `mirrorLeft`.
- **Code:**
  - Add-on: `mirror_for_side` in `addons/tiow_inbox_src/07_one_file_both_sides_1_16.py`, called in `import_request`
    (01) after `pick_variant`, reading the side from the request's socket or the selected socket.
  - Page: `asFor` in `squad-builder/src/app.js`.
  - `tools/gen_joints.py` now checks the page's `mirror` key against `joints.json`.
  - `gen_joints.py` re-splits the built add-on over `addons/tiow_inbox_src/`: run it before editing the sources, or
    edit again after.
- **Checks:**
  - In Blender (1.17.10, Assault Torso 3), Arm 1A R + Chain Sword 2 R sent to Shoulder L / Hand L land as the exact
    mirror of the same parts on the right (all vertices, max 0.0000 mm). Arm 5C L + Chain Sword 2 L sent to the
    right do the same.
  - The golden squads under 1.17.9 and 1.17.10 give all 140 parts where they were: nothing on its own side moved.
  - On the page (real library, Torso 2): the left arm slot has 831 candidates, 426 of them mirrored rights; the
    right arm slot has 865, 359 mirrored lefts; the left hand has 844, 232 mirrored. A mirrored Chain Sword 2 R on
    a mirrored Arm 1A R sits exactly at the mirror of the right pair (difference 0).
- **Not done:**
  - Near-twins (e.g. the Intercessor bolter pistols L / R whose hands differ by 0.5 mm) are offered twice per side:
    once as the part itself, once as its twin mirrored.
  - Connectors and fits are still worked out per file; under this rule only the right side strictly needs them.
- **Delivered:** `addons/tiow_inbox.py` (Blender add-on and bridge copy), `bridge/_library.json`, the page
  (`kb.py install mirror-2026-11-15`; old copies in `_backups\mirror-2026-11-15\before`). Josh restarts Blender.

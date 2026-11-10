**Lift-out, 18 Oct 2026:** `lift_parts_to_library.py` plus TIOW Inbox 1.1, both in `Desktop\TIOW Blender bridge`.

**What it does:**
- Exports each part of a worked kitbash `.blend` as an STL in the part's own frame, so the origin is preserved and object scale is not applied.
- Files it under `Library\<Creator - Mark>\<Kit>\<Type>\`.
- Writes `<part>.sockets.json` carrying sockets (relative to the part), per-part fits (`ws_fit::*`) and a snapshot of the fit types used.
- Saves every captured fit type to the Joint Library as "Kitbash master".
- Writes a CSV report; dry run by default.

TIOW Inbox 1.1 rebuilds those sockets and fits on import, and adds missing fit types without overwriting existing ones.

**Results on `3rd attempt finalising.blend` (24 Sep):**
- 185 parts → 182 STLs (3 copies skipped). 179 were traced to Mar Fil source files by name and triangle count.
- Origins: 112 set by Josh, 60 still as exported (37 two-handed guns, 18 helmets, 4 pistols, the torso), 6 with no known source.
- 46 parts carry sockets; 33 fit types.
- Destinations: Tacticus (AssaultMarines-V2 88, VeteranSquad 56, VeteranBladeSquad 16), Terminator (4), `_Unsorted\Mar Fil\HelmetsUpdate` (8), `_Unsorted\From 3rd attempt finalising` (6: four heavy weapons with cables, `base_32_mm_1` with its leg sockets, `iron_father_weapon`).

**Round trip tested:**
- The torso came back with 4 sockets.
- The combi weapon and helmet snap onto the lifted torso exactly as assembled.
- The jump pack lands on its socket. In the file it sits 0.146 forward and 0.77 lower, a hand nudge, which only survives if Store Per-Part Fit is run first (tested).

**Findings:**
- The torso's three sockets in that file (arm__Torso_r, Backpack, Head) are in no collection, so they can't be seen or selected.
- Helmet "2" is scaled 0.88 and `151-PowerAxe-2-2-B` scaled −2.3/−2.3/−0.674 in the scene; both are exported unscaled.

**The real working file is `Operation Marine\3rd attempt finalising actual.blend`** (4 Sep, 1.5 GB). It holds 550 objects:
- 435 meshes: 422 parts and 13 ND/BoxCutter helpers;
- 109 sockets;
- 4 other empties;
- 2 cable curves.

**Lift result:**
- 412 parts written, 33 of them variants and 10 identical copies skipped.
- 158 traced to Mar Fil: 94 with origins Josh set, 64 as exported.
- 254 from other creators go to `_Unsorted`: HeresyArms_r pattern C/P arms, the heresy Lower A/B/C legs, Torso new (Mk6/Mk8 and Upper A–Q), New backpacks, Raptor chainswords, Narthecium arms, claws, wings.
- 107 of 109 sockets carried; 2 have no parent.
- Export is now "as you see it": modifiers (except WS_) and scene scale applied, mirrored parts made true mirror copies.
- Same-named copies that differ in mesh, origin, scale or sockets are kept as variants.

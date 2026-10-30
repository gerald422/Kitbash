# Part Sockets × TIOW-FTRP — integration review

Reviewed 17 Oct 2026 against:
- **TIOW-FTRP**: the installed build in `%LOCALAPPDATA%\TIOW-FTRP` (16 Oct). Vanilla JS + three.js front end, Node server on `127.0.0.1:47741`.
- **Part Sockets 6.2.0**: `Desktop\part_sockets_6.2.0.zip`. Blender 5.1 still has **6.1.0** installed. The only code differences (checked file by file) are the cable repeat-unit picker and thumbnails. `sockets.py` is identical in both, so everything below works on either version.

> **Decision (17 Oct 2026): keep the integration light.** TIOW only works as a browser that sends a file into Blender. Part Sockets does all the work before and after. Built and tested: `Desktop\TIOW Blender bridge\`.
> - **`tiow_inbox.py`**: a Blender add-on. It checks `%LOCALAPPDATA%\TIOW-FTRP\local-data\blender-inbox` every 0.5 s and imports each requested STL into the open scene. Each part goes into a collection named after its TIOW category, centred on the 3D cursor at mm scale, and is left selected and active.
> - **`apply-blender-bridge.mjs`**: patches TIOW with anchored edits and keeps backups; `--undo` restores the originals. It adds *Send to Blender* (double-click a card, right-click menu, or the details button) and a `/api/local/blender` server route. The route resolves the file through the server's own `safe()` check and writes one request JSON.
> - A `.listening` heartbeat tells TIOW whether to say "Sent" or "Queued".
>
> The batch-origin and manifest designs below are parked. They are reference if a batch step is wanted later.

> **Scope narrowed (17 Oct 2026): four primary creators** — Mar Fil, Marta PunkGirl, Springles, Turtle Ninja.
>
> **Mar Fil, measured on 4 kits in `Desktop\All Mar All the time`:** parts are exported in assembly position. Within a kit, every arm's shoulder plane sits at the same coordinate:
>
> | Kit | Right-arm shoulder plane | Mirrored arms |
> |---|---|---|
> | Intercessor | max Y = −5.7 | min Y = +5.7 |
> | Terminator | max X = −6.0 | — |
> | Aggressor | min X = +5.5 | — |
> | Veteran | min X ≈ 5.2–5.5 | max X ≈ −5.3 |
>
> So within a kit, one hand-set origin is the exact origin for every sibling: copy the frame, with no geometry search and no roll problem. Templates are per **kit + slot**, not per creator, because the left–right axis differs between kits (Y for Intercessors, X for the others). The left side should be derivable by reflecting across the kit's mirror plane. `Scaling.txt` gives per-kit rescales (e.g. Intercessors 95%).
>
> **Offsets:** with one shared origin convention (joint-face centre, +Z out of the joint, +Y forward), one offset per joint type serves every creator. Creator-specific fit types are only needed where the joint is physically different. Store those as Joint Library sets with distinct type names, because loading two sets unions them.
>
> **Revised 17 Oct 2026: flat discs, not Shape Match.** Arm, leg and chest joints are flat discs for every creator (Mar Fil's legs and chest are the exception). Shape Match can't locate or roll a flat disc. The Set Origin at Flat engine can, run automatically.
>
> Tested on `Operation Marine\3rd attempt finalising.blend` (24 Sep):
>
> | Part | Rule | Found | Area | Distance from Josh's hand-set origins |
> |---|---|---|---|---|
> | Arms | largest flat patch facing −X | 33/33 | 16.1 every time | 0.02–0.11, one at 0.27 |
> | Legs | largest flat patch facing +Z | 21/22 | ≈36.8 | 0.1–0.28 |
>
> - The one leg miss (32-Legs-5) picked a 21.6 patch, so an area check would flag it for review.
> - All arms keep their imported rotation (rot = 0). Josh's convention is: origin at the disc centre, axes as imported, identity offsets.
>
> **Revised master:** disc direction in that creator's import axes, disc area (±10%), and a fixed creator correction. To apply one, find the matching patch, put the origin at its centre, and set rotation to the import axes × the correction. Fall back to a roll sweep only for creators whose export orientation varies.
>
> **Cross-creator example in that file:** torso `23-Torso-2.001` carries `arm__Torso_r` and `HeresyArms_r`. The second is the first rotated 91.7° about Z, shifted −0.17 along X and −0.73 along Z in socket space. That is that creator's correction. Recommended: bake corrections in at import so each torso needs one socket per joint.
>
> **Units:** that file is `scale_length` 1.0 (metres) with parts at 1 STL unit = 1 BU. The inbox add-on now defaults to 1:1. Bake for Print exports ×1000 in such a scene, so set Unit Scale to 0.001.
>
> **Decided 17 Oct 2026: one connection point per joint, with each creator's correction baked into the origin at import.** This covers arms, heads, pauldrons and backpacks.
>
> **The waist is the exception.** Mar Fil sculpts the belly armour on the legs, not the torso, so his waist is a different joint, not a correction. It is modelled as two joint families:
> - `waist_mar`: Mar Fil torso ↔ Mar Fil legs.
> - `waist_std`: any non-Mar torso ↔ any non-Mar legs, after corrections.
>
> Cross-family:
> - **Mar torso on other legs:** the filler piece Josh already uses, treated as an adapter. It sits on `waist_std` and carries a `waist_mar` socket.
> - **Other torso on Mar legs:** one cross offset type, captured once and chained against the Mar legs' waist socket.
>
> That makes a 2×2 waist setup however many creators there are, unless a third waist style turns up. The captured `Adaptor` fit type in the example file may be the filler; to confirm.
>
> **Proposed file layout (17 Oct 2026):**
> - **Top-level folders** are named `<Creator> - <Mark>` from fixed lists. Each is connected in TIOW as its own folder, so TIOW's Source filter becomes the creator + mark filter. Blender reads creator and mark from the same folder name.
> - **Slot** comes from the kit's own subfolders through an alias list (Helmets → Heads, Chests/Bodies → Torsos, …). Side comes from the direction the disc faces.
> - **Raw files only;** paths containing "support" are skipped.
> - **Misc bits** go in `Bits - <Type>` folders. A bit family with a repeatable mount gets one socket type and one master, with no creator correction. Bits with no mount are free placement: imported at the cursor and positioned with Settle / Conform Detail.
> - **Creator-specific adapters** (e.g. the Mar Fil waist filler) live with that creator.
> - **Don't run TIOW's Organise on this tree:** it moves everything into `Master Pieces/<Category>/<Variant>`. Duplicate cleanup is fine.
>
> **Part types, 18 Oct 2026** (bridge v2, `apply-blender-bridge.mjs`; TIOW changes are a patch Josh applies):
> - **Weapons are split into** Melee, Pistols, Heavy Weapons, Two-Handed Guns, Two-Handed Melee and Shields, matching Josh's Blender selections.
> - **Where the type comes from:** TIOW's category for a file is the nearest folder named after a part type, falling back to TIOW's own rules. Aliases and stripped suffixes (RawStl, Mirrored, Sergeant, Support) come from `_library.json`'s `partTypes`; `--library` bakes them in.
> - **What it affects:** the TIOW Item type filter, and the Blender collection a part lands in.
> - **Bits** moved to a single `Library\Bits\<Type>` folder.
> - **Patch before connecting the library:** TIOW sets a file's category only when it first adds the file to a catalogue.
> - **Joints differ by weapon type:** one-handed weapons attach at the wrist (`Wrist_socket_r`), two-handed at the shoulders (the example file has a Combi weapon snapped to `arm__Torso_r`).
>
> **Lift-out, 18 Oct 2026:** `lift_parts_to_library.py` plus TIOW Inbox 1.1, both in `Desktop\TIOW Blender bridge`.
>
> **What it does:**
> - Exports each part of a worked kitbash `.blend` as an STL in the part's own frame, so the origin is preserved and object scale is not applied.
> - Files it under `Library\<Creator - Mark>\<Kit>\<Type>\`.
> - Writes `<part>.sockets.json` carrying sockets (relative to the part), per-part fits (`ws_fit::*`) and a snapshot of the fit types used.
> - Saves every captured fit type to the Joint Library as "Kitbash master".
> - Writes a CSV report; dry run by default.
>
> TIOW Inbox 1.1 rebuilds those sockets and fits on import, and adds missing fit types without overwriting existing ones.
>
> **Results on `3rd attempt finalising.blend` (24 Sep):**
> - 185 parts → 182 STLs (3 copies skipped). 179 were traced to Mar Fil source files by name and triangle count.
> - Origins: 112 set by Josh, 60 still as exported (37 two-handed guns, 18 helmets, 4 pistols, the torso), 6 with no known source.
> - 46 parts carry sockets; 33 fit types.
> - Destinations: Tacticus (AssaultMarines-V2 88, VeteranSquad 56, VeteranBladeSquad 16), Terminator (4), `_Unsorted\Mar Fil\HelmetsUpdate` (8), `_Unsorted\From 3rd attempt finalising` (6: four heavy weapons with cables, `base_32_mm_1` with its leg sockets, `iron_father_weapon`).
>
> **Round trip tested:**
> - The torso came back with 4 sockets.
> - The combi weapon and helmet snap onto the lifted torso exactly as assembled.
> - The jump pack lands on its socket. In the file it sits 0.146 forward and 0.77 lower, a hand nudge, which only survives if Store Per-Part Fit is run first (tested).
>
> **Findings:**
> - The torso's three sockets in that file (arm__Torso_r, Backpack, Head) are in no collection, so they can't be seen or selected.
> - Helmet "2" is scaled 0.88 and `151-PowerAxe-2-2-B` scaled −2.3/−2.3/−0.674 in the scene; both are exported unscaled.
>
> **The real working file is `Operation Marine\3rd attempt finalising actual.blend`** (4 Sep, 1.5 GB). It holds 550 objects:
> - 435 meshes: 422 parts and 13 ND/BoxCutter helpers;
> - 109 sockets;
> - 4 other empties;
> - 2 cable curves.
>
> **Lift result:**
> - 412 parts written, 33 of them variants and 10 identical copies skipped.
> - 158 traced to Mar Fil: 94 with origins Josh set, 64 as exported.
> - 254 from other creators go to `_Unsorted`: HeresyArms_r pattern C/P arms, the heresy Lower A/B/C legs, Torso new (Mk6/Mk8 and Upper A–Q), New backpacks, Raptor chainswords, Narthecium arms, claws, wings.
> - 107 of 109 sockets carried; 2 have no parent.
> - Export is now "as you see it": modifiers (except WS_) and scene scale applied, mirrored parts made true mirror copies.
> - Same-named copies that differ in mesh, origin, scale or sockets are kept as variants.
>
> **Auto-snap — built (TIOW Inbox 1.2.0, lift script, `_library.json` "joints"):**
> - Josh's answers: Wrist_Armout_r is for extra forearm armour (e.g. tyranid carapace plates) → **Forearm R/L**; Shield_to_hand_r is the hand's shield mount → **Shield R/L**.
> - The lift renames fit types (RENAME table; `.blend` untouched): Shoulder R ← arm__Torso_r + HeresyArms_r, Hand R ← Wrist_socket_r, Forearm R, Shield R, Neck ← Head, Back ← Backpack, Back Top ← both toppers, Pack Fin R/L, Wing R/L, Hip R/L, Belt Front ← Tabard, Base Pose 1–5, Base Jump 1–8. Waist types (Legs, Legs to chest, Chest to legs, Adaptor) unchanged for now.
> - Almost every fit type in the actual file is an identity offset (Josh's origins sit on the joint). Exceptions: Wrist_socket_r (0.25 along Z), Shield_to_hand_r (small), Adaptor (180°), Legs (old).
> - HeresyArms_r merge: 23-Torso-2.001 carries both shoulder sockets; HeresyArms_r sits 0.75 mm and 91.6° from arm__Torso_r. That difference is baked into the 75 heresy arms' STL origins (creator correction in the origin, as agreed), and the twin socket is dropped. Generic rule: a merge needs a part carrying both sockets; without one, a merge only happens if the offsets are equal, else the second keeps `"<new> (<old>)"`.
> - Inbox: the model selected when a part arrives is the target. Part type → socket from `_library.json` "joints" (found by walking up from the STL; defaults built in). Side from name/folder words. Selected socket or same-kind part wins; else first free socket in the assembly; else swap. Hidden parts on a socket don't occupy it (Josh parks variants hidden). Held parts move across to the new part's same-type socket. Outgoing TIOW imports are deleted, Josh's own parts go to Dressing Room home (pref). `jointAliases` let library parts snap into old-named files (arm__Torso_r = Shoulder R).
> - Tests: `test_autosnap.py` (arm→Shoulder R, pistol→Hand R, swap keeps pistol, heresy arm lands where HeresyArms_r put it, helmet exactly as in file, left arm/no selection messages, pauldron fit + settle, Backpack2 settle), `test_alias.py` (into the real file), roundtrip/fit/inbox tests updated and passing.
>
> **Accessories (pauldrons, belt bits, shin/knee pads) — Josh's question, Oct 18:**
> - **Settle** (built): after the snap, slide along a socket axis until the part touches the host and anything else on that socket. Contact over the whole part (rays both ways via BVH), not Part Sockets' single-ray Settle Along Axis. On Josh's Backpack2 it reproduces his hand placement to 0.007.
> - **Pauldrons:** anchor = Shoulder socket (exists). One "Pauldron R/L" fit captured once, then settle down (-Z). In the joints table.
> - **Belt items:** a belt ring on legs pieces — rays out from the waist joint at fixed angles (front 0°, hips ±90°, back 180°). Found on all 28 legs pieces in the file. Front must come from the waist joint's convention: guessing front from shape (knee bend) was backwards on 14 of 27 heresy legs. Not built.
> - **Knee/shin pads:** pose moves the knee; knee-finding from shape alone (surface geodesics, leg split by nearest foot, hip/ankle proportions) was off by a few mm and unreliable. Options: the creator's own mount if it has one (Mar Fil legs have a round flat on each shin — unconfirmed what the pads mate with; the flat-disc finder picked the toe caps instead), or Knee/Shin R/L sockets clicked once per legs piece and carried in the library.
> - **Mar Fil kit frame:** Mar Fil exports every part of a kit in one shared frame (torso z 25.5–37.1, helmet on top at 33–42, jump pack behind at y −14.6…−3.6, arms beside the torso). Same-kit accessories could be placed exactly as designed if the lift records each part's kit position. Needs shin pads/pauldrons/pouches from Josh's drive to confirm.
> - Prototype code: `/home/claude/proto/` (lm3.py, flats.py, settle_proto.py, render_lm.py).
>
> **"for claude.blend" (Desktop, Oct 18) — parts as they arrive from each creator:**
> - **Mar Fil:** body parts share one kit frame — legs 35, torso 22, helmet 4, jump pack 55 assemble untouched, model standing on the origin, facing +Y. Accessories arrive upright in their own family frame, identical for every variant in a family (shoulder pads 56–60, 62–65; shin pads 68–73; pouches 230–237; seals; relics; holsters). Shin-Pad 29–32 arrive in kit position on legs not in the file.
> - **Marta:** lying in print orientation, bbox corner at the origin. Some variants share a frame (torso_3/4, helmet_3/4), others sit elsewhere (torso_2 at x≈60). "Chin_pad_*_L/R" are shin pads (half-tube greaves, no peg).
> - **Turtle Ninja:** lying in print orientation near the origin. Variants differ by pose (torso twist, leg pose), so joint discs move between variants even when the file frame matches.
> - **Springles:** standing upright (feet on z=0) but scattered over a print plate at different positions and rotations. 11 of them sit in the Scene Collection, not the Springles collection.
> - **Mar Fil shin pads are ball-and-socket:** every pad has a ball r≈1.745 at a fixed point in its family frame ((3.16, 0.10, 0.86) for 68–73; (5.31, 4.06, 9.22) for 29–32). Every Mar Fil legs piece has exactly two spherical sockets r 1.967 on the shins (sphere fit error 0.005 mm; 29-Legs-2 and 35-Legs-2-A). Seating ball centre on socket centre, pad out along the socket opening, pad up along the local shin axis (PCA within 6 mm) puts 68-family pads on both legs pieces correctly — cross-kit, since the socket size is shared. Pad outward = opposite the mean direction of the ball's surface (the ball grows out of the wall).
> - **Mar Fil pauldrons 56–60 have a spherical inner cup** r 2.805 at (0, 0.55, 0.33), fit error 0.0016, identical across the family. Mar Fil arms in the working file have a shoulder ball r≈2.28 at their origin (= the Shoulder socket). Cup centre on the Shoulder socket gives the position; the angle around the joint is one fit per family. The 62–65 family shows no consistent cup.
> - **Mar Fil belt bits** (pouches, seals, relics, holsters) and belts have no clean mating feature → anchor + family fit + settle.
> - Analysis code: `/home/claude/blend/forclaude/` (balls.py, shinfit.py, padaxes.py, contact.py, render_groups.py).
>
> **Decision (Josh, Oct 18):** don't rely on Mar Fil's ball joints. Josh checked the renders and some pads were oriented wrong. The ball fixes a point, not a direction: the turn around it came from the socket's opening axis and a local shin-direction guess, and on 29-Legs-2's left leg the opening points 38° downward, so the pad tipped. Only two of the four pad families checked had a ball or cup. Shin pads will be printed in one piece with the legs, so the goal is settled contact with a little overlap, not a matched joint. **All pads (shin and shoulder, every creator) use one mechanism: an anchor socket + one fit per pad family + settle with sink.** The Shin anchor's frame (Z out of the shin front, Y up the shin) is what makes the angle right; proposed to set it with two clicks per leg (knee, ankle), stored in the library.
>
> **Built — TIOW Inbox 1.3 (Oct 18):**
> - Place Anchor (sidebar > TIOW Inbox > Anchors): Shin R/L by two clicks (knee, ankle; socket on the knee point, Y up the shin, Z out of the front); Hip R/L, Belt Front/Back, Pad R/L by one click (Z = surface normal, Y up, or forward for Pad). Re-clicking replaces. Anchors are normal Part Sockets sockets and the lift saves them.
> - Save Fit for Folder: the first pad from a folder is parked on its anchor; Josh places it by eye and saves; `_fits.json` in that library folder gives every sibling the same fit (applied as `ws_fit::<anchor>` on import). L and R saved separately.
> - Joints: Knee Pads → Shin (sink 0.2); Shoulder Pads → Pad (sink 0.1); Accessories/Grenades/Seals/Trophies → Hip R, Hip L, Belt Front, Belt Back (sink 0.1), selected anchor wins. "ShinPads"/"greaves" folders now map to Knee Pads (patch v3).
> - **Pauldrons sit on the arm** (Josh's point): every part landing on a Shoulder socket gets a Pad anchor automatically (ray straight up from the joint to the shoulder top, turned like the shoulder socket); the pad is parented to the arm's anchor, so an arm swap carries it across and re-settles it. A first attempt that turned the pad by the arm's measured swing failed — the shape-based swing is dominated by the shoulder bulk and flipped the pad under a sideways-raised arm — so raised arms get a re-clicked Pad anchor instead.
> - Settle now stops at the anchor's part and the part it hangs from (arm + torso), and backs off twice the part's depth so a part that arrives buried still starts outside.
> - Tests (`test_pads.py`, `test_anchor_modal.py`, plus the earlier suites): shin pad lands 0.20 into the shin, pouch 0.10 into the belt, pad follows an arm swap and rests 0.10 into the torso. The real viewport click (region/raycast) is untested headless.
>
> **TIOW Inbox 1.4 (Oct 18, after Josh's review of the images: pauldron not on the arm or in its direction, shin pad pitch off from the side, only one side tested):**
> - **Rocking settle**: before the slide, the pad tilts up to ±15° per anchor axis (belt bits ±8°) to the pose where its inner side is most flush without cutting in (BVH nearest + signed distance on ~220 inner points; coarse then fine grid). Offline, a shin fit saved on 29-Legs-2 and reused on the jump legs went from 5–11° off the best-seated pose to 0.4–2.0°.
> - Pads rest on the part their anchor is on only (arm, legs) — not the torso.
> - **Pad anchor follows the arm's forward/back swing** about the shoulder-disc axis: upper-arm direction = mean of the arm between 0.35 and 0.65 of its reach from the joint (nearer in, shoulder armour dominates). Following the full 3D direction (incl. sideways raise) pushed both pads into the neck on sideways-raised arms, so abduction is ignored; `followArm` in the Shoulder Pads joint scales the swing (default 1).
> - Both sides tested (`test_both.py`): Shin R/L on two legs pieces, Hip R/L, Pad R/L through arm swaps 111 → 126 → 131 → 101 (left arms = mirrored copies; Shoulder L by Part Sockets-style conjugation). Images: shin_pads_both_legs.png, pauldrons_both_arms.png, belt_both_hips.png.
> - The "by eye" first fits in the tests are stand-ins: shins = best-seated ball-in-socket pose (rotation search about the ball, min cut + gap); pauldron = upright over the shoulder, cup over the joint, slid onto the arm.
>
> **TIOW Inbox 1.5 (Oct 18, after Josh's second review: shins and belt good; pauldrons followed the arm but floated too high; wants more shin pad variations on the assault legs):**
> - **Why pauldrons floated:** the Pad anchor's ray started inside the shoulder disc and stopped on its inner face (≈2.2 above the joint on every arm), and the stand-in fit put Mar Fil's pad cup on the joint, where the arm's deltoid pokes through the pad. Settle then lifted the pad to first contact — the pad's rim on the outer slope of the shoulder, ~6 mm high. A Mar Fil 56–60 pad's inside is a r 2.8 cup over a narrow half-cylinder; Mar Fil assault arms' shoulders (bulb ~r 3.4, top 3.5–4.5 above the joint) don't fit inside without overlap, so a pauldron always overlaps the arm.
> - **Fixes:** Pad anchor = the arm's surface straight below a point 0.1 × arm reach out from the joint (cast from above, in the swung frame), so it really is the top of the shoulder. Shoulder Pads: no rock, settle with `pushOut: false` (only closes a gap, never lifts a pad off an overlap). Stand-in by-eye: pad upright, 5° lean in, the cup's ceiling on the shoulder top 1.25 out from the joint.
> - **Settle is now relative to the by-eye placement:** Save Fit for Folder also stores how rock and slide judge that placement (`rock`: 3×3 tilt in anchor axes, `slide`: mm) in `_fits.json`. On placement only the difference is applied (and no sink), so siblings land exactly like the first pad on the same model; on other legs/arms they tilt and slide by the difference. Without this, the flush objective pulled Marta and Mar Fil 29–32 pads ~19° away from an upright by-eye pose on the same legs.
> - **Rock:** inner side sampled by rays from the model side (decoration undercuts no longer count as inner); tilt about anchor X and Y only (no spin); samples already >1.5 mm inside the model (knee cuffs, lugs) count as gaps, not cuts.
> - **Shin slide `touch: 20`:** stop when 20 % of the inner side touches rather than at first contact — the 29–32 pads have a knee cuff whose arms reach 4.7 mm behind the knee point; first contact held the pad 4.5 mm off the shin.
> - New pad families tested both legs on 29-Legs-2 and jump legs 35-Legs-2-A: Mar Fil 29–32 (Kit B, upright, outer +Y, ball on the back that lines up with the legs' socket) and Marta Chin_pad 1–3 (flat, outer +Z, knee end +Y, all share the bbox corner (0.35, 0, −0.33) so one fit carries across). Images: shin_pads_marfil_29-32.png, shin_pads_marta.png, pauldrons_on_the_arm.png (arms 111/101/126/131 both sides, plus pads 57/58 swapped in).
> - Files: tiow_inbox.py 1.5.0, _library.json (joints + about), README. Pad fits saved with 1.4 should be re-saved.
>
> **Mar Fil rigs as ground truth (Oct 18, after Josh rejected the 1.5 images and proposed three-point anchors):** Josh supplied Mar Fil's rigged build files `ChaplainOnBike-BlenderFile.blend` (Desktop\All Mar All the time\ChaplainOnBike-Bits) and `Techmarine-Build-BlendFile.blend` (D:\new cults\Techmarine-Build-BlendFile (1)). In both, the shin pad is parented to the lower-leg piece (`Knee-A-Pose.L/R`, `Knee-L/R-Pose`) and the pauldron to the arm's shoulder piece / "mini shoulder pad" (`Shoulder-L/R`, `Shoulder-A-L/R-Pose`). Shin pads go on Mar Fil legs only (Mar Fil or Marta pads).
> - **Three points (Josh):** shin = the two ankle circles (ends of the ankle cylinder) + top of the shin hole; pauldron = the two bottom corners of the arm's mini shoulder pad + a point between them. Frame: shin X across the ankle, Y from between the ankle circles up to the hole top (origin there), Z out of the shin (hole opening); pad Y along the corners, Z from the corner line to the middle point.
> - **Validated:** the rig shin pad relative to the shin frame is the same in both rigs to 0.09° / 0.004 mm. On Mar Fil legs the points are found automatically (ankle balls r≈1.75–1.82 and the hole r≈1.97 are spheres; pair = two balls ~5–5.6 apart, ~6.7 below the hole).
> - Library 68–73 shin pads are the same shell as both rig pads (ICP median 0.04–0.08 mm, rotated 90° about Z, ~2° about X) → Mar Fil's exact placement. 29–32 match partly (0.13–0.17), Marta are lined up onto the Mar Fil pad (0.23–0.42). Rendered on 29-Legs-2 and 35-Legs-2-A, both legs: all seated.
> - Pauldrons: 62–65 ≈ Techmarine rig pad (0.10), 56–60 (0.18) and Turtle Ninja (0.15) nearer it than the Chaplain pad. Assault arms' shoulder caps are not the rigs' caps (ICP ~0.4–0.5), so the soft middle point matters: "straight above the corners' midpoint" matches the rig's look; "top of the arch" sits high and leans in. Asked Josh to confirm. Arm-to-arm transfer of the three points within the assault kit works by matching the shoulder region (median 0.12–0.18).
> - **Josh's verdict (Oct 18 late):** shin pads perfect on the right leg; the left leg needs the mirrored pad (Mar Fil 68-73 and 29-32 come as right pads; Marta's `_L` files are genuine left designs, not mirrors). Left placement = the right placement mirrored across the shin frame's X (across the ankle) — done.
> - **Pauldron example from Josh:** `Desktop\pauldron placement.blend` — raw kit-frame arm `76-Arm-1-R-A` with pad `62-ShoulderPad-1` placed by hand, and six empties: arm points `Empty` (front corner), `Empty.001` (back corner), `Empty.002` (middle = top of the mini shoulder pad at its inner edge, by the disc); pad points `Empty.003`, `Empty.005`, `Empty.004` (the matching places on the pad: inner bottom corners and inner top). Pad and arm points are 2.0 / 2.2 / 0.1 mm apart, so the placement is a learnt relation: pad frame relative to arm frame (same three-point construction on both), reproduced to 0.008°. Carried to the other assault arms (76→111/101/126/131/81/91 by matching the shoulder region, medians 0.11-0.19) and to other pads by matching their shape to the 62 (63: 0.04, Turtle Ninja: 0.11, 56-58: 0.19).
> - Offline pipeline: `/home/claude/blend/mf/` (exports, `icp/` scripts, renders); 1.6 fit builders in `/home/claude/real/`.
>
> **TIOW Inbox 1.6 — built in (Oct 19, after Josh: "This all looks good please go ahead and build it in"):**
> - **Shin anchors found on import** for Mar Fil legs (category Legs) and by the *Find Shin Anchors* button. Sphere fit tightened (band follows the fitted radius, 6 rounds): Mar Fil's two rigs now agree to 0.03° / 0.001 mm in the shin frame (was 4.9° with the first add-on version, 0.09° offline). Hole top put level with the hole centre across the ankle (the rim's top vertex jumped ±0.25 mm sideways). On 29-Legs-2 / 35-Legs-2-A the add-on's frames are within 0.5° / 0.2 mm of the frames used for Josh's approved renders; 68 on the right lands within 0.6° / 0.2 mm of the approved placement.
> - **Pad anchors copied on arrival** (category with socket Shoulder): the arm's mini shoulder pad is matched to the 76-Arm-1-R-A region from Josh's example (packed inside tiow_inbox.py) or to any clicked arm in the same/sibling folder; saved to the arm's `.sockets.json`. Matching: even surface sample of the reference (vertices bias it), start points at the arm's possible shoulder joints (highest r≈2 round bits) × pitch −90..90/15 × yaw ±40/20 × roll ±20, scored, best 10 → short ICP, best 3 → full ICP; ~3.5 s per arm. Mar Fil places each raw arm differently in its file (shoulder x from −7 to +7), which the old X-rotation seeds missed (126 was 4–7 mm off). Accept ≤ 0.2 median: the assault arms 0.01–0.14, Veteran Blade arms ~0.29 (rejected: click their three points).
> - **Pad frame sign:** X out from the body on a right arm (in on a left), from the shoulder sockets (this one minus its opposite); before snapping, the arm file's +Y as forward. Both give the same frame (tested on 76 and 78).
> - **Real library (D:\new cults, folder access granted):** files match the meshes used offline exactly. Fits written as `_fits.json` / per-part `.sockets.json`:
>   - AssaultMarines-V2 RawSTL\ShinPads (68–75 co-registered to 0.3°) "Shin R" from the Techmarine rig; ShinPads\LeftOrientated "Shin L" (those files are the right ones mirrored then turned 180° about Z).
>   - VeteranBladeSquad Shin-Pads-RawSTL "Shin R" (29–35 + Flame, average; 1.2° spread — shape differs from the rig pad), Shin-Pads-Mirrored "Shin L" (exact X mirrors). Both copies of the kit.
>   - Marta `legs-chin pads and base`: per-pad sidecar fits (pads sit up to 54 mm apart in their files), R from the rig's right pad, L from its left. Both copies.
>   - AssaultMarines-V2 ShoulderPads "Pad R" = Josh's 62 on 76 exactly; 66 and 67 face the other way in their files (180° about Z) → own sidecar fits. VeteranBlade ShoulderPads-RawSTL "Pad R" (56–59 average, 62 matched onto each) + Death-ShoulderPad own fit (sits like 62); ShoulderPads-Mirrored "Pad L". TurtleNinja Pauldrons "Pad R".
> - **mirrorLeft** in the Shoulder Pads / Knee Pads joints (no rock/settle): a right pad with no left fit is mirrored onto a left socket; a `...-Mirrored` file counts as a left for these joints.
> - Tests (`/home/claude/test/v16`, real files linked into `test/reallib`): shin anchors vs numpy (<0.02°), 6 shin sets × 2 legs × both sides, 62 on 76 = Josh's example (<0.3°, <0.05 mm), left = mirrored right, arm swaps 111/101/126/131 both sides with pads carried, pad swaps 63/66/67/56/57-Mirrored/Death/58/TN, click = copy frame, clicked arm becomes the folder reference; older suites updated (Shin now three clicks; arms get a Pad anchor on import).
> - Delivered: `Desktop\TIOW Blender bridge\` tiow_inbox.py 1.6.0, README.txt, _library.json; example Library `_library.json` pad joints switched to mirrorLeft. Images: v16_shins_marfil.png, v16_shins_marta.png, v16_pauldrons_arms.png, v16_pauldrons_pads.png.
>
> **TIOW Inbox 1.6.1 (Oct 19, Josh's first real test, `Desktop\first attempt.blend`):** TIOW bridge patch applied (it never had been). Raw torsos from `D:\new cults` have no sockets, so arms don't snap onto them yet (next piece of work). Pads sent from TIOW arrive as its own "Shin Pads" type, which 1.6.0 ignored → pads are now recognised by file name (ShinPad / Shin-Pad / Chin_pad / KneePad / ShoulderPad / Pauldron). Josh clicked a Shin R when no anchors appeared (cause not pinned down; the anchors were ~1 mm arrows inside the hole): auto anchors now fill whichever side is missing, Find Shin Anchors replaces clicked ones and forgets saved clicks, three-point anchors are drawn bigger and in front, and the status line reports a failed search. Chaplain kit (`ChaplainOnBike-Bits\…\ChaplainRawSTL`) got Shin R (5-ShinPad-R) and Shin L (6-ShinPad-L, used as is) from the Chaplain rig (pads match the rig's to 0.03–0.05 mm). Captain Terminator shin pads: not for Tacticus legs (Josh). Josh confirmed the legs + Chaplain pads work in Blender. Delivery note: re-committing the same staged path wrote the old copy; stage each delivery under a new path and check the md5 on the device.
>
> **TIOW Inbox 1.7 — Assault Marines kit socketed (Oct 19, from `3rd attempt finalising actual.blend` + `posing for claude.blend`):** torso is the root; every AssaultMarines-V2 file (272) has a `<part>.sockets.json` in D:\new cults with sockets, fit and `category` (the sidecar category now wins over TIOW's, so power fists arrive as Arms and TwoHandedWeapons as Two-Handed Melee). Files merged on the drive, never replaced (existing Pad anchors kept).
> - Torso: Shoulder R (Josh's arm__Torso_r), Shoulder L (mirror), Neck (Head), Back (Backpack), Waist (Legs to chest). All 6 AM-V2 torsos and the 5 Veteran Squad chests share these joints to 0.03 mm.
> - Waist is a ball-style joint (dome in the torso, plug + stomach plating on the legs). Mar Fil's export positions don't seat the torso (29/30 sit high, jump legs are 13 mm off). Josh: "the bottom of the front lip on the torso needs to match the top lip of the stomach plating". His Chest-to-legs sockets on all 20 legs in Legs donrrr follow that rule consistently (tilt 14° fwd / 6° side vs a 28-based plating match, twist −9…−17° per legs) → used as each legs' Waist fit; 28 gets their average; Mirrored legs = mirror of the original (Mirrored-35…40 are also turned 90°). His Right/Left Hip sockets carried as Hip R/L. Base socket = legs file origin.
> - Arms: R = Josh's origins + Wrist_socket_r (type offset baked into Hand R) + Wrist_Armout_r (Forearm R, scale dropped). L-A/B/C are X-mirrors of R-B shifted along x (ICP 0.03) → mirrored sockets/fits. Power fists are whole arms; main folder = right arms, Mirrored = left; joint = arm's inner face on the shoulder axis (y 0.2, z 31.95), which matches Josh's joints to ±0.05 on his arms.
> - Hand-held: Josh's origins; 10 melee not in his file use the shared grip (his 211 bolt pistol fit). LeftOrientated = mirrors (176/177/183 slightly moved, handled). Shield 211 holds a hand → Shields joint now Hand.
> - Two-handed weapons in kit position on Shoulder R; new joint option `spans: ["Shoulder L"]` clears the left arm, and an arm on either shoulder replaces the two-hander. Jump packs: kit position (Josh). Fins 60/61 are left pieces in kit position → Pack Fin L, `mirrorSides` mirrors onto Pack Fin R. Helmets/heads: Josh's 1-Helmet-1 fit for the folder.
> - Add-on 1.7: sidecar category, joints Legs→Waist, Bases→Base, Pack Fins, spans, mirrorSides, socket types ensured before snapping. Test `test/v17/t_marine.py` builds three marines (standing, Josh's jump legs 47 exact, mirrored jump legs + power fists), 47 checks pass; v16 suites pass. Belt bits left for later (Josh).
> - Next: the other six kits (VS staged: chests/arms/backpacks/2H guns/heavy weapons in kit position; VS helmets = AM-V2 helmet frame + (1.41, 0, 35.95)); VS/VBS arm wrists to carry from AM-V2 arms by matching the cuff.
>
> **TIOW Inbox 1.8 — hands are hands (Oct 19, Josh: "a hand should be a hand regardless of the creator or set it's from"; "Go ahead with the wrist"):** the wrist joint is now a rule on both ends, worked out from the shape on import, cached in the part's `.sockets.json` (marked `"ruled": {"Hand R": "wrist-1"}` for fits, `tiow_anchor: "rule"` for sockets). Josh's own sockets/fits always win; the rule fills gaps.
> - **Arm (Hand R/L socket):** the outermost round flat face (3–25 mm², r 1–2.8, rim spread < 12 % of r) at the far end from the shoulder joint (joint from the Shoulder fit). Origin = circle fit of its edge, Y = into the arm. Roll from where the forearm armour sits: the mean lateral offset of the surface 0.3–2.5 mm behind the face, radius 1.9–4.5, lies −86° from the wrist's up (right arm; left = the rule on the mirror image). On Josh's 60 AM-V2 wrist sockets: origin 0.16 mm median, axis 0.9°, roll within 3° on the 48 oval-wrist B/L arms (spread 0.7°); the 12 round-wrist R-A arms have no roll in the wrist itself and come within ~6° on average, 4 of them 9–29° (91-Arm-4-R-A worst).
> - **Mar Fil `-Mirrored` arms are not pure mirrors:** VS `14x-Arm-?-Mirrored` forearms are turned ~150° against the mirrored right arm, so the armour cue put left-hand weapons sideways. Rule: an arm `<name>-Mirrored.stl` with `<name>.stl` beside it (sibling folder) takes the roll of that right arm's wrist, mirrored; the face stays its own.
> - **Hand-held part (Hand R/L fit):** candidate wrist stumps = flat caps 2.5–16 mm² with a neck wall right behind them all the way round (≥ 85 % of 15° sectors) and nothing in front; a reference fist (Mar Fil's assault right hand: the surface shared by its hammer, bolt pistol, knife and axe hands, 1369 points, packed in the add-on) is fitted behind each cap at 24 rolls, best 10 → ICP, plus the half-turn, then a full ICP. Y = the cap's normal, origin = cap centre 0.19 mm into the hand (where Josh's placements seat the stump in the arm's face), Z (top / blade side) from the fist. On all 82 AM-V2 hand-held parts vs Josh's (or the shared) frames: right cap every time, axis 2.5° median (6° max), roll 0.9° median (4.9° max). Variants 1/2/3 are the same fist re-posed round the weapon; the stump's own oval is 20° off on the -3s, so the fist, not the oval, gives the roll.
> - **Combined, rule arm + rule hand vs Josh's arm socket + weapon fit,** all 2460 AM-V2 arm/weapon pairs: weapon rotation median 5.1°, 90 % within 8.3°, max 33° (round-wrist arms); fist position median 0.25 mm, max 0.74.
> - **Side:** from the name/folder as before (`-Mirrored` = left); unnamed hand-held parts (VS `Melee-RawSTL`) are tried both ways and the better fist wins.
> - Power fists / claws / gauntlets (by name) get no Hand socket; arms without a round wrist face report it on the status line.
> - Speed: arm rule ~0.3 s; hand rule 2–5 s (BVH nearest in a Python loop), both once per file. `_components` was vectorised (grid pairs + label spreading): 25–30× faster, identical patches.
> - Delivered (md5 checked on the device): `Desktop\TIOW Blender bridge\` tiow_inbox.py 1.8.0, README.txt (new section "Hands are hands"). Nothing written to D:\new cults; rule results cache themselves on first use.
> - Tests: `test/v18/t_wrist.py` (kitlib + VS linked, no VS sidecars): VS arm gets Hand R by rule (= prototype), AM-V2 chainsword on it by its own fit, VS chainsword B (no side, no fit) by rule and saved, VS mirrored arm + mirrored sword (left = mirror image of right, twin rule), AM-V2 arm 77 replaces the VS arm and the VS sword moves across, AM-V2 arm 92 with its Hand R removed gets one within 3° / 0.3 mm of Josh's, pistol on it, re-import uses the saved fit (0.3 s). 20 checks pass; `test/v17/t_marine.py` 47 checks pass on 1.8.
> - Prototype + measurements: `/home/claude/kits/` (wristrule.py, handrule.py, fist.py / fistref.py, armcheck.py, composite.py, vs_rules.py; renders in `renders/`).
>
> **TIOW Inbox 1.8.1 — pauldron anchors on every arm (Oct 19, Josh: "ok go ahead"):** 16 Assault Marine arms got no Pad anchor (arm 3 and power fists 163-174): the old start grid (pitch ±90, yaw ±40, roll ±20 about candidate pivots) missed arms swung 89-97° from the 76 reference. With the arm's shoulder joint known (its Shoulder fit), `swing_match` now holds the two joints together and tries every swing up to 120° (~3100 evenly spread rotations, 80 points each), nudges the best 40 (6 ICP steps, 250 points), polishes the best 6, then the whole region. Joint-anchored matches are accepted up to 0.25 median (power fists 163-165 and Veteran Squad 143 sit at 0.21-0.23 because their mini pads differ slightly; pauldron renders confirm they sit right). Result: all 90 AM-V2 arms and power fists get a Pad anchor (`test/v17/t_pads_all.py`, ~5 s each the first time, cached after); VS arms 142-146 both sides 0.09-0.23. `t_full.py` builds four complete marines (arms down / forward / power fists / arm 3 raised) with weapons, jump packs, fins, pauldrons both sides and shin pads both legs: all checks pass. Delivered tiow_inbox.py 1.8.1 + README (md5 checked).
>
> **TIOW Inbox 1.9 — Veteran Squad and Bladeguard (Oct 19–20):** both kits share the Assault Marine kit frame. Chests: AM torso sockets. Arms / power fists / Bladeguard sword arms 159-160 / Vet gun arms: joint on the shoulder's inner face (x 5.568, Josh's Bladeguard value). Melee, pistols, Vet one-handed guns, Bladeguard shields: hand rule. Two-handed guns, heavy weapons, two-handed melee: kit position on Shoulder R (spans Shoulder L). New joints: Heavy Weapon Cables → Cable (S_CABLE = translate(7, 1, 22) on each heavy weapon, cables in kit position) and Backpack Toppers → Back Top (Josh's topper socket from Vet backpack 1). Helmets: one Neck fit per folder (AM 1-Helmet-1 matched onto the kit's helmet 1, 0.046/0.047). Vet shin pads from the Techmarine rig pads; Vet pauldrons from the 62-on-76 example. 486 sidecars merged into D:\new cults.
> - **Legs: seated (Josh, Oct 20: "the orange/seated version on the vets looks far better").** Each Vet / Bladeguard legs piece gets the closest of Josh's AM-V2 legs' waists (plug + plating within 6.5 mm of the waist joint) matched onto it (ICP median 0.06–0.10) and that legs' torso placement and Hip R/L carried over; each mirrored legs piece takes the exact mirror of its original's seat (mirror fit 0.04). Josh's own AM seats sit 11–19° from Mar Fil's export position, the Vet seats 4–27°. 28 legs sidecars re-merged (md5 checked). `/home/claude/kits/vet/legs_seat.py`, `legs_match.py`; test `test/v19/t_vet.py` (6 marines, 134 checks).
>
> **TIOW Inbox 1.10 — Intercessors V2 (Oct 20), `D:\new cults\Intercessors-V2\…\RawSTL`, 416 files, 410 sidecars:**
> - The chests are the AM torso at every joint (AM torso regions at Waist / Shoulder R / Neck / Back lie on the Intercessor chest at identity, 0.02 mm), so the AM torso sockets, and the same placing rules: legs seated like Josh's AM legs (ICP 0.08–0.19; mirrored legs = mirror of the original, 0.04); arms by the inner face; Bolter-Dual and two-handed heavy weapons in kit position; cables/belts on Cable; helmets/heads one Neck fit (AM helmet on Intercessor helmet 1: 0.016); backpacks kit position; rocks = Bases at identity on the legs' Base socket (legs that stand on them are exported on them).
> - **Hands are separate.** New joints: **Hands** → Hand (sided) and **Hand-less Weapons** → Grip (sided). Hands 273–281: the hand rule gives one wrist for all of them (cap at (−1.13, 2.77, 1.20), axes = file axes, left = mirror); saved as their Hand fit, plus a Grip socket at that wrist. Mar Fil's melee-with-hand and pistol-with-hand pieces share that wrist (their hands lie on the kit hands at 0.13–0.19 in place) → same fit. The -NoHand melee and pistols are in the hands' file frame → Grip fit = inverse wrist; the -NoHand bolters are the held bolters' bolter turned 90° about Z (ICP 0.025) → Grip fit through the held bolters' wrist. Weapons go in either hand unmirrored (Mar Fil's left-hand pieces hold the same unmirrored weapon).
> - Held bolters (Bolter-Individual 144–178 R/L): their own hand at the stock end; one family wrist from the rule on 144/158/165 (0.07; 151/172 alone pick a roll 150° off at 0.11, so the family value is used). Hand 10 (282, hand holding a shield): Shields by the rule (0.067).
> - **Arm pieces with a weapon** (Bolter-Individual 125–143 R/L, heavy arms 188/189/191/193/201/203/205 R, 189-L/201-L/202/204 L) are exported 2–5 mm off the shoulder and turned 6–25°. Matching the plain arm's shoulder region by ICP fails (the mini pad turns with the arm's swing, 0.2 median). Rule instead: the **shoulder disc** — the round flat inner face (area 12–18, r 2.2–2.7, rim spread < 0.15; plain arms: centre on the joint, normal (−1, 0, −0.04)) — centre on the joint, face turned flat onto the chest by the smallest turn; per pose family (spread ≤ 0.12 except 126 → family median). They are exported in right/left pairs as one turned unit (125-130 R + L, 131-136, 137-143, 188/189 + 189-L, 201 + 201-L, 203 + 204: torso turned ~9–25° and shifted), so each pair gets one rigid placement (weighted Kabsch on both discs, the single-disc swing as a weak guide): both discs within 0.09 mm / 1.3° of their joints, swing within 1.5° of the single-disc answer (two discs on one axis leave the swing about that axis free). Right heavy arms carry a Cable socket.
> - Not placed: Desolator 213–218 (SuperFrag/Superkrak/Vengor launcher bits).
> - Add-on 1.10: the two joints; `choose_socket` tries the selected part's own sockets before the rest of the model (a hand-less weapon goes in the selected hand; an unsided pad on the selected arm); `find_shin_points` looks for ankle balls within 11 mm of the holes only (legs 33/36/39 found no balls because other round bits filled the 12 vote slots; AM/Vet legs unchanged, ≤ 0.003 mm).
> - Shin pads: same pads as the Techmarine rig's Intercessor pads (0.03–0.05) → Shin R/L per file. Pauldrons 49–56: Pad R from 62-on-76 (0.10–0.15), left by mirrorLeft.
> - Tests: `test/v110/t_iv2.py` (9 marines, 111 checks), `t_iv2_pairs.py` (the 7 arm pairs, 67 checks); on 1.10 the older suites pass too (t_marine 47, t_full, t_wrist — now starts from fresh Vet sidecars instead of none —, t_vet). Delivered (md5 checked on the device): `Desktop\TIOW Blender bridge\` tiow_inbox.py 1.10.0 (08e3ced4…), README.txt (new section "Intercessors V2"), _library.json (+ Hands, Hand-less Weapons joints); example Library `_library.json`; 410 Intercessor sidecars merged into D:\new cults (all new). Scripts: `/home/claude/kits/iv2/` (iv2_build.py, legs_seat.py, disc.py/disc2.py → discs2.json → disc_fits.json (single: disc_fits_single.json), hands.py, bolt_rule.py, boltQ.py, iv2_pads.py).
>
> **Cross-kit compatibility (Oct 20) — requirement from Josh: any kit's part must fit any other kit's body** (an Intercessor V2 shin pad on Assault or Vet legs, any torso on any legs). Audited and tested (`test/v111/t_cross.py`: 3 single-kit marines + 6 mixed ones, AM / Vet / Bladeguard / IV2 / Chaplain parts on each other's bodies; every joint snaps; closest approach 0.00–0.06 mm and deepest cut ≤ 0.65 mm, the same as within a kit). The shared conventions every new kit must follow:
> - **Chests:** the AM torso sockets exactly (all 20 chests checked: identical).
> - **Legs → Waist:** seated like Josh's AM legs (AM waist region matched onto the new legs, Josh's placement carried).
> - **Arms → Shoulder:** the shoulder disc centre on the socket origin, face flat on the chest (all AM fits: ≤ 0.3 mm; Vet, IV2 and Chaplain the same; Bladeguard 159/160 SwordHandled are posed 0.8 mm / 16° off by Mar Fil).
> - **Hands:** wrist rule on arms, hand rule on hand-held parts. Josh's own AM wrist sockets and weapon fits agree with the rules to ≤ 0.4–0.5 mm; their roll about the wrist differs by a few degrees (8 of 60 AM arms 5–29°), so a weapon moved between kits can need its roll touched up.
> - **Heads → Neck:** Josh's AM helmet seat (its neck ring matched onto the new head). Mar Fil's own export position is 4.5° off it (the Chaplain head was on that and was moved).
> - **Packs → Back:** Mar Fil's export position = Josh's AM jump-pack fits exactly.
> - **Pads:** Shin anchors by the shin rule on every legs; pads fitted to the rig's shin frame / the 62-on-76 pauldron example.
> - **Belt anchors (fixed):** the Hip R/L sockets carried over from Josh's AM legs had Z up/down inside the waist, not the clicked-anchor frame (Z out of the surface, Y up) that belt bits are fitted to and settle along — a Chaplain book on Vet legs came in turned and slid ~10 mm. Now every kit's legs get Hip R / Hip L / Belt Front / Belt Back by a rule (`kits/belt.py`: in torso coordinates at the belt line z 22.5, the outermost belt surface to the right / left / front / back; Z = surface normal made level, Y up), applied to all partials by `kits/fix_belts.py` (also called at the end of each build). Anchors saved where a maker put a particular part (`tiow_holds`, the Chaplain's belt bits) stay.
>
> **TIOW Inbox 1.11 — Chaplain with Jump Pack, Outriders, Techmarine (Oct 20):**
> - Add-on: joints Cables (Cable), Servo Arms (Servo Arm), Mechadendrites (Mechadendrite), Bikes (Bike), Bike Parts (list: Bike Front, Front Wing, Front/Rear Wheel, Exhaust R/L, Handle R/L, Bike Guns); `tiow_holds` on an anchor = the part file name(s) ('|' for alternatives) it was saved for: `choose_socket(prefer=)` puts such a free anchor first and `place_on` takes that part there exactly (no rock/settle); belt-type (list) joints use `_side_with_mirrored` ('-Mirrored' tries Hip L first); a sided part goes on the side the user picked (selected socket, or a selected part's single own socket of that joint) when it has a fit for it or the joint mirrors — fixes right-only pads ignoring a selected Shin L/left arm and '(Right)'-folder hand-less weapons refusing a left hand; `arm_wrist_frame` takes the outermost face if round, else a wrist-sized (r 1.6-2.0) round face within 1.5 mm behind it (Chaplain 17's rosary cross) — 254 kit arms: 253 unchanged, 1 newly found; `round_tol` parameter (default 0.12).
> - Chaplain: four poses each exported on a turned torso; P_X from the arm pair's two shoulder discs (Kabsch on centres + normals, residual 0.01 mm). Legs seated Josh-style from inv(P_X) start (3-6° from Mar Fil's). Arms placed by P_X with disc on the joint. Head on the AM-helmet neck seat (export 4.5° off). Jump pack export position + Back Top (exhaust). Belt bits: `tiow_holds` anchors at Mar Fil's spots on each legs (book/grenade Belt Back, badge Belt Front, holster Hip L). Arm 17's wrist needed the rule fix. 30 sidecars.
> - Outriders: legs/arms/bike exported in the bike frame (bike +X forward, symmetric about y = 0; mirrored legs = y-mirror). Arm ↔ legs from the shoulder face orientation under each legs' seat (best 0.3-4° vs next 5-22°), matching the ReadMe. Arms: F = inv(S) @ M_legs @ T(0, -shift, 0) — exactly Mar Fil's assembly relative to the bike (hand on the handlebar); export shifts are pure y (29.16, 18.0, 16.4, 13.4, 8.4, 7.1; the mirror twin's seat residual removed); disc lands 0.2-0.6 mm from the joint. Bike: 19-Body-1 on legs 'Bike' (identity), carries one socket per bike part with `tiow_holds`. Base fit T(-29.6, 0, -14.37) @ Rz(90°). Weapons hand rule (A 0.013-0.024, B ~0.08); NoHand = A frame (0.02) → Grip R inv(W_A), Grip L inv(MX W_A MX). Pauldrons: side from export (+y right: 1-R, DW-1; 22 chapter pads left). Belt bits in local frames (front +y, up +z; holsters up +x; mirrored holsters front -y). 155 sidecars, test 218 checks.
> - Tests on 1.11 (`test/v111/run_all.sh`, fresh test library): t_marine 47, t_full 50, t_wrist 21, t_vet 79, t_iv2 111, t_iv2_pairs 67, t_cj 131, t_or 218, t_tm 108, t_cross 146 (8 mixed marines incl. Outrider/Techmarine) — 978 checks, no failures. Delivered Oct 20, md5 checked on the device: `Desktop\TIOW Blender bridge\` tiow_inbox.py 1.11.0 (bfd67ba5…), README.txt (1c59f7d5…; sections "Every kit fits every kit", Chaplain, Outriders, Techmarine), _library.json (45234a67…, + the five joints), example Library _library.json (ea77b691…); 347 sidecars merged into D:\new cults (227 new: Chaplain 30, Outriders 155, Techmarine 42; 120 legs re-anchored: Assault 42, Vet/Bladeguard 28, IV2 50; 0 clicked anchors to keep). Copy kept in `Desktop\TIOW Blender bridge\sidecars-1.11\`. Scripts: `kits/cj/`, `kits/or/`, `kits/tm/`, `kits/belt.py`, `kits/fix_belts.py`, `kits/neckfit.py`, `kits/deliver/pack111.py`.
> - Techmarine: chest = AM torso (back 2°). Arms exported in four turned-torso sets (18+12/14, 19+16, double arms 20, 22; disc residual 0.08). Bionic wrists: centre by the rule at round_tol 0.2 (rims 15-18 % off), roll from Mar Fil's own hands (hand 38 on 12 → 14/16 by matching the wrist end, 0.016; cog axes on 18/19) — the armour-based roll was 21-103° off. Mar Fil's build file (Techmarine-Build-BlendFile, registered on the kit backpack at 0.022) gives the servo shoulder-ball seat (-9.36, -9.95, 41.39); servo arms (ball r 2.47) translated into it; forge guns match the build (Back Top); mechadendrites as exported. Holsters (shared spot) and pouch: `tiow_holds` anchors on the legs they touch. 42 sidecars, test 108 checks.
>
> **Helmet updates and BackPackUpdate-1 (Oct 20, after 1.11):** Mar Fil's two helmet update sets (10 + 11) exist byte-identical in three places each (All Mar All the time\HelmetsUpdate, Outriders' unzipped Helmets-1/-2, and HelmetsUpdate / HelmetsUpdates-1 at the D:\new cults root); BackPackUpdate-1 (4 backpacks + 9 toppers) in four (Vet, Bladeguard, Outriders' unzipped BackPacks, root). Helmets exported in the old Intercessor frame (+X forward); the AM-helmet neck seat matches all 21 within 0.05° / 0.001 mm (update helmet 1 = AM 1-Helmet-1, match 0.000) → one Neck fit for all. Backpack copies get the Vet sidecars (Vet and Bladeguard identical). 89 sidecars merged (all new); test `test/v111/t_hb.py` 183 checks on AM / IV2 / Outrider / Techmarine / Chaplain chests. Lesson: device_commit_files to an existing staged path can deliver a stale copy — stage every change under a new path and md5-check on the device.
>
> **Other creators — scope (Josh, Oct 20):** everything must cross-fit every kit.
> - **Marta** (`D:\new cults\Marta`, 18 Oct archive is the newest): legs, chin pads, weapons, bases, shields, accessories, pauldrons. No torsos or heads (so the GURLS kits are the same as the boys'). Weapons: hand-held only, unless two-armed. Marta legs are flat-topped → body adaptor on Mar Fil torsos.
> - **Springles:** arms and weapons, the hand or two-armed versions (not one-armed unless needed). Heresy scale (Josh scaled them up in his blend).
> - **Turtle Ninja:** everything; one pose per torso (the flat one). Skip the Mk6 "Kitbash Files (Rigging Required)" folders.
> - **Body adaptor** (`D:\new cults\body adaptor`, 6 models): comes across automatically when flat legs go on a Mar Fil torso; adaptor 3 is the default, any of the 6 selectable.
>
> **TIOW Inbox 1.12 — Turtle Ninja + body adaptor (Oct 20):**
> - **Waist kinds:** "Waist" (Mar Fil plug + stomach plating on the legs) and "Flat Waist" (Turtle Ninja / Marta flat-topped legs). Joint options: `byFit` (legs go on whichever socket they have a fit for), `exclusive` (alternative sockets: legs on one replace legs on the other), `adaptor: {"Flat Waist": "Waist"}` (no Flat Waist on the model → `bring_adaptor` puts the default adaptor on Waist and the legs stand on its Flat Waist). New joints Adapters → Waist, Two-Handed Held → Hand R. Prefs: Body Adaptors folder + default number (3); panel row + **Next Adaptor** (swaps to the next, legs stay on). Mar Fil legs replace adaptor + flat legs.
> - **Adaptor frame:** the top of all six adaptors is a copy of the Mar Fil legs' waist (ICP 0.1 mm) → Waist fit = Josh's AM legs seat; flat ring (y 4.544) → Flat Waist socket.
> - **TN torso:** a flat bottom; Flat Waist = bottom face; Waist (for Mar Fil legs) = bottom placed on the Mar Fil front belt top (z 24.8): Bottom @ inv(KB) @ S_Waist, KB = frame((0, 0.571, 24.8), Z, Y). Sidecar `upright` (new key, applied on import) stands the Y-up TN file in the Mar Fil frame. Front −X, or +Z for Mk10 and Mk7/8 jump-pack torsos (found from the back face). Flat pose = the one whose shoulder discs are axis-aligned (score ≈ 0.2 vs ≥ 10): 54 designs.
> - **TN torso sockets:** shoulders and back = the disc / back face frame @ Q, Q = the AM torso's socket in its own face frame. **Neck rule D** (Josh, after A/B were wrong per mark: "B is almost correct but the depth is wrong depending on the armour mark"; D "fine to go with for now"): Neck = shoulder_frame(S_R, S_L) @ NECK_IN_SH, the AM neck relative to the AM shoulder joints (0.79 above the shoulder line, 21.6° forward tilt).
> - **Sidecars on D:\new cults\Turtle Ninja:** legs 465 (Flat Waist from the merged top face, belt anchors 1 mm below, Base under the feet, no shin anchors), torsos 54, adaptors 6, arms 143 + Mk4 lightning arms 2 + Mk10 power fists 12 (disc on the joint as Mar Fil; arms Y-up with ±X discs, front −Z), helmets 197 (neck ball r 2.44 / 2.1 in the torso's neck cup on a same-mark reference torso, else via rule D), hands 48 (hand rule), packs 53 + the five Mk10 Hellblaster packs in Intercessors V2 BackPacks-Raw (mount plate on Back), accessories / seals / grenades 75 (lying on their backs: −Z back, +Y up → belt anchors, rock + settle), bolter poses (Mk4 Tactical A–D, Mk6 Addon A–C): right arm gets Hand R at its lettered wrist, the held bolter is Two-Handed Held and meets the left arm; merged bolter + arms = Two-Handed Guns on Shoulder R. Merged with `merge_sidecars.py` (copy in `Desktop\TIOW Blender bridge\sidecars-1.12\`).
> - **Tests (fresh test library, `test/v112`):** t_flat 31 checks (adaptor 3, Next Adaptor, Mar Fil legs replace, TN torso both waists, Mar Fil arms / helmet / pack on a TN torso, belt line); full regression on 1.12: t_marine 47, t_full 50, t_wrist 21, t_vet 79, t_iv2 111, t_iv2_pairs 67, t_cj 131, t_or 218, t_tm 108, t_cross 146, t_flat 31 — no failures.
> - **Delivered Oct 20, md5 checked on the device:** `Desktop\TIOW Blender bridge\` tiow_inbox.py 1.12.0 (a06492c2…), README.txt (45c82807…, section "Turtle Ninja and the body adaptor"), _library.json (dbef6345…, Legs byFit/exclusive/adaptor, Adapters, Two-Handed Held). 1.11 copies kept in `old-1.11\`. A library with its own _library.json needs those three joints copied in (its "joints" replace the built-in table; D:\new cults has none).
> - **Open:** TN pauldrons (arm dome r ≈ 2.75 about 1.3–2.2 mm out from the disc, pad inner sphere r ≈ 3.8; need Josh's reference placement and whether they must cross onto Mar Fil arms), terrain / bases, pack toppers (banner, vox, Mk6 Powerpack 1), Mk4 lightning claws (no flats), Mk6 Arm Singles claws / shields, the one-off kits (Legion Moritat, Librarian, Primus Medicae, WGBL, Mk4 Tactical bodies), Mk10 power fist swing check. Then Marta, then Springles. Still unanswered: Desolator 213–218 mounting. Scripts: `kits/cr/` (conv.py, flatface.py, ad_match.py, make_crlib.py, dev/ device scripts), `kits/tn/`.
>
> **TIOW Inbox 1.12.1 / 1.12.2 — Turtle Ninja extras, one-off kits, Marta (Oct 20, Josh: "carry on for now"):**
> - **Add-on 1.12.1:** a sided part with no side in its name goes on the side it has a fit for (Mk7 power fists are left-only, TN arm singles right-only); a hand-held part with a fit for one hand only takes that hand (before the fist rule). **1.12.2:** belt-list joints (Accessories etc.) restrict to the anchors the part has a fit for, unless a socket is selected (Marta loincloths → Belt Front, not the first free hip). Delivered (md5 checked): 1.12.1 (e1c47b35…), then 1.12.2 (4793843d…, README b3ce4b28…). Regression on 1.12.2: 14 suites, 1,104 checks, no failures (new: t_tn2 26, t_oneoff 60, t_marta 8).
> - **TN pack toppers:** Back Top on all 17 TN powerpacks (not Hellblaster) = top-centre of the flat-lying pack (column at the bbox x-centre, highest band, Z = pack up +Y, Y forward); toppers' pole tip 1.1 mm into the pack top, pole up, decorated face (+Z) forward. Validated: the Mk4 vox caster, exported in place on the Mk4 pack, is reproduced by the rule to 0.13 mm / 0.006°. Mar Fil toppers on TN packs and TN toppers on Mar Fil packs both work (same Back Top convention: pack top surface, Z up, Y forward). `Powerpack 1` (Mk6 pack + vox, standing, 0.92 scale) gets Back like Mk6 Powerpack 1 with plate centres together.
> - **Mk7 power fists (6):** whole arms lying along X; shoulder disc = the ~13 mm² flat at the +X end; left arms (all six are the same arm re-posed, not mirror pairs; B_11/B_21 only bring the fist forward as lefts; shoulder-region match favours L by 15–25 %); swing = upper arm as near straight down as the disc allows.
> - **Mk4 lightning claws:** an overlay for the open hand of `Mk4_Lightning_Powerfist_A` (merged claw arm = that arm + claws, matches 0.05 mm). The arm gets a Hand R socket at the claw's cuff end (claw PCA axis), the claws a Hand R fit reproducing the merged arm exactly.
> - **Jump-pack terrain:** exported in the Mk10 jump legs' frame. Each of the 90 jump legs gets a second Base anchor (`tiow_holds` the three terrain files) at the usual Base spot (7.95, 0, 12.55); terrain Base fit = inv(that), so it lands as exported; round bases still take the normal Base.
> - **One-off kits in one assembly frame:** Librarian (torso = `Full_Model_Decimated`, sockets by the flat torso rule; legs Flat Waist / arms / heads / pack / base by assembly; hands on wrist-rule Hand sockets; pauldron and belt bits on held anchors) and Legion Moritat (`LM_Body` = torso + legs: shoulder sockets from the arms' disc rule, Back from the pack plate, Neck by rule D, a virtual waist from the shoulders for belt anchors and upright; plasma pistols at the wrists 0.04 mm; volkite pistols by matching the plasma's hand, 0.07–0.08). Every part lands as assembled (test `t_oneoff.py`, 56 checks incl. Mar Fil arm/helmet and TN legs on the kit bodies). **Mk4 Tactical bodies (10):** torso + legs in one; shoulder discs / back face by the flat torso rule restricted to the torso region, Neck rule D, Base, belt anchors, upright. **Primus Medicae, WGBL:** parts not in one frame → parked.
> - **Springles (done in 1.13, below):** 882 files. Josh's working file has 74 Springles heresy arms scaled by **1.1002** (mesh-applied; same tri counts as the Springles files) and placed relative to the torso's HeresyArms_r socket; files are scattered on print plates. Plan: sidecar `scale` key in the add-on, arm fits from Josh's placements, weapons in their with-hands versions.
> - **Marta (D:\new cults\Marta, 2305 unique raw files):** survey by folder/name; presupported skipped; torsos/heads skipped (Josh). Marta frame: Y up, front +Z (checked visually on 10 legs across releases; a toe heuristic disagreed and was wrong).
>   - Legs 220: flat-legs rule (top face, belt anchors, Base). Bases 42: bottom = largest flat, origin = disc centre on the rim top (histogram mode of rim heights). Two-armed sets 32: pair of opposite ±X shoulder faces 12.2–13.1 mm apart; right face (on −X, facing +X) by the TN/Mar Fil shoulder rule on Shoulder R; left follows (on Mar Fil torsos ~1.4 mm in). Loincloths 21: Belt Front fit (top edge centre at the back, face +Z), rock + settle.
>   - **Chin pads: Mar Fil legs only for now** (Josh, Oct 20: Marta legs that take different shin pads don't cover her full range; revisit later). 49 more chin pads fitted to the Techmarine rig pad; 31 accepted (median ≤ 0.40; most newer ones are left-only files → left shin only), 18 thicc/heavy rejected (0.45–0.76: made for her bigger legs).
>   - Pauldrons: 102 fitted, 62 matched onto each (both chiralities tried; nearly all symmetric, so Pad R + mirrorLeft); 86 accepted (median ≤ 0.30, contact sheets checked), 16 left for Save Fit for Folder (thicc, Mithraism, Pagan feathered, SW pelt). Shoulder shields, accessories other than loincloths, shields and weapons: waiting on Josh (Marta sells arm / hand / weapon separately).
>   - Device: scipy installed for the user (`pip --user`) so ICP can run there too.
>
> **TIOW Inbox 1.13 — Springles (Oct 20).** Josh's choices: guns = two-hand and off-trigger versions only (pistols / axes their with-hand versions); heavy weapons + their backpacks now, ammo belts later; the "mk6 uparmoured cybernetics" folder is legs (one bionic leg) → skipped.
> - **Scale:** Josh's 74 heresy arms in `3rd attempt finalising actual.blend` are the Springles files scaled (vertex order identical: C ×1.10022, P/S ×1.10001). New sidecar key `scale` (mesh scaled on import, sockets/fits in scaled coordinates); C 1.1002, everything else 1.1.
> - **Arms (144, C/P/S, R and L):** Josh's origins = the shoulder disc's flat-patch centroid, file axes, on HeresyArms_r (0.75 mm / 1.6° from Shoulder R). Rule: R fit = inv(S_R) @ S_H @ T(−c); L = inv(S_L) @ MX @ S_H @ MY @ T(−c) (discs face file −Y on rights, +Y on lefts; L arms aren't mirrors of R). Matches Josh to ≤0.05 mm on 58 arms; 16 of his origins sit 0.2–1.2 mm off the disc; his P/S arms are turned 90° (disc facing forward) — the rule fixes both. Helmet-hold arms are left arms (Josh mirrored the C one; L rule reproduces his mirrored placement exactly). New sidecar key `noPad` (no Pad anchor) — but Josh (Oct 20, 21:28): the Springles arms have no pauldron, they need one → see Pauldrons below (`noPad` now false on all). `arm+hand` added to HANDLESS.
> - **Wrists:** arms end in a cup (lip ring r 1.69, recess 0.55 deep, flat floor); Hand R/L socket = lip centre, Y up the forearm, Z = torso (up+forward) ⊥ Y. Found on 119 arms by the lip-ring search; 22 pattern P cups carried from the same pose in pattern C by ICP of the forearm end (C/P/S forearms are the same mesh; C and S cups coincide to 0.01 mm). Hands end in a dome (sphere R 2.42 file units); the dome tip sits on the cup floor: Hand R fit origin = tip − 0.55·axis, Y = wrist axis, Z = file +Z ⊥ Y.
> - **Weapons (109):** hands found by differencing each file against its "no hands" version, domes by sphere votes (R fixed 2.42). Springles uses the same hand poses throughout: guns have the grip wrist along −X and the support hand 10.9/3.9/0.9 mm from it; hip-held heavies the trigger hand at (−0.48,−0.74,0.46) with the other 12.6 mm away; shoulder-type heavies (las cannon, plasma cannon, rocket launcher) their own pair; tabar poses: lower hand = right. Which hand is the right one was checked against Springles' arm pairs. Categories: Two-Handed Held 83, Pistols 14, Melee 12. Skipped (no hands): banestrike bolt cannon, umbra bolter slung.
> - **Two hands on ball wrists (add-on):** sidecar `offHand` (other wrist frame) + `pivot` (grip dome tip). After snapping to Hand R the gun turns about the dome tip so the other hand reaches the model's Hand L (Wahba on the off-hand direction + both forearm axes), only if it gets within 3 mm. Ranged pairs: 1.5–2.2 mm; heavy pairs 1–3: ~1.1–1.5 mm; las/plasma cannon/rocket launcher on ranged arms 0.5–1 mm after ~125°.
> - **Pauldrons (Oct 20, after Josh: "they don't have a pauldron on them"):** every arm has a Pad R/L anchor in its sidecar (`noPad` false). First try (62-on-76 anchor on the hanging slung arm) was replaced by **Josh's hand placement** (Oct 20, 22:59): `62-ShoulderPad-1` placed on `patternC heavy Rarm 4` in `3rd attempt finalising actual.blend` (raw 62 mesh; pad sits on the shoulder armour, 0.8 % of its points ≤0.17 mm in). His pad follows the raised arm (91° from the torso-fixed 76 pose, 21° / 1.8 mm from the first try). Reference = his anchor (pad @ inv(62 Pad R fit), relative to the arm) brought to the slung-arm frame by the h4 shoulder rotation; every arm = reference turned by its shoulder rotation about the disc centre (1-DOF swing search, 3-DOF ICP, global search when >0.15; all 144 ≤0.20 mm median vs the slung arm), pushed out only if >3 % of the pad would be >0.15 mm inside (one arm moved 0.27 mm: P sarge Larm). h4 reproduces Josh's pad to 1e-5 mm/°. Lefts on the mirror image. Delivered (sidecars only; add-on unchanged 84ffde37…): `sidecars-1.13\sidecars_springles_arms_pads_josh.tgz` (df28ce88…), README (fd712ab3…); 144 merged. t_spr 29 checks. Scripts: `kits/spr/josh_pad.py`, `josh_ref.py`, `capmatch.py`, `swing_all.py` (cached rotations `w/swing_*.json`), `build_pads.py w/josh_ref.json`. Big files: Josh prefers to be asked to save a smaller .blend rather than having a 1.5 GB file split and copied.
> - **Packs (12):** hw backpacks + assault cannon ammo pack: the mount plate (50 mm²) on Back, plate centres together (TN pack rule, Z-up files).
> - **Delivered Oct 20 (md5 checked on the device):** `Desktop\TIOW Blender bridge\` tiow_inbox.py 1.13.0 (84ffde37…), README.txt (331d6db1…, section "Springles"); 1.12.2 copies in `old-1.12\`; 265 sidecars merged into D:\new cults\Springles (all new; copy `sidecars-1.13\sidecars_springles.tgz`, d7abbf2f…). Regression on 1.13: 15 suites, 1,129 checks, no failures.
> - Tests: `test/v113/t_spr.py` (26 checks) (Springles on AM / TN torsos, Mar Fil weapons in Springles cups and the reverse, two-hand turn, packs). Scripts: `kits/spr/` (spr_g.py, spr_arms.py, cuprule.py, cup_transfer.py, build_arms.py, domes.py, hands.py, classify.py, build_weapons.py, packs.py, qa_weapons.py).
> - **Open:** ammo belts (Josh, 20 Oct: later; they are cut ends with no connector, so a reference placement or a choice of which end they follow is needed), the backpack camera, the 1-hand / no-hands / plastic versions, the mk6 uparmoured legs. Still waiting from before: Marta Q2 (weapons with hands), TN pauldron reference, Primus Medicae / WGBL, Desolator 213–218.
>
> **Kitbash Library (Oct 21):** `D:\Kitbash Library` is the new master (Josh: "anything going forward should work from there"), built from the set-up parts in D:\new cults: `<Creator> - <Mark>\<Kit>\[groups]\<Type>\[Left|Right|Mirrored]\file.stl` + sidecar, `Bits\<Type>`; 3312 parts, 22.75 GB, verified. Josh connected it in TIOW. Josh's first real test showed no anchors/sockets: Blender was still running TIOW Inbox 1.6.1, not 1.13 (fix: reinstall). Josh: don't make sidecars readable by old add-ons. `build_library.py` overwrites a library sidecar that differs from new cults' copy, so adding makers is done with `--only` plans (below), never a full re-run.
>
> **TIOW Inbox 1.14 — BBoosty + CyberBrush (Oct 21).** Josh: BBoosty = everything but posed bodies and posed weapons (two-handed weapons allowed); CyberBrush = everything. Both export in model axes (front −Y), only moved for printing → Mar Fil frame by RZ180.
> - **Arms:** round flat shoulder face (normal ±X) on the heresy shoulder point S_H, as Springles: R W = S_H·RZm90·T(−cc)·A, L mirrored. Turned prints take a sibling's pose: rotating ICP of the sibling's upper arm (fists 0.08–0.21, spear 1/4 ~0.2), or — better — **moved-only**: CB Chainsword 2/4, Sword 4 share a second round face (r 2.15, same normal) with Axe/Hammer/Sword 2/4 → translation-only match 0.004–0.006 mm (rotating ICP had given 0.26–0.33 and no shoulder dome); Guns 3 = 3 (Bayonet) moved (0.020). Wrist sockets (BB bare arms) like Springles' cups. Pad R/L anchor on every arm's shoulder dome (107 arms), none on BB "…Shoulder…" arms (pad built in). New sidecar key **`noHand`** (all CB arms, BB shield-grip left arms): no wrist rule, no status-line complaint.
> - **Hands/with-hand weapons** (BB): wrist ball in the wrist socket, both hands. **Paragon two-handed blades:** upper hand on Hand R, `offHand` + `pivot` as Springles. One-hand Praetor swords Melee; sergeant shield-with-hand Shields.
> - **Pauldrons:** inner shell on the arm's dome where Josh's 62 sits on the heresy arm, turned square so it opens inward/down (BB 20, CB 10). Fixed after renders: Consul ShoulderPad_Studs (printed at an angle) = placed exactly as Consul ShoulderPad (ICP 0.02 on closest 30 %); IH ALTBlank/ALTSign/Dots turned like IH Sign/Blank (0.11). CB set 1 (2)/(4)/(5) are **left pads** (open toward model −X): own Pad L fit (rule on the mirror image), and add-on 1.14 mirrors a left-only pad onto a right arm.
> - **Heads** neck ball in the neck cup; **packs** BB as Josh's Backpack2 (MM variants by front plate), CB centred on the back plate; **CB torso** (Chests) with Shoulder/Neck/Back/Waist/Flat Waist moved from Mar Fil's by feature differences; CB two-armed guns / 2H sword / 2H axe on Shoulder R spanning L; BB bases by the round-base rule.
> - **Forearm armour** (new type `Forearm Armour`, joint Forearm sided + mirrorLeft): CB Space Bug Hunter forearms (tyranid carapace plates). Josh placed Forearm 3 on 77-Arm-1-R-B (`Wrist Right arm` socket in `example issues.blend`); fit = relative to 77's Forearm R (his Wrist_Armout_r). Forearms 1/2 are exported like 3, only moved (inner-face translation match 0.08 / 0.23). On Mar Fil AM arms Forearm R/L = Hand @ a constant step (spread 0°, ±0.1 mm) → add-on 1.14 gives any arm with a Hand socket a Forearm socket when forearm armour arrives (`ensure_forearm_sockets`). CB weapon arms have no wrist → no Forearm socket yet.
> - **Not placed (type-only sidecars, park or land at cursor):** BB separated weapons 25 + plain 2H power swords (Hand-less Weapons), shields without hand, holsters/pouch (Accessories), grenades/melta bomb, servo arms + modules + Iron Father claw/flamer/melta (Servo Arms), backpack cams (Backpack Toppers), base topper; CB equipment 1–7 / belt decorations / loincloths (Accessories), cloaks (new type `Cloaks`, no joint), shields without arm, Free weapons + 2H (5) + loose Gun / Gun (Bayonet) (Hand-less Weapons). Asked Josh for reference placements.
> - **Add-on 1.14.0:** Forearm Armour joint + forearm socket rule; `noHand`; left-only pads mirrored onto the right. `_library.json` joints now regenerated from DEFAULT_JOINTS (31 joints) and partTypes + Forearm Armour, Cloaks (34 types). Library tooling: `plan_library.py --work --survey --only`, `build_library.py --work` (keeps other `_sources.csv` rows), `survey_new.py`; BB → `BBoosty - Heresy`, CB → `CyberBrush - Tacticus` (220 planned after 5 identical Chaplain/Consul copies; longest path 161).
> - **Tests:** `test/v114/t_nc.py` 87 checks (15 marines: BB/CB on Mar Fil, TN and CB torsos, forearms, weak-match arms), `t_pads.py` 36 (every pad family both sides), `t_josh.py` 6; full regression on 1.14 (17 suites) 1,225 checks, no failures.
> - **Bundle:** `/home/claude/outbox5` (tiow_inbox.py 1f7a579d…, 321 sidecars BB 169 / CB 152, INSTALL-1.14.txt). **Delivered Oct 21 (md5 checked on the device):** bridge folder tiow_inbox.py 1.14.0 (1f7a579d…), README (79d08162…), _library.json (54530eda…), apply-blender-bridge.mjs (c073c916…; TIOW re-patched v4 with Forearm Armour / Cloaks), 1.13 copies in `old-1.13\`; Blender `scripts\addons\tiow_inbox.py` replaced (it was still 1.6.1; old copy in `old-installed-1.6.1\`) with Josh's go-ahead; 321 sidecars merged into D:\new cults (all new, byte-identical); D:\Kitbash Library + 316 parts (BBoosty - Heresy 164, CyberBrush - Tacticus 152), verify 0 bad, `_sources.csv` 3628 rows. Left without sidecars on purpose: posed bodies (Chaplain/Consul/Iron Father/Praetor bodies), PosedWeapon 70, Poses 33, Supported copies. Scripts: `kits/nc/` (build_bb*.py, build_cb_*.py, fix_cb_turned.py, fix_cb_via.py, build_cb_forearms.py, build_unplaced.py, merge_all.py).
>
> **Kitbash Finalise 0.1 — new add-on, first draft (Oct 21).** Josh: finalise a socketed model by booleaning it together (Hard Ops' setup, no HOps UI, solver Manifold; non-manifold parts listed with an option to use Exact for those), a preset joint order, optional sub-assemblies chosen per build, a peg at each split (first asked bayonet, then "the more basic version… the long version rather than the disk version": Part Sockets' push-fit spike in Long proportions; peg on the piece, cavity in the body) and the same ID letter on both mating faces beside the peg. File `Desktop\Kitbash Finalise\kitbash_finalise.py` (+ README), copied to Blender `scripts\addons` (Josh ticks it); source `/home/claude/finalise/`.
> - Flow: Finalise Model (dialog: non-manifold list + Use Exact, sub-assemblies + piece checklist, carve overlaps, letters) → draft collection "Finalise - <model>" (parts copied with modifiers applied, originals hidden; booleans built through HOps' `operators/booleans/operator.add()` with its `boolean_solver` / `workflow` prefs set temporarily to MANIFOLD / NONDESTRUCTIVE and restored; falls back to plain Boolean modifiers if HOps is off or fails) with booleans switched off in the viewport (a 15-boolean body costs ~5 GB and seconds per redraw live) → Preview Booleans per piece → Apply Booleans (one modifier at a time; ~18 s for the marine) → manifold report; Discard restores.
> - Exact only for booleans involving a listed part, placed last on that piece (Exact output can be non-manifold, which later Manifold booleans can't take). Peg/cavity/letters hang from one arrow empty per joint (FA_joint_<letter>) for re-aiming.
> - Peg axis = pull-off direction: area-sampled body points within 0.3 mm of the piece, best direction on a sphere for the 10th percentile of n·d (+0.25 mean), refined; site = piece faces facing the body within 7 mm of the socket, cast onto the body (gap ≤ 3 mm), body depth under the axis and round the cavity rim ≥ L + bottom gap + 0.3, nearest the socket; among near-best sites the first leaving room for a letter. Letters beside the peg where both faces are flat and within 2.5 mm (shrinking to 0.6 mm), else peg tip / cavity floor. Carve: the piece's parts whose surfaces intersect the body are differenced from it.
> - Test on Josh's `claude tests.blend` marine (pistol removed: 12 open edges → Exact path tested on small meshes, `test/t_exact.py` 10 checks): 6 pieces, all manifold; shoulders get letters beside the peg (0.6 mm), waist/neck/pack on the peg tip; warnings: waist peg bridges 1.4 mm and the torso is 2.4 mm deep there (needs 2.8), pack 2.4. HOps path checked with HOps 26.1.4's real `add()` and stand-in prefs (`test/t_hops.py`).
>
> **Kitbash Finalise 0.2 (Oct 21) — pegs centred, one letter per model.** Josh on 0.1's renders: "the arms are fine however the torso pieces are all off to the side. This should essentially be consistently in the middle of a face so that the connection is easy… the adaptor connection points to the torso … would be impossible to put on"; letters: "only one letter on the torso … relatively large on the base as it's flat. On the arm … the full space of the flat that's connecting in … the head … the whole base of the neck. Legs … the whole top"; confirmed "the same letter per model … all of these parts belong to this model".
> - Cause found: the torso (23-Torso-2) is hollow — a dome socket underneath for the legs' post and the neck cup on top, ~1.3 mm of torso between — so 0.1's depth search slid pegs sideways, and the contact-normal axis was ~26° off the legs' post (and 45° off at the neck, where the helmet ball sinks >1.5 mm into the cup), hence "impossible to put on".
> - Placement now: `JointGrid` samples both mating faces on a 0.1 mm grid across the joint (coarse 0.4 first; per cell piece-face / body-face height + facing; footprint = facing each other, gap −3..3 mm). `main_face()` = biggest step-free patch of the piece's face (holes filled). Flat (rms ≤ 0.1 mm, ≥ 3 mm²) → axis = its normal (regridded square to it); curved → the socket's Z if within 30° of the pull-off axis and the socket is on the piece (neck sockets sit on the ball's pole with Z through its centre; a sphere fit was tried and dropped — unstable, false ball on the legs), else pull-off axis. Peg at the face's centroid. `solid_depth` counts crossings. Peg On (scene `fa_peg_side`): AUTO = piece, but flips to peg-on-body / hole-in-piece when the body is > 0.6 mm short of L + bottom gap + 0.3 and the piece is deeper; small shortfalls shorten the peg; PIECE never flips.
> - Letters: one per model (dialog field, default the next letter unused by another build in the file; stored `col["fa_letter"]`; pieces named `<model> - Body [A]`, `<model> - <part> [A]`). Each piece: biggest letter on its main face beside the peg/hole (≥ 0.8 mm), else biggest hidden face elsewhere on the piece, else peg tip / hole floor. Body: one letter, on the face the Waist / Flat Waist piece plugs into if ≥ 1.5 mm, else the biggest body face under any piece. Fit = Chebyshev box over free cells (hidden, facing ≤ 45°, no steps > 0.15 mm, clear of pegs/holes +0.25, thickness ≥ depth + 0.4, margin 0.2) in 15° turns, up to Max Letter Size (default 6 mm); the unit letter is draped over the face (front +0.25 out, back −depth), so curved faces work. Letters parent to their piece's host; only the tip/floor fallbacks follow the joint arrow.
> - Marine result: waist + neck pegs on the torso (into the legs' top / helmet ball), arms + pack peg on the piece; all centred (0.0–0.7 mm from socket). Letters A: legs 2.5, pack 2.8, body 1.6 on the waist dome, arms 1.3 / 1.6 on the pauldron's hidden inner face (the 4.5 mm shoulder disc with a 2 mm peg leaves < 0.8 mm), helmet 0.7 on the ball. All 6 pieces manifold. Tests: `test/t_viz2.py` (sections + face renders), `t_place.py` 15 checks (hollow body: flip, centre, square; thick body: no flip; PIECE forced), `t_exact.py` 13, `t_hops.py` (every boolean through HOps `add()`; the one 0.1-era fallback was the test's stand-in prefs lacking `color.colection_color`).
> - **Delivered Oct 21 (md5 checked on the device):** `Desktop\Kitbash Finalise\0.2\` kitbash_finalise.py (c89e5af6…), README (402ca75a…), finalise_0.2_faces.jpg; Blender `scripts\addons\kitbash_finalise.py` replaced with 0.2 (0.1 still in `Desktop\Kitbash Finalise\`).
>
> **Kitbash Finalise 0.3 (Oct 21) — square keyed pegs, no waist peg, foot-to-base peg.** Josh: "Could we make the peg square? That way the orientation is fixed in blender… I'm also not sure we need a peg in the body to legs. The flat face and adaptors should usually be enough? It's mostly arms heads and back packs"; "make sure there is a peg on the foot to attach to the base".
> - Peg profile SQUARE (new default, `square_peg()`): side = the size's diameter, Part Sockets' taper + nose rings, the +X+Y corner cut by 0.3 × side so it seats one way only (a plain square would still go in 4 ways); hole = same grown by clearance with the 0.18 mouth flare. r_wall (hole walls, depth checked there) vs r_out (flared mouth, letter keep-out) vs r_peg now separate.
> - Dialog: per-piece Peg toggle (FA_Item.peg); default off for prefs `no_peg` = "Waist, Flat Waist"; Base parts default split. No-peg joints still get carve + letters.
> - Base joints (`joint_base == "Base"`; bases hang off the legs' Base socket): main face from the body side (`main_face('body')` = the sole), peg forced onto the body (foot), hole in the base, may go through (no shorten/flip).
> - Size step-down: `joint_place(sizes=[…])` tries the chosen Part Sockets size then smaller LONG presets; first one either side takes within 0.6 mm wins (marine neck: M's square corners break out of the 13 mm² helmet ball → S, peg on the torso).
> - Fixes: (1) **0.2 bug** — a peg on the body was unioned before the carve, which cut it off again (0.2 torso neck/waist pegs missing; 0.2 shouldn't be printed); each piece's booleans now sorted members → carves → pegs → holes → letters (HOps sort keeps it). (2) `pull_direction` scored by mean(n·d) − 8·mean(max(0, −n·d)) instead of the 10th percentile, which ignored small opposing walls (gave a 45° diagonal at a foot; likely the 0.1 waist tilt). (3) letter keep-outs limited to the peg/hole's length along its axis (the foot peg's axis was blocking the legs' top).
> - Marine: legs no peg (letter 5.1 mm on top, body 3.9 mm on the base), arms + pack keyed M pegs on the piece, neck S on the torso; all manifold; every peg checked present after Apply (PEGCHECK). Tests: `t_base.py` 12 (hollow 25 mm base: foot peg in the sole's middle, square, survives, base holed), `t_place.py` 21, `t_exact.py` 13, `t_hops.py` (all through HOps, order kept), `t_viz2.py`.
> - **Delivered Oct 21 (md5 checked):** `Desktop\Kitbash Finalise\0.3\` kitbash_finalise.py (2df81db4…), README (081dcc28…), finalise_0.3_faces.jpg; Blender `scripts\addons\kitbash_finalise.py` = 0.3.
>
> **Bases moved to `D:\Kitbash Library\Bases` (Oct 21).** Josh: "move all bases into a separate folder so they get their own tag in TIOW … a new top level folder. The designer of the base shouldn't really be a concern." All 61 type-Bases parts (round bases, rocks, terrain, BBoosty BaseTopper) + their 61 sidecars moved flat into `Bases\`; 18 clashing names (Windows ignores case) got the kit folder in brackets, the plan script's own rule (`Base (Chaplain).stl`, `base_40mm (48 February 2026).stl`, `Base_40mm (Librarian Custom).stl`…). No folder `_fits.json` in any Bases folder; `tiow_holds` reference stems and none of the renamed ones (jump-leg terrain kept its names). `_sources.csv` updated (61 rows; backup `_sources.before-bases.csv`), log `_bases_moved.csv` (was, now). 34 now-empty Bases folders were left in place at the time; removed Oct 29 with `rmdir` after a delete grant (the 14 parents still hold other parts). `kits/lib/plan_library.py`: type Bases → `Bases/<file>`, clashes renamed `stem (kit)`.
>
> **TIOW Inbox 1.15 (Oct 21) — Stand on Base.** Josh: "is there way to get the base to end up flat? i understand everything hangs off the torso but its so that the pose can be viewed properly? This could even take place at the end once the base is brought in?" Everything hangs off the torso, which keeps its file angle, so legs and base tilt with the waist fit (his test marine: 17.6°). The legs' Base socket Z matches the base's flat underside (0.00° on the BBoosty Chaplain base).
> - `stand_on_base(sock)`: turns the model's root about the Base socket by the smallest rotation taking the socket's Z to world Z (keeps heading), then drops the lowest point of the base(s) on it (or the socket) to z = 0, x/y unchanged (squads stay side by side); parts snapped in without being parented get the same delta. Runs automatically at the end of `auto_snap` when the socket is "Base" (pref `stand_on_base`, default on; status ", model stood flat on it (N deg)"); `tiow.stand_on_base` "Level Now" in the TIOW Inbox panel (`base_socket_of` prefers a Base socket with a base on it). Joints unchanged (all parts identical relative to the torso).
> - Tests: `finalise/test/josh/t_level.py` 10 checks on Josh's marine (button and re-snap). Regression 1,225 checks, no failures — `v112/t_oneoff` now compares in-place kits with the body as it is after levelling (Librarian Custom / Legion Moritat are exported 28.3 mm below the grid and get dropped onto it, 0.0° turn).
> - **Delivered (md5 checked):** bridge folder tiow_inbox.py 1.15.0 (4792c177…), README (9008a74e…, section "Standing on the base"); 1.14 copies in `old-1.14\`; Blender `scripts\addons\tiow_inbox.py` = 1.15.0.
>
> **Kitbash Finalise 0.3.1 (Oct 21) — first run in Josh's Blender.** Josh: "run a test on my machine. Bring in some bits using the bridge try to manifold them and add in pegs". Parts sent through the TIOW inbox (request JSON written with json.dumps — an earlier hand-built request had unescaped Windows backslashes, so the inbox couldn't parse it): AM-V2 24-Torso-3, 31-Legs-4, arms 106-R / 108-L, 12-Head-4, 57-JumpPack-3, BBoosty Chaplain Base (scenic, 231 open edges). Driven by computer use (Blender 5.1 + textinputhost.exe allowed; typing doesn't reach Blender, single key presses do; Josh's Ctrl+S is a pie menu; Kitbash Finalise had to be ticked in Preferences).
> - 0.3 result: 7 pieces, all manifold but the base (input); arm / neck / pack pegs present; **foot peg missing** — the base carve was Exact (non-manifold cutter) and Exact ops ran last, after the peg. Fix: per piece, rank order (members → carves → pegs → holes → letters, Manifold first within a rank) and Exact from the first op that needs it onward. Also: `pull_direction(nrs, toward)` tie-break toward the piece's middle (a foot sunk into a base touches only round its sides → was choosing up); empty HOps "Cutters" collection removed after Apply / Discard. `t_base.py -- --open` (open base, sunk foot) 12 checks.
> - 0.3.1 rerun in Josh's Blender (second instance, file reopened, add-on re-ticked): all pegs + holes present (PEGCHECK on the baked pieces, plan rebuilt from his hidden originals: `test/josh/check.py`), legs 3 booleans Exact, foot peg 2.2 M keyed square in the middle of the 13 mm² sole patch, base hole + letter 1.0 mm. Letters: legs 6.0, body 3.6 on the waist, pack 2.5, arms 1.9 (pauldron inner), head 0.7.
> - **Delivered (md5 checked):** `Desktop\Kitbash Finalise\0.3.1\` kitbash_finalise.py (6e573e32…), README (511c5454…); Blender addons copy = 0.3.1. Test file `Desktop\finalise-test.blend`.
>
> **TIOW Inbox 1.16 (Oct 22) — one file, both sides.** Josh: "do we need the mirrored and l and r? or could we just mirror these in blender?" → agreed plan: inbox mirrors first, then move the copies out, then rename (Maker Kit - Part).
> - Sidecar `"variants": [{side, mirror, align (keep-file coords → copy's), name, folder, from, match, sidecar: the copy's own sockets/fits}]`, plus `duplicate` (same part twice) and `synth` (a plain mirror the Mirror button made, saved so clicked anchors stick). `load_stl(variant=)` moves the mesh by align (flip normals if det<0) and uses the variant's sockets/fits; no folder fits for variants.
> - `pick_variant`: sided parts only, real (non-synth, non-duplicate) variant for the other side; the picked side wins (socket / part on it / the arm whose hand), else the free side, own side first (choose_socket over both sides' names).
> - Mirror operator (`tiow.mirror_part`, TIOW panel): sided socket → re-import the counterpart onto the opposite socket, held parts mirrored onto the image sockets, the occupant swapped back mirrored; central socket (legs, head) → flipped in place, held parts re-seated on same-named sockets, re-levels on the base; loose (torso) → W_new = W_old·MX·K⁻¹. Two-handed (spans) refused.
> - Rules read the maker's names: `tiow_orig`/`tiow_folder` on the part (sidecar `original`, or the variant's), `_part_key` = orig (holds never need rewriting), `_mirror_twin` falls back to sidecar `original` names. Sidecar writers (anchors, rule fits, Save Fit for Folder) write into the variant entry for a variant part.
> - Tests: full regression on 1.16 = 0 fails (t_marine 47, t_full 50, t_wrist 21, t_vet 79, t_iv2 111, t_iv2_pairs 67, t_cj 131, t_or 218, t_tm 108, t_cross 146, t_flat 31, t_tn2 26, t_oneoff 60, t_marta 8); `test/v116/t_variants.py` 32 checks (variant = old copy in shape, place and sockets; Mirror swaps; plain mirror; legs/torso flip) on the folded lib and again on it renamed; replays of t_vet/t_iv2/t_or/t_cross/t_marine against a renamed library: every part lands identically.
> - **Delivered (md5 checked):** tiow_inbox.py e2f19db7… to `Desktop\TIOW Blender bridge\` and Blender addons; README d1ec6075…; 1.15 kept in `old-1.15\`.
>
> **Mirror copies folded in (Oct 22).** First count (372) used order-preserving triangle samples, which also passed re-posed copies; `fold_twins.py` checks the whole surface after alignment (mirror or same, ICP): fold only if median ≤ 0.05 mm and 95% within 0.15 mm. Result: **224 folded** (220 mirrors, 4 same-side duplicates; Mar Fil 220, TN 4), **148 kept** (e.g. Intercessor bolter pistols L vs R: median 0.001 but the hand differs by 0.5 mm; arms 57–61 L vs R; Mar Fil jump legs Mirrored re-posed). Moved to `D:\Kitbash Library - mirror copies\` (same paths), log `_mirror_copies.csv`, `_sources.csv` updated (3,404 rows, backup `_sources.before-mirrors.csv`), twin sidecars backed up in `…mirror copies\_sidecars-before\`. Tools in `Desktop\TIOW Blender bridge\library build\`.
>
> **Library renamed (Oct 23, Josh: "go ahead and run as is").** 3,337 files renamed, 0 skipped; log `D:\Kitbash Library\_renamed.csv` (was, now), index backup `_sources.before-rename.csv`; every sidecar has `original`, all 224 variants have titles. Undo: `rename_library.py "D:\Kitbash Library" --undo _renamed.csv`. Plan as it was: `plan_names.py`: `<Maker> <Kit> - <Part>`, side last; makers MarFil / Marta / TN / BBoosty / CyberBrush / Springles; kit short names in a table (TN builders named by their mark subfolder); Mar Fil catalogue numbers dropped (kept as `#n` only to break a tie), kit words dropped from the front, `Mirrored` → L, 'chin pad' → Shin Pad; ties broken by catalogue number, then nearest folder, then a count. 3,337 renamed, 67 bases/adaptors kept, 0 shared names. Preview artifact "Kitbash Library Names"; `names_plan.csv` on Josh's desktop. `rename_library.py` writes `original` {name, folder, path} into each sidecar (creates one if missing), titles for variants, updates `_sources.csv`, `--undo` from the log.
>
> **Squad Builder + TIOW Inbox 1.17 (Oct 23–25).** Josh: TIOW's navigation is what makes it clunky. He wants:
> - guided selection (torso, then legs, arms…);
> - a whole squad sent in one go ("5 torsos etc");
> - outlines rather than thumbnails, and ghost outlines of parts in the builder.
>
> "Happy for this to be separate". It was built while his computer was out of reach; delivery and a run on the real library wait for it.
>
> **The page** (`Squad Builder.html`, one offline file, three.js r147 inlined):
> - **Steps:** Torso, Legs, Arms R/L, Head, Back, Shoulder pads R/L, Weapons R/L, Shin pads R/L, Base.
> - **Filtering:** each step lists only parts that fit what's already picked, i.e. the model has a socket for them.
> - **Cards** are outline drawings (edges over a dark fill). Hovering a card shows the part in place, as a blue outline, on every model.
> - **Placement:** picks are drawn where Blender will put them, using the inbox's maths:
>   - socket × gap × fit;
>   - mirrored lefts and maker's left copies;
>   - the adaptor for flat legs on a Mar Fil torso (adaptor number is a setting, default 3);
>   - stood on the base.
> - **Squads:** 1–10 models side by side, 80 mm apart. "Same part for every model" is the default; untick it to pick for one model at a time.
> - **Files:** reads the library through the browser's folder access (Chrome/Edge; handles remembered, one click reconnects). Send writes one request JSON per part into TIOW's inbox.
>
> **The index:** `_builder\index.json` plus one ~6,000-triangle preview mesh per part (`KBP1` binary). Made by `Prepare Squad Builder.bat`, which runs `prepare_builder.py` in Blender in the background:
> - It first works out the anchors some parts only get on their first import: wrist sockets, Pad anchors, Shin anchors and hand fits. It saves them in the sidecars, so the page shows those parts exactly where Blender puts them.
> - It resumes from `_builder\anchors_done.txt`. After the first run it only does new or changed parts.
>
> **Inbox 1.17** adds three request fields:
> - `model`: the squad model's id. A part with a `model` goes on that model, whatever is selected in Blender.
> - `socket`: the socket type to land on.
> - `at`: [x, y, z] mm for a model's first part (the torso). That part becomes the model's root (`tiow_model_root`) and is placed at `at`.
>
> **Tests:**
> - `builder/test/drive.js` (Playwright) builds a 3-model squad through the page's own cards.
> - `t_squad.py` sends those requests through 1.17 in Blender and checks every part against where the page drew it. 48 checks, all within 0.05 mm / 0.1°, covering maker's left copies, mirrored pads and shins, the adaptor path and the base stand.
> - Anchor pass over the demo library: 677 parts, 0 failures.
> - Regression on 1.17: 15 suites, 1,135 checks (t_marine 47, t_full 50, t_wrist 21, t_vet 79, t_iv2 111, t_iv2_pairs 67, t_cj 131, t_or 218, t_tm 108, t_cross 146, t_flat 31, t_tn2 26, t_oneoff 60, t_marta 8, t_variants 32), no failures.
>
> **Online demo:** an artifact named "Squad Builder".
> - It holds a 524-part sample: MarFil Assault, Veteran, Jump Chaplain and Helmets; TN Mk10 and Mk6 Assault; Marta; bases; adaptors.
> - Previews are 3,000 triangles. They are packed as base64 text because artifacts can't serve binary files or `_` folders.
> - Send only reports what would go to Blender.
>
> **Delivered Oct 29 (md5 checked on the device):** bridge `tiow_inbox.py` 1.17 (1101094d…) and README (564f750f…), also installed as Blender's `scripts\addons\tiow_inbox.py`; 1.16 kept in `old-1.16\`. `Desktop\TIOW Blender bridge\Squad Builder\`: Squad Builder.html (c8a57738…), Prepare Squad Builder.bat (e672d3a6…), prepare_builder.py (47521b31…), build_index.py (5fd74221…), README.txt (f9e443c2…).
> - **"No fit yet" (Oct 27, Josh asked why some demo cards said Blender would place them):** those parts had no fit for that slot in the demo's sidecars. Cards now say "no fit yet" (tooltip: placed by eye in Blender). `build_index.py` also reads folder `_fits.json` files and writes `_builder\no_fit.txt` listing every part without a fit for its slot. The demo artifact was republished with the Marta fits patched in; Josh shares it himself for feedback.
> - **Prepare on the real library (Oct 29):** started by double-clicking the .bat (computer use, File Explorer at click tier; it opens in Windows Terminal), ~65 min in all. Anchor pass: 2,063 parts and variants, 668 sidecars updated. Index: 3,404 parts, all with previews (366 MB of files, but 3.4 GB on the drive: D: has 1 MB allocation units, so packing previews into a few files would save ~3 GB). `no_fit.txt`: 48 parts — 38 Hand-less Weapons (BBoosty separated weapons etc.), 5 shields (CyberBrush 2A/3, Bladeguard 1C–3C), 4 TN claws/sword, 1 BBoosty backpack, BaseTopper.
> - **Page fix (Oct 29, delivered as `Squad Builder.html` cde6a106…):** a part whose preview can't be read made `meshFor` → `geometry().then(redraw)` loop forever (geometry resolves null on a failed read) and froze the page; now it only redraws when a preview arrived (also for the base and the hover ghost). The search box is cleared when the step changes, and a maker filter with nothing in the new step falls back to all makers (both had left "No parts here match the filters" after picking by search). Found by driving the page over the real index with only the squad's previews staged.
> - **TIOW Inbox 1.17.1 + page (Oct 29, after Josh's first try: Opera GX's folder picker refused TIOW's inbox "because it contains system files").** Chromium's File System Access blocklist covers all of AppData, so the page can never be given `%LOCALAPPDATA%\TIOW-FTRP\local-data\blender-inbox`. Now the page asks for read+write on the Kitbash Library only and writes requests into `<library>\_builder\inbox` (created on connect); the inbox picker is gone. The add-on watches TIOW's inbox and pref `builder_inbox` (default `D:\Kitbash Library\_builder\inbox`, only when its `_builder` exists, empty = off), with a `.listening` heartbeat in each; the page reads that heartbeat every 4 s and shows "Blender listening". Built from 1.17 (not the on-hold 1.18 work, which still needs this change merged in). Tests: `builder/test/t_squad_1171.py` (requests through the builder inbox, 50 checks) and `t_squad_1171_tiow.py` (TIOW inbox, 48), real files. Delivered (md5 checked): bridge `tiow_inbox.py` 1.17.1 (d83f32ec…) + README (9530b22d…), Blender addons copy, `Squad Builder.html` (eaa4f0a5…) + README (c1c08774…); 1.17 kept in `old-1.17\`. Josh restarts Blender to load it.
> - **Squad test on the real library (Oct 29):** the demo plan (3 models: Mar Fil Assault, model 2 with the maker's left arm, model 3 on Marta legs with adaptor 3, pads/shins mirrored, rock bases) driven through the page over the real `index.json` → 39 requests; `t_squad_real.py` with 1.17 on the real files: 48 checks, 0 fails (every part where the page drew it). The same 39 requests written into Josh's inbox: his Blender 5.1 built all three models on their rocks in ~8 s; test models deleted afterwards. Lesson: `computer_open_application` on Blender starts a new instance each time — two extra empty instances had to be closed from the taskbar (each would also listen to the inbox).
> - **Josh's first squads (Oct 29, 18:05–18:35):** "overall pretty incredible". Issues: pauldrons on CyberBrush Bug Hunter arms (wrong in page and Blender; file `Desktop\issues with pauldrons.blend`: Outrider pads over an Intercessor chest sit tight into the chest top — the CB arms' Pad anchor came from the 62-on-76 match on a much bulkier shoulder); with the CyberBrush Light Armour torso the head sits wrong, the torso slightly off and pads hit the torso (mostly fine on a Mar Fil torso); hands slightly off on every torso; bases: some right, some slightly off, some float. Josh wants to adjust once in Blender and have it saved for every combination; keep CB weapon arms as arms for now (his call; not sold on making them weapons).
> - **Page (Oct 29, after Josh):** steps Base → Legs → Torso → arms…; a click picks without moving on, **Next ▸** moves on (Skip removed; Next with nothing picked = skip); a model's legs stand on the base before a torso is picked (legs on the model's spot, base flat on the grid); the hand slot is skipped for an arm with a built-in weapon (anchored arm with no Hand socket). Send order unchanged (torso first). Test `builder/test/t_page_flow.js`.
> - **TIOW Inbox 1.17.2 — bases settle (page and add-on):** after a base snaps onto the legs' Base socket it rises along the socket's Z until the lowest point of the legs touches it, plus `BASE_SINK` 0.2 mm; never lowered (feet already on or in a scenic base stay), capped at 25 mm, skipped for kit-held and corrected placements. Heightfields on a 0.5 mm grid in the socket frame from points spread over the triangles (≤0.25 mm apart): legs' lowest surface (min z, whole legs — a band of 8 mm above the lowest point missed a foot standing on a tall rock: IV2 20-Legs-4 on Rock-16 rose 0.6 mm), base top (max z), gap = min difference over shared cells. Page does the same on the 6,000-triangle previews (cached per legs+base): within ~0.15 mm of Blender's full-mesh result. Examples: IV2 Legs 10 on Textured Base +2.7 mm, Assault 6A on the Chaplain base +1.9, jump Legs 1A on 32_mm_1 +8.8 (toe touches). Scripts: `kits/basefix/` (settle_lib.py, probe.py, probe_prev.py, pairs.jpg).
> - **TIOW Inbox 1.17.2 — Save Correction** (panel box; prefs Whole Folder, Both Sides): **Fix the Part** saves the part's placement as its fit for that socket type in its own sockets file (variant entry for a maker's copy) and marks it `exact` (placed exactly, no rock/settle/base settle); the move E = F_new·F_old⁻¹ (socket frame) is applied to every folder sibling's fit and the folder `_fits.json` with Whole Folder, and MX·E·MX to the other side's fits. **Fix the Socket** keeps the part where it is and moves the host's socket: K_new = P·F⁻¹·T(gap)⁻¹, C = K⁻¹·K_new (socket frame) written into the host's sockets file (L_new), siblings' same socket ·C with Whole Folder, other side ·MX·C·MX. Copies in the scene follow (parts re-placed; sockets moved with their parts). Run Prepare after, to refresh the page. Test `test/v1172/t_correct.py` (sword fit + re-send, folder sibling, Neck socket + head re-send on another model, Pad R socket with the mirrored Pad L).
> - **Tests:** the older test sets passed on 1.17.2 apart from one expectation: Mar Fil exports IV2 20-Legs-4 0.44 mm above Rock-16 (nothing touching), so the rock now rises 0.6 mm (`v110/t_iv2.py` updated to expect it). Josh (Oct 29): don't re-run checks over all parts or all suites any more (usage); after a change, test only a subset of the parts it can affect.
> - **Installed Oct 29, 21:00 (md5 checked); was waiting while the PC was unlinked:** `/home/claude/outbox10`: bridge `tiow_inbox.py` 1.17.2 (8f144f13…) + README (b294cdb7…), also the Blender addons copy; `Squad Builder\Squad Builder.html` (71cb6b40…) + README (36ba731e…). Keep 1.17.1 as `old-1.17.1\`. Then Josh restarts Blender. The on-hold 1.18 bionic file (`/home/claude/tiow_blender/tiow_inbox.py`, 45579d69…) doesn't have the 1.17.1/1.17.2 changes yet: merge them in when bionics resume.
> - **Kitbash Finalise 0.3.3** (from 0.3.1, not the on-hold 0.3.2): dialog tick "Make them manifold first (3D Print Toolbox)" (default on; greyed out without the extension, `mesh.print3d_clean_non_manifold`, Josh has print3d_toolbox 1.4.1): runs Make Manifold on Finalise's copies of the non-manifold parts after copying, re-checks, fixed ones use Manifold, the rest Exact (logged). Tests `finalise_034/test/t_make_manifold.py` (open box → closed copy, Manifold union, original untouched), t_exact 14, t_place 21, t_base 12. Delivered (md5 checked): `Desktop\Kitbash Finalise\0.3.3\` + addons copy (29f9ff2b…).

>
> **Repository (Oct 29): github.com/gerald422/Kitbash (public; Josh: sidecars yes, STLs never).** Working clone `/home/claude/kitbash`. `main` = what's installed (addons/tiow_inbox.py 1.17.2, addons/kitbash_finalise.py 0.3.3, bridge/, squad-builder/ with src + vendor three r147 + built page, library-tools/, kits/ and tests/ scripts only, docs/project-notes.md = this doc, library/ = the 3,404 sidecars + `_sources.csv` and the move/rename logs, stored byte-for-byte incl. CRLF). `bionic-1.18` = TIOW Inbox 1.18 + Finalise 0.3.2 + tests/v118 (needs main merged in). `.gitignore` blocks *.stl/*.blend/*.npz/*.bin/_builder. `library-tools/sync_sidecars.py export "D:\Kitbash Library" library` (or `Export sidecars to repo.bat`) copies changed sidecars in before a commit; `import` puts them back. The add-on carries small point samples of two Mar Fil parts (the fist and the 76-arm shoulder used for matching) - not printable, but derived from paid files, worth knowing in a public repo.
>
> **Oct 29–30, late:**
> - **Squad Builder: Two-handed tab** (installed 22:47, 1995a270…). Arms = Right / Left / Two-handed; the two-armed pieces (Two-Handed Guns / Melee, Heavy Weapons) only on Two-handed (slot `arm2`, socket Shoulder R). Picking one replaces both arms and vice versa; a model with one skips the hands (built-in weapon) and the pads (TIOW Inbox only finds pad spots on single arms) and doesn't send those picks. Fixed: changing the Squad number ate the next card click (the box fired `change` again on blur). Test `squad-builder/test/t_two_handed.js`.
> - **Marta at 90% (Josh, Oct 30: "her models are designed to be 32mm…probably 10 percent too big").** Measured: her May 2026 torso matches a Mar Fil chest at 0.90–0.92 (scaled ICP), two-armed sets have shoulder faces 12.2–13.1 mm apart vs Mar Fil 11.1; her closed hand is Mar Fil fist size (1.04), so hand-held bits may not need it. Done for the 32 Marta two-armed pieces only: sidecar `scale: 0.9`, fit/socket translations ×0.9 (right shoulder stays on Shoulder R), previews and index.json rewritten on the device (no Prepare needed; Prepare only remakes a preview when the STL is newer). Backups `D:\Kitbash Library\_backups\marta-scale-2026-10-30\`. Script `kits/marta/marta_scale.py`; Blender check `tests/marta90/t_marta90.py` (lands where the page shows, mesh at 90%). Checked the rest (Oct 30) against Mar Fil in the index, no change: boots 11.9 x 6.7 mm vs Mar Fil 11.2 x 6.9 (feet flat on the base), shoulder pads 10.5 x 10.1 vs 10.8 x 10.3 (in the Pad frame), knee pads 12.7 long vs 12.9 (a little thicker), loincloths sized for her legs. So only her arm sets (made for her own bulkier 32 mm torsos) are oversized; legs, pads, knee pads and loincloths stay at 100%. Script on the device `~/twoarm/survey_scale.py`, `soles.py`.
> - **Two-armed pieces seated by their shoulders (Oct 30, after Josh: the Mar Fil bolter reference "isn't lined up correctly").** The 'kit position' assumption for Mar Fil two-handers was wrong for several kits: the inner shoulder faces (what single arms are fitted by: face centre on the socket) landed up to 4 mm low/forward (Intercessor Bolter-Dual 1/3/4/5/6/7, Desolator, Plasma Incinerator, Pyreblaster), 7 mm high/forward (Assault Power Sword 2H 1, Eviscerator 2), tilted 15-18 deg (Assault Hammer/Spear/Sword 2H 2), and Intercessor Bolter 2 / 8 were exported turned 37-46 deg (gun pointing sideways). Bladeguard, Veteran, Techmarine and most Assault pieces were right (faces within 0.1-0.2 mm). Fix: match Mar Fil's shoulder joints (from Bladeguard Great Sword A) onto each piece (`kits/twoarm/two_icp.py`, ~0.15-0.25 mm), then only line the two joints up with Shoulder R/L - the joint is round about the shoulder axis, so the arms' own swing is kept. Applied to 86 Mar Fil pieces (sidecar Shoulder R fit + index.json; backups `_backups\two-armed-seat-2026-10-30\`); held: Power Axe 1 x4 (faces already on, the match disagreed), Plasma Incinerator 3A/3B (poor joint match - by eye). Checked independently by the face finder (`two_discs.py`): median worst-axis offset 0.2 mm after, worst 1.8 (Power Sword 2H 2B). Blender check `tests/marta90/t_seat_bolter5c.py`: Bolter 5C Grenade faces within 0.5 mm of both sockets. CyberBrush, Marta and TN Mk4 two-handers already have the right face on the socket; their left face is 1-1.6 mm out on a Mar Fil torso only because their shoulders are wider (12.0 / 11.1-11.9 / 12.6 mm vs Mar Fil 11.1), which suits their own torsos - left as they are.
> **TIOW reset** (Josh asked how to clear down the library):
> - **Recommended:** a new catalogue with only `D:\Kitbash Library` connected.
> - **Full wipe:** export a backup, rename `config.json` and `.bak`, then clear the browser's site data for TIOW's page. Both are needed: on load TIOW copies `config.json` into IndexedDB, and on save it writes IndexedDB back to `config.json`.
>
> **Source:** `/home/claude/builder/`:
> - src/shell.html, app.css, app.js;
> - build_page.py, build_index.py, prepare_builder.py;
> - make_demolib.py, make_demo.py;
> - test/.
>
> **Bionic legs: TIOW Inbox 1.18 and Finalise 0.3.2 (Oct 26).** Josh asked for an automatic plug near the leg socket for bionic legs, with the old leg booleaned out at the same time and the new leg roughly following the old one (manual was acceptable). His answers: cut at the hip; the bionic leg prints as a separate piece on the plug; Mar Fil legs first. He sent the SM Mechanical Legs kit files (he has the same files on his PC). He noted it won't work on Bladeguard (tabard) and that he may want Springles legs and other leg types later.
>
> **The kit** (each file stands up +Z, front −Y, knee hinge along X):
> - LINK_LEG is the plug: a spherical cap, ball r 2.689, glue face r 2.42 sitting 0.37 above the ball's centre.
> - LEG_HIGH (thigh): hip cup r 2.889 at (−0.38, −0.146, 8.831); knee fork centred at (0.005, −0.095, 2.168).
> - LEG_LOW (shin): knee cog at (0.025, −0.454, 9.227); ankle ball r 1.343 at (0.026, −0.373, 1.345).
> - FOOT_1–7: ankle cups r 1.37–1.43 (centres are in `BIONIC_DEFAULT`).
> - Armour: KNEE, LEG_HIGH_ARMOR, LEG_LOW_ARMOR. They aren't in an assembly frame; a contact fit was unreliable, so they get placed by eye once and then saved.
> - The STLs come as overlapping and touching shells, with stray faces and pin holes.
>
> **The cut:**
> - The leg's centre line is traced from mid-shin upwards. Mar Fil's shin points give the start; other makers' legs use a clicked Shin anchor's three points. Each step slices square to the leg and moves to the centroid of the loop round the current point.
> - The cut goes 0.8 mm below where the section's area jumps (×1.6 against the median), i.e. where the thigh meets the hip armour or crotch.
> - Cutters are three convex hulls: the thigh (its top held exactly on the cut plane), the shin and the foot.
> - The foot's region is the points nearer this leg's skeleton than the other's. Its sole is the biggest flat patch at the bottom with "down" turned about the ankle axis, so back feet on their toes come out right. A foot unioned to a rock is stopped at a boot depth of 3.6 mm.
> - The legs get one Boolean (collection operand, Manifold; Exact if the legs aren't manifold) and a Geometry Nodes tidy step. The tidy drops islands lying wholly within 1.5 mm of the cutters; it needed the cutters realised and the point positions fed to Geometry Proximity.
>
> **The pose:**
> - The plug's glue face sits on the cut centre, dome down the leg.
> - The foot sits on the old sole, under the old ankle, turned like the old foot.
> - A two-bone solve runs in the plane the old knee bends in, aiming 0.385 short along the hinge so the ankle lands exactly.
> - Joints: Bionic Hip R/L socket (ball), Knee empty (only X is free), Ankle empty (ball); the parts themselves are locked.
> - Follow Old Leg restores the pose; ◀ ▶ swaps the foot; armour toggles park a piece until Save Armour Places writes its fit (relative to its host) into its sockets file, mirrored for a left leg; Remove brings the old leg and its Shin anchor back; Mirror refuses a model with a bionic leg.
>
> **Kit parts are cleaned on their first import** (`bio_clean`): split edges with more than two faces, drop fins of 8 faces or fewer and flat shells, fill holes, orient each shell, then union with Geometry Nodes (Split to Instances by island → Mesh Boolean, Manifold). They look the same; overlapping volume is counted once. Without this, Finalise's Exact output was non-manifold (1,000+ open edges).
>
> **Finalise 0.3.2:** `BALL_JOINTS = {"Bionic Hip"}` makes the bionic leg split by default with no peg; shin and foot go with the thigh, and the plug stays with the body.
>
> **Tests:**
> - `test/v118/t_bionic.py`: about 176 checks over marine 29 R, L and both; legs 31 L, jump legs 37 R, 30 R and 32 L; plus Bladeguard 19 R, which is known not to work (tabard). It checks the joint chain to 0.01–0.03 mm, a shared hinge axis, the plug's glue face on the cut, the cut legs as one closed piece, knee locks, Follow, foot swap with the sole on the old sole, armour saved and mirrored, removing one side then both, and the Mirror refusal.
> - `t_bionic_click.py`: the clicked Shin anchor path.
> - `t_bionic_fa.py`: Finalise gives two pieces, both manifold, no peg.
> - Overview image: `test/v118/bionic_leg_overview.jpg`.
>
> **On hold (Josh, Oct 29: "Hold on all the bionic legs bits as we will fix the plug first").** Not delivered: 1.18 and Finalise 0.3.2 stay in `/home/claude/tiow_blender/` and `/home/claude/finalise/`. Josh will send an example of where he wants the plug. State reached after his reviews (Oct 26–27, "nearly perfect" / "almost there"):
> - **Cup fix:** the true LEG_HIGH hip cup is at (−0.91, −0.163, 9.801), r 2.762, opening (−0.482, 0, 0.876) (sphere votes; the first fit was ~1 mm off, which put the plug into the thigh). The kit files are a left leg; the right leg uses the mirrored meshes and points (`_bio_mirrored`, `bio_kit_side`).
> - **Sloped cut like the ribbed hip it replaces:** `bio_belt_cut` tilts the cut 30° (`BIO_BALL_TILT`) plus a swing iterated from a seated pre-pose; the ball sits on the leg's line through the middle of the leg section; the pivot puts the plug section's high edge on the glue point. Pose solve (`bio_pose`, LM over rotation + knee) keeps the cup within 15° (`BIO_CUP_MAX`) of the ball.
> - **Kit scale:** k = mean leg width / ball diameter, within 0.8–1.4, stored per model so both legs match; the panel has "Slope N° ◀▶" and "Kit size N% ◀▶".
> - **Stump:** the plug is cut just under its neck step and sunk 0.15 into the leg, so only the lip shows; where the leg is narrower than the plug a skirt is lofted from ray-cast leg sections and joined by Boolean.
> - Tests on that state: `test/v118/t_bionic.py` 179 checks, `t_bionic_fa` 9, `t_bionic_click` 3. Renders: `bionic_hip_v6.jpg`, `bionic_hip_v6_closeups.jpg`.

> **Open:**
> - Josh's plug-position example.
> - Find where the kit lives on Josh's PC (not on D: or the Desktop); the add-on looks for LINK_LEG.stl in the library.
> - Armour places, which Josh sets once.
> - Springles legs need setting up as legs first (waist, upright, base); their shins are then clicked.
> - Springles' own bionic legs as donor legs is a possible later mode.
>
> **New anchor families — plan (Oct 27–29, from Josh's examples and answers; nothing built yet).** Josh sent 16 Games Workshop reference images and the Honoured of the Chapter page (warhammer.com didn't load for WebFetch). His chapter is renegades: **no purity seals**.
> - **Hip plates:** a hip plate is placed on the legs once, and scabbards, pouches and holsters attach to the plate, so loose items are fitted once per plate, not per set of legs. Josh's example: `WaistPlate.stl` (plain plate, 1.6 × 5.2 × 6.6 mm, not in kit position).
> - **Scabbards, pouches, gun holsters:** on the hip plates.
> - **Tilt shields:** on the pauldron or on the chest (covering the gap between pauldron and torso), either side.
> - **Chest pieces:** chains and tubes reinforcing bionics, or hangers for ork and tyranid trophies; centre and sides.
> - **Tabards:** hang under the belt buckle or sit on top of it; the buckle is not cut away.
> - **Cloaks:** under the power pack, like the Captain with Jump Pack's cape, not just over the shoulders.
> - **Thigh straps** (assault legs): sculpted on the legs, so the anchor comes from matching the strap.
> - **Mechadendrites:** from the back of the power pack; Josh does one example placement and the rest of a squad randomises length, angle and head in the same place.
> - **Belt accessories, first attempt (Oct 30, for Josh to check):** the Jump Captain's waist plates are exported in place on his body. Seated the body by matching the AM torso onto his chest (0.40 mm; the waist match fails because the waist is merged), put belt anchors on it by the leg rule (`kits/belt.py`); the holster and pouch plates sit on his Hip R (nearest point 0.6 mm), the scroll plate and relic hang from Hip L. Fit = inverse of that anchor. Library: `Mar Fil - Tacticus\CaptainWithJumpPack\Accessories\MarFil Jump Captain - Hip Plate With Holster / With Pouch / With Scroll / Relic` (Accessories; `_sources.csv` +4, index + previews written directly). Blender check `tests/belt/t_belt.py`: on Mar Fil Assault 1A, Marta May 2026 Legs 1 and TN Mk6 Lower A1 every plate snaps to its hip, TIOW tilts it 6-13 deg to sit flush and settles it (nearest 0.0-0.5 mm). Page: new step 10 Belt (Right hip / Left hip / Front / Back on the legs' anchors; a part shows on the tabs it has a fit for; test `squad-builder/test/t_belt_step.js`). Installed page b4731c25, README 2b8180a3. Backups `_backups\belt-2026-10-30\`. Not done yet: the plates only on their own side (no mirrored copy), chest plate (6-Plate) and cape (7-Cape), BBoosty / CyberBrush accessories with no fit.
> - **Hidden parts (Oct 30; Josh: renegade chapter - no aquilas or purity seals anywhere, probably no scrolls; keep the work, just leave them out):** library file `_hidden.txt` (CRLF; in the repo as `library/_hidden.txt`) - a library path per hidden part, `word: <text>` (name contains), `type: <type>`, `#` comments. Starts with aquila / aquilla / purity seal / scroll / type Seals (22 parts: 16 seals, 2 TN Mk10 aquila torsos, 4 scrolls incl. the Captain's scroll plate). The page reads it with the index, leaves those parts out, shows 'N hidden' in the count, a "Hide parts" toggle by the search box (Josh: a toggle, not always on the cards) that puts Hide / Unhide on every card and shows hidden parts dimmed; Hide writes the path to `_hidden.txt`. Sidecars, STLs and TIOW untouched. Test `squad-builder/test/t_hide.js`. Installed page 2d253f33, README 5de20f45, `_hidden.txt` 36699a37. Sculpted-in aquilas (e.g. Mar Fil chests) need Josh to hide them by eye.
> - **Mechadendrite tails - Josh's spec (Oct 30, with a reference picture of a ribbed tentacle mass):** a bundle of tails from *below* the backpack (will mark sergeants later; build it for bulk now), plus 1-4 Techmarine-style mechadendrites from the backpack itself. Tails are active - curling, raised, reaching - and only sometimes reach the base. Built from his own segments (not the picture's), ending in heads; servo skulls and servo arms available. Assets: `Desktop\tubes, pipes, chains\` - `tubes.blend` (connector / tube variations), folders `servo skulls`, `Scavenger Servonators`, `Sewrvo arms`, `Warhammer Techmarine Conversion Kit @STL_Printer`, `Weapons`, `Toothed Glaives and Swords (1)` (extra weapons Josh wants included), `skull_1_with_combi_weapon_.stl`, `skull_2.stl`, `skull_3.stl`. Not surveyed yet. Plan agreed in outline: anchor under each pack, curves built from repeated segments (Part Sockets cable style) ending in heads, seeded per model with re-roll, page just switches Tails / Mechadendrites on per squad, Finalise fuses them to the pack.
> - **Captain with Jump Pack (`d:\new cults\All Mar All the time\CaptainWithJumpPack`), checked Oct 29:** 3-Legs is torso + legs in one. 6-Plate (chest plate with tassels), 7-Cape, 8/9-WaistPlate (hip plate + holster / + pouch, alternatives in the same spot, right hip, one piece each), 10-WaistPlate-3 (scroll, left hip) and 11-Relic are all exported in place on the body; 4-JumpPack is at the file origin. The cape's top is gathered at the back bracket, so the pack goes over it: cloak anchor = the Back socket, cape between body and pack. Josh's WaistPlate.stl is not the Captain's plate sculpt (ICP onto 8 and onto 9 gives two different places, median 0.14 / 0.24). Renders and scripts: `/home/claude/kits/capjp/`.
> - **Survey (Oct 29).** Already in `D:\Kitbash Library`: ~25 holsters/pouches (BBoosty Medusas Mortals, Mar Fil Outriders / Techmarine / Jump Chaplain, TN Mk4 / Mk6 / Mk10), 5 CyberBrush cloaks, 4 Mar Fil Techmarine extensible arms (type Mechadendrites), 16 servo arms, 9 CyberBrush belt decorations, loincloths (CyberBrush 5, Marta 21), 16 purity seals (unused by Josh). Only in `D:\new cults`: scabbards AssaultMarines-V2 215–220 SheatPistol and AssaultSquad 55–61 Sheath / SheathPistol / KnifeSheath (+ mirrored copies); `Tilt Shields\Tilt Shields` (24) and Iron Hands tilt plates; `Copy of TyranicWarVetAccesories` (tyranid plates, belts, shoulder, talon); mechadendrites: Iron Warriors Warsmith kit (4 styles basic / cabled / mechanical / segmented × 6 poses bend1 / bend2 / front-low / front-mid / front-top / resting, plus 7 separate tips: clamp, clamp-grav-core, drill, pliers, pliers-grav-cell, plug, scissors, sting) — modular, so suits the randomised idea — and whole sculpts in `Mechadendrites` (L/R 1–3) and Primary Mage Wargear Kit. Chains / tubes: `Desktop\tubes, pipes, chains` (chain link, plain tube connectors, tubes.blend).
> - **Open questions to Josh:** which Chaplain / Techmarine "hip armour" files he meant (none found); whether his mechadendrite example will use segments or whole sculpts (the Warsmith kit is segments + tips).
>
> **Original plan, superseded above:** (they don't export in place). Their files are being tidied into four creator folders, each holding that creator's kits.
>
> **Making a master, by hand, once per creator × armour mark × part type:**
> 1. Set a correct origin on one example part.
> 2. Run Add Socket at Origin.
> 3. Edit-select only the joint faces, then Capture Shape, named by key (e.g. `springles/grav/arms`).
>
> The template stores the joint cloud, the origin socket and the fit type, including its snap offset, in the shared `shape_templates.json`.
>
> **Applying it** (glue still to build): Match Shape → bake the origin to the matched socket → delete the socket. This runs for each part on import, or over a whole selection for bulk.
>
> **Looking up the template:**
> - creator comes from the path;
> - armour mark comes from the TIOW tags the bridge already sends;
> - part type comes from the TIOW category.
>
> Fall back from creator/mark/type → creator/type → no template. A WEAK match is flagged, not applied.
>
> **Notes:**
> - No centring step is needed first: the match works at any position or rotation.
> - The match is rigid, so do rescales after the origin step.
> - `_shape_ensure_types` never overwrites an existing type. Use mark-specific type names only where the joints really differ.
>
> **Resolved:** the other three creators don't export in place, hence the Shape Match approach above. Once the files are in one folder per creator, the creator can be read from the path the bridge already sends.

---

## Summary

1. **Batch origin-setting is feasible, and most of the engine already exists.** `sockets.flat_patch_frame(ctx, obj, tol)` is the function behind *Set Origin at Flat*. It only reads the cursor position as a seed, so a headless script can set the cursor and call it directly. The batch needs three new things: a **seed rule**, a **roll rule** and a **confidence score**.
2. **Roll is the main problem.** *Set Origin at Flat*'s roll depends on how the STL happened to be oriented in world space, and it jumps by 90° once the face tilts more than about 8° from vertical (details below). A shared fit-type offset needs every arm to have the same roll, so the batch has to set roll itself. The fix is a 1-DOF roll sweep against the template arm, using the `KD` class already in `shapematch.py`.
3. **Connect the tools through files, not code.** First, TIOW's organised folder layout. Second, a manifest keyed by **SHA-256**. Never write into TIOW's `config.json`.
4. **Best uses beyond arms:** batch Shape Match socket kits for torsos, Cycle Variant and Dressing Room collections built from TIOW filters, and measured joint data fed back into TIOW's categorisation.

---

## Relevant parts of each tool

| TIOW-FTRP | Part Sockets |
|---|---|
| Catalogue items: `category`, `armour` (tac/grav/phob/term…), `tags`, `variant` (Raw / Presupported), `mirrored`, `path`, `bytes`, notes | `flat_patch_frame()`: flat-patch centroid + normal from a seed point |
| Folder report export (`tiow-folder-report.json`): per STL `sha256`, `triangles`, `dimensions`, `status`, `warnings` | `shapematch.run_auto_match()`: RANSAC + ICP that returns candidates with `inlier`/`rms`. The matching maths needs only numpy |
| Catalogue export (`*-catalogue-backup.json`): all items + notes | `cable_units._import_mesh_file()`: STL import that returns what it created. `_normalise_unit` shows how to keep scale |
| Organiser writes `Master Pieces/<Category>/<Raw\|Presupported\|Unspecified>/…` | Cycle Variant: the pool is the part's first non-`WS_` collection |
| Server already spawns local processes (`FolderPicker.exe`, `explorer.exe`) | JSON libraries on disk (`shape_templates.json`, `joint_library.json`) with atomic writes and an UNREADABLE guard |
| Quarantine + SHA-256 duplicate detection | Bake for Print: STL export in mm (`scale_length × 1000`) |
| | Dressing Room: racks collections around the active model; `dr_home` |

Prerequisite: the catalogue in TIOW's saved config is currently empty (`items: []`, no folder linked to the catalogue). `D:\new cults` (or the working copy) has to be connected and scanned before any of this has data.

---

## The batch origin pipeline (your arm example)

### 1. Template, made once in Blender
- Import one good right arm and **don't move it**. *Set Origin* operators never move geometry, so world space stays equal to STL space.
- Set its origin with **Set Origin from Flat Face**. The click on the front face makes the roll deliberate.
- A new **Save Origin Template** operator stores:
  - `seed_uvw`: the patch centre as a fraction of the world bbox
  - `patch_area`
  - `tol`
  - `fit_type` (e.g. `arm_r`)
  - about 3k template vertices in the template's local frame, packed with `_shape_pack`

  Store templates in their own `origin_templates.json`, not in `shape_templates.json`. `_shape_enum_items` lists every key in that file, and Shape Match expects each entry to have `points`.

### 2. Locate the patch on each part
- Seed = `bbox_min + (bbox_max − bbox_min) * seed_uvw`. Set `scene.cursor.location` to it and call `flat_patch_frame`. This is your "cursor at a similar location" idea.
- It holds when files share an export orientation, which is normal within one sculptor's set. Mixed sets (lying on the print bed vs upright) need the **v2 locator**: flood-fill every planar patch over a minimum area, then score each by area ratio and roll-sweep fit. The flood fill already exists in `flat_patch_frame` and just needs running from every unvisited face.
- **Shape Match fallback** for sets that share the joint geometry: capture the shoulder ring with a socket at the origin. `bpy.ops.ws.shape_match(template=…)` then gives a full 6-DOF frame, and its inlier % is the confidence.

### 3. Fix the roll
`flat_patch_frame` builds X as `ref × z`, where `ref` is world Z. It switches to world Y only when `|z·Z| > 0.99`. Checked numerically:

| Face normal | Resulting X axis |
|---|---|
| tilted 5° toward +X | +X |
| tilted 9° toward +X | +Y (90° jump) |
| tilted 9° toward +Y | −X |

The docstring already says "roll is arbitrary", which is fine for connectors but not for 40 arms sharing one `arm_r` offset. The fix:
- Take the part's points in the patch frame.
- Sweep roll 0–355° in 5° steps, with and without an X-mirror.
- Score each step by mean nearest-neighbour distance to the template cloud.
- Keep the best.

The mirrored result gives **handedness detection** for free. It follows the same X-mirror convention as `mirror_x()` and *Mirror Offset*, so `arm_l` offsets derived by Mirror Offset stay valid.

### 4. Confidence and the review loop
Each part gets `status: ok | review | failed` based on:
- patch-area ratio against the template (≈0.4–2.5×)
- best fit ÷ bbox diagonal
- the margin to the next-best distinct roll or handedness

Flagged parts go into `review.blend`, racked by Dressing Room with origins visible. You fix them by hand (Set Origin from Flat Face). A small **Write Frames to Manifest** operator then saves the corrections back.

### 5. Output: frames, not meshes
An origin is just a 4×4 in the STL's own coordinates. Store it, keyed by SHA-256, and any later import can apply it straight away with no recompute. That avoids a multi-GB `.blend` holding every arm. A library `.blend` is still useful for curated sets you actually kitbash with.

### Sketch (not yet run)
```python
# blender.exe --background --python ps_batch_origin.py -- job.json
import bpy, json, math, sys
import numpy as np
from mathutils import Matrix, Vector
from bl_ext.user_default.part_sockets.sockets import flat_patch_frame
from bl_ext.user_default.part_sockets.shapematch import KD, _shape_unpack
from bl_ext.user_default.part_sockets.cable_units import _import_mesh_file
from bl_ext.user_default.part_sockets.core import flat_from_mat, remove_objects

def local_points(obj, M, n=3000):
    nv = len(obj.data.vertices)
    co = np.empty(nv * 3, np.float32)
    obj.data.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)[::max(1, nv // n)].astype(np.float64)
    T = np.array(M.inverted_safe() @ obj.matrix_world)
    return co @ T[:3, :3].T + T[:3, 3]

def best_roll(pts, kd, step=5):
    best = (math.inf, 0, False)
    for deg in range(0, 360, step):
        a = math.radians(-deg); c, s = math.cos(a), math.sin(a)
        q = pts @ np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]]).T   # frame M @ Rz(deg)
        for mirrored in (False, True):
            qq = q * (-1.0, 1.0, 1.0) if mirrored else q
            best = min(best, (kd.query(qq)[0].mean(), deg, mirrored))
    return best

job = json.load(open(sys.argv[sys.argv.index("--") + 1]))
tpl = job["template"]                       # loaded from origin_templates.json
kd = KD(_shape_unpack(tpl["cloud"]))
results = {}
for part in job["parts"]:                   # [{path, sha256}] from TIOW's exports
    objs = _import_mesh_file(part["path"])
    if len(objs) != 1:
        results[part["sha256"]] = {"status": "failed", "reason": "import"}; continue
    obj = objs[0]
    lo, hi = Vector(obj.bound_box[0]), Vector(obj.bound_box[6])
    bpy.context.scene.cursor.location = lo + (hi - lo) * Vector(tpl["seed_uvw"])
    M, info = flat_patch_frame(bpy.context, obj, tpl["tol"])
    if M is None:
        results[part["sha256"]] = {"status": "failed", "reason": info}
    else:
        d, deg, mirrored = best_roll(local_points(obj, M), kd)
        M = M @ Matrix.Rotation(math.radians(deg), 4, 'Z')
        results[part["sha256"]] = {"frame": flat_from_mat(M), "fit": d / (hi - lo).length,
                                   "handedness": "L" if mirrored else "R"}
    remove_objects([obj])                     # the add-on's own delete; no orphan mesh left
```
Gaps the sketch leaves open:
- Patch area (see refactor A below).
- Status thresholds.
- Plates holding more than one large mesh island: check with bmesh, then split or flag.
- Resume support: skip SHA-256s already in the manifest.
- Saving to a `.blend` instead of only the manifest.

Run Blender **without** `--factory-startup`, so the installed extension loads as `bl_ext.user_default.part_sockets`. `tests/smoke.py` enables the add-on by its development name `part_sockets`, which won't match an installed extension.

---

## The contract between the tools

**v0 — the folder is the interface (no code coupling).** TIOW organises files into `Master Pieces/Arms/Raw/`, and the batch takes that folder. Part Sockets already uses the same idea for cable units: a folder on disk is the source of truth.

**v1 — `part_sockets_manifest.json`, keyed by SHA-256.** TIOW's cleanup renames and moves files, so results keyed by path would break after every run. A hash also means each unique mesh is processed once, however many copies exist. Use TIOW's plain SHA-256 (from the folder report or `/api/local/hash`), not the duplicate finder's `seg512:` block fingerprint. Frames are stored as 16 floats, row-major, the same layout as `core.flat_from_mat`.

```json
{ "schemaVersion": 1,
  "parts": { "<sha256>": {
      "path": "Master Pieces/Arms/Raw/Arm_R_03.stl", "bytes": 1234567,
      "origin":  { "template": "arm_r_shoulder", "frame": [16 floats], "handedness": "R",
                   "status": "ok", "patchArea": 39.8, "jointDia": 7.1, "fit": 0.012 },
      "sockets": { "template": "torso_ring", "inlier": 0.94, "rms": 0.021,
                   "kit": [ { "type": "arm_r", "frame": [16 floats] } ] },
      "fitTypes": ["arm_r"] } } }
```

The Part Sockets side then needs one importer: **Import from Manifest**. It imports the STLs into a named collection and applies the stored frames. That collection feeds Cycle Variant and Dressing Room directly.

**v2 — optional TIOW patch.** Keep it in its own module so updates from TIOW's author don't keep overwriting it.
- **Send to Blender**: a new `/api/local/blender` route. It resolves each part through the existing `safe()`, writes `job.json` and spawns `blender.exe --background`, the same way the server already spawns `FolderPicker.exe`.
- **Status from the manifest**: chips and filters such as *Origin set*, *Fits arm_r* and *Needs review*.
- **Viewer overlay**: draw the origin and socket frames in TIOW's three.js viewer. Use `Matrix4.set(...frame)`, which is row-major. `stl-worker.js` also needs to post the `center` it subtracts.

**Don't write `local-data/config.json` from Blender.** The server reads it once at start, keeps it in memory, and `persist()` writes that copy back. The browser also re-persists from IndexedDB on every save, so outside edits get overwritten.

---

## Other applications, ranked

| # | What | How | Effort | Value |
|---|---|---|---|---|
| 1 | **Batch origins per category**: heads (neck cut), legs/bodies (waist), backpacks (mount face) | The arm pipeline with one template per category | S once arms work | High |
| 2 | **Batch socket kits for torsos** | Capture the neck ring + shoulder cuts + backpack mount once, then run `ws.shape_match` headless on every torso. Inlier % → status | M | Very high: once torsos have kits and limbs have standard origins, any arm snaps to any torso |
| 3 | **TIOW filter → Blender collection** (`arms_right_tac`) | Import from Manifest | S | High: Cycle Variant auditions the whole filter, Dressing Room racks it |
| 4 | **Joint size as data**: equivalent diameter `√(4A/π)` from the flat patch | Falls out of #1 once patch area is returned | S | Medium–high: checks TIOW's armour-family tags (Gravis vs Tacticus joints differ), and supports a "joint within ±10% of this torso" filter |
| 5 | **Categorisation feedback** | "Arms" items that fail the arm template are probably mis-categorised; Shape Match hits on `Unclassified` items suggest a category | M | Medium: helps you tune TIOW's categorising |
| 6 | **Print-ready parts back into the collection** | Point Bake for Print's export folder at `Master Pieces/<Category>/Raw/`, with a `_ps` suffix on object names (files are named after objects). TIOW's organiser treats that path as already organised | S | Medium |
| 7 | **Consistent thumbnails** | Standard origins mean one camera fits every part; background Workbench render → PNG keyed by SHA-256 | M (needs a TIOW patch to show them) | Low–medium |
| 8 | **Cable units from the collection** | Point the units-folder preference at an organised chains/cables folder. TIOW has no category for these yet; one rule adds it | S | Low–medium |
| 9 | **Conform Detail sources** | Browse TIOW's Seals / Chapter Bits / Banners from Blender | M | Later |

Poor batch candidates: **shoulder pads** (curved, so they need Settle Along Axis + per-part fit) and **weapons** (the grip isn't flat; Shape Match on the grip might work).

---

## Review findings that affect this

- **Roll discontinuity** in `flat_patch_frame` (above). This is the one that would quietly ruin a batch.
- **The origin-move block is copied three times**: `WS_OT_origin_at_flat`, `WS_OT_bake_origin`, `WS_OT_origin_from_face`. All three do the same `L = mw⁻¹ @ M; data.transform(L⁻¹, shape_keys=True); mw = mw @ L` plus child restore. `check_review`'s duplication test only compares module-level function bodies, so it misses this. → **Refactor A**: move it into `core.set_origin_frame(obj, M)` (with child restore), and have `flat_patch_frame` also return the patch area it already computes. The batch then imports both.
- **TIOW has two categorisers that disagree.**
  - `app.js guessCategory` uses `/arm(?!or)/i`, which matches *armour*, *armoury*, *charm* and *farm*. It also uses `/legs?/i`, which matches *Legion* and *legacy*.
  - `folder-organisation.js` uses word boundaries (`\barms?\b`) and is correct.
  - So the catalogue's "Arms" filter will include armour plates; the organised `Arms/` folder is cleaner. The organiser also files arm-mounted weapons from an "Arm Weapons" folder under Arms, because the Arms rule comes before the Weapons rule. The batch's confidence check will flag those.
- **Process only Raw files.** Supports attach to exactly the flat faces the locator needs, and they distort Shape Match.
- **Scale.** Part Sockets assumes 1 unit = 1 mm. STL import at scale 1.0 into a mm scene gives that. Skip anything TIOW's audit flags (extent < 1 or > 300 units means the wrong unit or a whole plate).

---

## Suggested build order

1. Refactor A in Part Sockets: `core.set_origin_frame` + patch area from `flat_patch_frame`.
2. Save Origin Template operator + `origin_templates.json`.
3. Headless `ps_batch_origin.py` with the roll sweep, writing the manifest. Test on one sculptor's arm set first.
4. Import from Manifest operator → collections for Cycle Variant and Dressing Room.
5. Review loop: `review.blend` + Write Frames to Manifest.
6. Torso socket kits via headless Shape Match (#2).
7. Optional TIOW patch: Send to Blender + manifest chips.

---
name: kitbash-sidecars
description: Use when adding a new maker, kit or part type to Josh's Kitbash Library: generating the part.sockets.json sidecars (sockets, fits, anchors, variants) so parts snap in TIOW Inbox and the Squad Builder.
---

# Generating sidecars for the Kitbash Library

A sidecar `<part>.sockets.json` sits beside each STL in `D:\Kitbash Library`. TIOW Inbox reads it on import (sockets, fits, category). Prepare Squad Builder reads it to build the page's index. The code and every sidecar are in this repo (`library/` mirrors the library's folders). **STLs never go in the repo.** The history of every kit done so far, with measured values, is in `docs/project-notes.md`: read the section for the nearest kit before starting.

## Ground rules (Josh)

- **Every part must fit every kit.** Follow the shared conventions below so a new kit's torso takes Mar Fil arms and its arms go on any torso. Don't invent a new frame per kit.
- **Test only a subset.** Use the parts the change affects: a few models built in Blender, plus renders. Never re-run every suite or every library part; it burns usage.
- **Never overwrite what Josh or Prepare made.**
  - Merge into existing sidecars rather than replacing them.
  - Keep sockets with `props.tiow_anchor` `clicked`, `copied` or `auto`, and keep `tiow_corrected`, `tiow_holds` and `exact`.
  - Back up the sidecars you touch first, under a dated folder.
- **Never write TIOW's `config.json`.**
- Ask Josh for a reference placement when no convention covers a part, such as a new pauldron shape, a hip plate or a belt bit. He places one by eye in Blender; you carry it across the family.

## Sidecar format

All matrices are 4x4 and **row-major** (16 floats). They are in the part's **own STL file coordinates**, in file units (TIOW Inbox multiplies translations by its unit scale).

```json
{
  "schemaVersion": 1,
  "part": "24-Torso-3",
  "category": "Chests",
  "sockets": [{"type": "Neck", "name": "24-Torso-3_socket_Neck", "matrix": [16],
               "display_type": "ARROWS", "display_size": 3.0,
               "props": {"tiow_from": "how it was found"}, "points": [[x,y,z], ...]}],
  "fits": {"Waist": [16]},
  "notes": {"Waist": "why"},
  "original": {"name": "...", "folder": "...", "path": "..."},
  "variants": [{"side": "L", "mirror": true, "align": [16], "name": "...", "title": "...",
                "folder": "...", "from": "...", "match": 0.0,
                "sidecar": {"sockets": [], "fits": {}}}]
}
```

**What the pieces mean:**
- **Socket `matrix`:** where something attaches, in the part's frame. Z points out of the joint.
- **Fit:** where this part sits on a socket of that type: part = socket · T(0, 0, gap) · fit.
- **`category`:** must be one of TIOW Inbox's `DEFAULT_JOINTS` types (Arms, Legs, Chests, Heads, Backpacks, Jump Packs, Shoulder Pads, Knee Pads, Pistols, Melee, Shields, Hands, Hand-less Weapons, Two-Handed Guns/Melee/Held, Heavy Weapons, Bases, Adapters, Accessories, Cloaks, and so on). The category decides the joint.

**Optional keys:**

| Key | Meaning |
|---|---|
| `upright` | [16] stands a lying or Y-up file up in the Mar Fil frame |
| `scale` | the maker's scale; sockets and fits are in scaled coordinates |
| `noPad` | the arm has no Pad anchor |
| `noHand` | the arm has its weapon or hand built in, so no wrist socket |
| `offHand` + `pivot` | two-handed weapons on ball wrists |
| `exact` | fit types placed exactly, with no rock or settle |
| `types` | fit-type offsets |
| `ruled` | which fits came from a rule |
| `tiow_holds` (socket prop) | the part file name(s) that socket is reserved for |

**Variants:** a maker's left copy, or a mirror, folded into the right part's file. `align` maps the kept file's coordinates to the copy's, and the copy's own sockets and fits go in `sidecar`. Duplicates and on-the-spot mirrors are marked `duplicate` / `synth`.

## Shared conventions (the Mar Fil kit frame: Z up, front +Y, standing on the origin)

Take reference values from the existing library sidecars rather than retyping them.

**Torso and legs**
- **Chests:** the Assault torso's sockets exactly, i.e. Shoulder R/L, Neck, Back, Waist (see `MarFil Assault - Torso 3.sockets.json`). A flat-bottomed torso also gets `Flat Waist`. For Turtle Ninja style torsos, use the flat torso rule and neck rule D (`kits/cr`, `kits/tn`).
- **Legs → Waist:** seated like Josh's Assault legs. Match the Assault waist region onto the new legs and carry Josh's placement across (`kits/legs_match.py`, `kits/*/legs_seat.py`).
  - Flat-topped legs (Marta, TN) get a `Flat Waist` fit from their top face and bring the body adaptor.
  - Legs also get `Base` (under the feet), and belt anchors Hip R/L and Belt Front/Back from `kits/belt.py` (Z out of the belt, Y up).

**Arms and what they hold**
- **Arms → Shoulder R/L:** the shoulder disc's centre on the socket, face flat on the chest (`kits/disc.py`, `kits/*/disc*.py`).
  - Arms exported as turned left/right pairs get one rigid placement for the pair.
  - Don't hand-write wrist or Pad anchors: TIOW Inbox works them out on first import (wrist rule; Pad anchor matched from Josh's 62-on-76 example) and Prepare caches them.
- **Hand-held parts → Hand R/L:** the hand rule (`kits/handrule.py`, reference fist in `kits/fistref.py`) unless the maker's assembly gives the grip.
  - Hand-less weapons get a `Grip` fit.
  - Two-handed weapons go on Shoulder R, spanning L.

**Head, back and pads**
- **Heads → Neck:** Josh's Assault helmet seat, with its neck ring matched onto the new head (`kits/neckfit.py`). Mar Fil's own export position is 4.5° off it.
- **Packs → Back:** the mount plate on Back, plate centres together. Toppers go on `Back Top` (pack top surface, Z up, Y forward).
- **Shoulder pads / shin pads:** fitted to the three-point anchor frames.
  - Shins: the rig's shin frame.
  - Pauldrons: the frame from Josh's 62-on-76 example.
  - Set `mirrorLeft` for right-only pads.
  - Pads Josh will place by eye can be left for Save Correction.

**Bases**
- The round base rule: disc centre on the rim top, Z up from the bottom face. TIOW Inbox 1.17.2 then raises a base to meet the feet automatically.

**Parts exported together**
- Parts the maker exports in one assembly frame (a whole kit, a bike, a one-off character) keep that frame. Fits come from the assembly, so they land as the maker posed them.

## Procedure

1. **Scope with Josh.** Settle which maker, kits and part types are in. Skip by default: posed bodies, presupported copies, and duplicates (keep raw files only).
2. **Survey on the device.** Use `device_bash` in `D:\new cults\...`.
   - List the files by folder; get triangle counts and bounding boxes.
   - Work out how the maker exports: kit frame, print plate, Y-up, or scattered.
   - Render a small contact sheet from a few staged files to confirm front, up and left/right before writing any rule. A toe or knee heuristic has been wrong before.
3. **Write a build script** in `kits/<maker-or-kit>/`.
   - It reads the STLs with numpy and works out sockets and fits per the conventions.
   - It writes sidecars into a staging folder that mirrors the library's paths.
   - Reuse `kits/geo.py`, `kits/nc/geo.py` and the ICP and disc helpers.
   - Record how each value was found in `props.tiow_from` / `notes`.
4. **Check a subset in Blender.** Use the build container's `bpyenv`.
   - Build 2–4 marines with TIOW Inbox's `import_request`, using the staged sidecars.
   - Mix the new kit with Mar Fil parts both ways: new arms on a Mar Fil torso, Mar Fil arms on the new torso.
   - Check every joint snaps, the closest approach and the deepest cut (≲0.65 mm, as within a kit), and render.
   - Send Josh the renders before merging.
5. **Into the library.**
   - **New files:** `library-tools/plan_library.py --work --survey --only <plan>`, then `build_library.py --work --only`. Never a full re-run, because it overwrites sidecars.
   - **Names:** apply the naming rules with `plan_names.py` / `rename_library.py` (log, `--undo`).
   - **Mirror copies:** fold them with `fold_twins.py` (fold only if median ≤0.05 mm and 95% within 0.15 mm).
   - **Existing parts:** merge the new keys in, back up first, and keep Josh's anchors.
   - **Deliver** each file staged under a new path, `device_commit_files`, then check the md5 on the device.
6. **Prepare.** Josh runs `Prepare Squad Builder.bat`, or start it from his Desktop folder. It only redoes new or changed parts. Read `_builder\no_fit.txt` for parts still without a fit.
7. **Record it.**
   - Run `library-tools\Export sidecars to repo.bat`, or `python library-tools/sync_sidecars.py export "D:\Kitbash Library" library` in the clone.
   - Commit the build script and sidecars to `main` with the session attribution lines, and push.
   - Add a short section to `docs/project-notes.md`: what was decided, the reference values, the test results, and the files delivered.

## Fixing one part later

Don't regenerate a whole kit for a small error. In Blender, move the part and use **Save Correction** (TIOW Inbox panel):
- **Fix the Part** saves this part's fit everywhere.
- **Fix the Socket** moves the host's socket.
- **Whole Folder** and **Both Sides** are options on either.

Then run Prepare, export the sidecars and commit.

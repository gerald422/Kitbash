---
name: kitbash-sidecars
description: Use when adding a new maker, kit or part type to Josh's Kitbash Library: generating the part.sockets.json sidecars (sockets, fits, anchors, variants) so parts snap in TIOW Inbox and the Squad Builder.
---

# Generating sidecars for the Kitbash Library

A sidecar `<part>.sockets.json` sits beside each STL in `D:\Kitbash Library`. TIOW Inbox reads it on import (sockets, fits, category). Prepare Squad Builder reads it to build the page's index. Every sidecar is in this repo (`library/` mirrors the library's folders). **STLs never go in the repo.**

**Start here:**
- A new maker's heads, pauldrons and loose bits: run `kits/creator/add_creator.py` (its docstring is the whole procedure; one JSON config per maker). Don't redo those steps by hand. On the PC it is one command inside Blender (`... add_creator.py -- add RECIPE --src FOLDER`), which also leaves out parts the library already has.
- Anything else (a new part family, a new rule): read the nearest kit's entry via `docs/notes/INDEX.md`, write a script against `kb/` (`kb.geo`, `kb.sidecar`, `kb.index`, `kb.deliver`), deliver with `tools/kb.py apply`. Standing rules and the PC are in `CLAUDE.md` and `docs/reference.md`.

## Ground rules (Josh)

- **Every part must fit every kit.** Follow the shared conventions below so a new kit's torso takes Mar Fil arms and its arms go on any torso. Don't invent a new frame per kit.
- **Test only a subset.** Use the parts the change affects: a few models built in Blender, plus renders. Never re-run every suite or every library part; it burns usage.
- **Never overwrite what Josh or Prepare made.**
  - Merge into existing sidecars rather than replacing them.
  - Keep sockets with `props.tiow_anchor` `clicked`, `copied` or `auto`, and keep `tiow_corrected`, `tiow_holds` and `exact`.
  - Back up the sidecars you touch first, under a dated folder.
- **Never write TIOW's `config.json`.**
- Ask Josh for a reference placement when no convention covers a part, such as a new pauldron shape, a hip plate or a belt bit. He places one by eye in Blender; you carry it across the family.
- Renegade chapter: no aquilas, purity seals or scrolls. New parts with them sculpted in go on `_hidden.txt` (a library path per line, `# why` above it); merge with Josh's current file, he hides parts from the page.
- Keep usage low: stage only what a task needs, ask before copying big blends.

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

**Belt, loincloths, wings (TIOW Inbox 1.17.4-1.17.5)**
- Belt bits (Accessories, Grenades, Seals, Trophies): Hip R / Hip L / Belt Back only, rocked and settled.
- Loincloths (type `Loincloths`): Belt Front only. Rule: the top edge's centre, at the back, on the anchor; face out along Z, top along Y; then rock and settle. A loincloth that tucks under a buckle gets Josh's own placement with Fix the Part (`exact`).
- Wings (type `Wings`, sided) hang from a connector (type `Wing Mounts`, sided) that the wing brings: the wing's sidecar key `adaptor` is the connector's library path; the pack carries `Wing Mount R/L`, the connector `Wing R/L`. Only packs Josh chose get Wing Mounts (TN Mk6 Universal).
- Held in both hands, no arms (`Two-Handed Held`): Hand R fit, `offHand` (the other wrist) and `pivot`.

**Scale and sources**
- A maker at another scale gets `scale` (Marta's two-armed sets 0.9; Bladecrow wings 1.3); fits and sockets are then in scaled coordinates, variants need their own `sidecar.scale`.
- OBJ-only sources: convert to a binary STL in the OBJ's own coordinates, record the OBJ in `_sources.csv`.
- Taking placements from Josh's blend: his meshes are usually the source files moved (origin set, rotations or scale applied). Register each mesh onto its source file first (24 axis turns + ICP, similarity if he scaled it: `kits/wings/extract.py`), then measure in the source file's coordinates; take out any scale on his model (orthonormalise Z, then Y).

**Parts exported together**
- Parts the maker exports in one assembly frame (a whole kit, a bike, a one-off character) keep that frame. Fits come from the assembly, so they land as the maker posed them.

## Fast path: a new maker's helmets, pauldrons and loose bits

`kits/creator/add_creator.py` does the whole job in about eight tool calls (its docstring has the steps and the
config keys; `kits/creator/wargame-exclusive.json` is the example). Helmets/heads get the Neck fit (AM Helmet 1 seat),
pauldrons the Pad fit (pad 62, pushed out where thicker inside); every other type is filed without a fit and logged.
Parts whose match fails a gate (neck ring > 0.30 mm off, pad 62 only matching at the scale limit) are filed without a
fit too. On the PC, `Squad Builder\add_creator_pc.py survey ... --stage` surveys and packs one archive to stage, and
the delivery's `on_pc.py apply` does the md5 checks, backups and writes in one call. Arms, legs and torsos filed into a folder that already has fitted ones take `"fit": "like"` (`kb/carry.py`, notes 091: carried from
the fitted folder-mates, gated; the dropped ones are filed without a fit). A kit with no fitted folder-mates, packs and
other fitted types still need the procedure below (a kit script), then can be filed with the same delivery.

## Procedure (when add_creator.py doesn't cover it)

1. **Scope with Josh.** Which maker, kits and part types are in. Skip by default: posed bodies, presupported copies, duplicates (raw files only).
2. **Survey on the PC** (`kits/creator/on_pc.py survey`, or your own `device_bash` listing): files by folder, triangle counts, bounding boxes. Work out how the maker exports (kit frame, print plate, Y-up, scattered). Render one small contact sheet to confirm front, up and left/right before writing a rule: a toe or knee heuristic has been wrong before.
3. **Write one build script** in `kits/<maker-or-kit>/` on `kb.geo`. It works out sockets and fits per the conventions and records how each value was found (`props.tiow_from`, `notes`). Gate each fit on a number (match residual), as `add_creator.py`'s `GATES` do; parts that fail the gate are filed without a fit and logged, not dropped.
4. **Check a subset in Blender**: 2-4 marines through TIOW's `import_request`, the new kit mixed with Mar Fil both ways. Every joint snaps; closest approach and deepest cut within 0.65 mm. Send Josh the sheet before merging.
5. **Write sidecars** with `kb.sidecar.merge` onto what is on the PC (never a full `build_library.py` re-run: it overwrites). Names by `plan_names.py`; mirror copies folded with `fold_twins.py` (median <= 0.05 mm and 95% within 0.15 mm).
6. **Deliver** with `kb.deliver` + `tools/kb.py apply`: sidecars, `_sources.csv` rows (CRLF), the index updated in place (`kb.index`) with previews, hidden lines.
7. **Record it**: `tools/validate.py`, sidecars exported into `library/`, commit and push, a `docs/notes/NNN-<slug>.md` entry (decisions, reference values, test numbers, files delivered) and its `INDEX.md` line, `docs/OPEN.md`.

A new part type also needs: `joints.json` then `tools/gen_joints.py` (add-on table, bridge template, partTypes), a step or slot in `squad-builder/src/app.js` (`python3 build_page.py`), a short name in `plan_names.py`.

## Fixing one part later

Don't regenerate a whole kit for a small error. In Blender, move the part and use **Save Correction** (TIOW Inbox panel):
- **Fix the Part** saves this part's fit everywhere (and marks it `exact`: no rock, settle or base rise next time).
- **Fix the Socket** moves the host's socket (`tiow_corrected`; since 1.17.3 belt bits on it are only settled, not rocked).
- **Whole Folder** and **Both Sides** are options on either. Both Sides is on by default: turn it off when both sides were placed by hand.

Then run Prepare (or update the index entries in place), export the sidecars and commit.

When Josh sends a blend with parts moved by hand (`Desktop\query.blend`): rebuild the same model with TIOW in the container and compare each part relative to the torso (`kits/corrections/query-*/rebuild.py`), so TIOW's own rock/settle/base rise isn't taken for his moves; save the moves with TIOW's own `correct_socket` / `correct_part` (`both=False`, `folder=False`), rebuild to confirm, deliver.


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

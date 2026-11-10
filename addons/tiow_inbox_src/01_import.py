# ---------------------------------------------------------------- import

def _layer_collection(lc, coll):
    if lc.collection == coll:
        return lc
    for child in lc.children:
        found = _layer_collection(child, coll)
        if found:
            return found
    return None


def _target_collection(scene, view_layer, name):
    """The collection named after the TIOW category, created if missing and
    made visible if it is excluded. Part Sockets' Cycle Variant takes its
    pool from a part's collection, so every arm sent lands in one pool."""
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
    if coll.name not in scene.collection.children and \
            _layer_collection(view_layer.layer_collection, coll) is None:
        scene.collection.children.link(coll)
    lc = _layer_collection(view_layer.layer_collection, coll)
    if lc is not None:
        lc.exclude = False
        lc.hide_viewport = False
    coll.hide_viewport = False
    return coll


def _view3d_override():
    """A window and 3D View area for bpy.ops, when one exists. Timers run
    with a thin context; the importer is happier with a real area."""
    wm = bpy.context.window_manager
    for win in getattr(wm, "windows", []):
        for area in win.screen.areas:
            if area.type == 'VIEW_3D':
                return {"window": win, "area": area}
    win = getattr(bpy.context, "window", None)
    return {"window": win} if win else {}


SIDECAR = ".sockets.json"


def read_sidecar(stl_path):
    """<part>.sockets.json next to the STL, written by the lift-out script."""
    p = os.path.splitext(stl_path)[0] + SIDECAR
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    if not isinstance(data.get("sockets"), list):
        data["sockets"] = []
    return data


def ensure_types(scene, types):
    """Add the fit types these sockets use if the scene lacks them, with
    their offsets. Existing types are never touched - the same rule Part
    Sockets' Shape Match follows - so a scene's own tuning always wins."""
    if not hasattr(scene, "ws_types") or not isinstance(types, dict):
        return []
    have = {t.name for t in scene.ws_types}
    added = []
    for name, spec in types.items():
        if not name or name in have or not isinstance(spec, dict):
            continue
        t = scene.ws_types.add()
        t.name = name
        t.gap = float(spec.get("gap") or 0.0)
        mat = spec.get("mat")
        if spec.get("captured") and isinstance(mat, list) and len(mat) == 16:
            t.mat = [float(x) for x in mat]
            t.captured = True
        added.append(name)
    return added


def rebuild_sockets(part, data, scale, coll):
    """Recreate the part's socket empties, parented to it, in the same place
    relative to the geometry as in the file they were lifted from."""
    loc, rot, _ = part.matrix_world.decompose()
    frame = Matrix.LocRotScale(loc, rot, Vector((1.0, 1.0, 1.0)))
    target = coll or (part.users_collection[0] if part.users_collection
                      else bpy.context.scene.collection)
    made = []
    for s in data.get("sockets", []):
        tname = str(s.get("type") or "")
        m = s.get("matrix")
        if not tname or not isinstance(m, list) or len(m) != 16:
            continue
        L = Matrix((m[0:4], m[4:8], m[8:12], m[12:16]))
        L.translation = L.translation * scale
        ob = bpy.data.objects.new(f"{part.name}_socket_{tname}"[:63], None)
        target.objects.link(ob)
        try:
            ob.empty_display_type = s.get("display_type") or 'ARROWS'
        except (TypeError, ValueError):
            ob.empty_display_type = 'ARROWS'
        ob.empty_display_size = float(s.get("display_size") or 1.0) * scale
        ob["ws_type"] = tname
        for k, v in (s.get("props") or {}).items():
            if isinstance(k, str) and k.startswith(("ws_", "tiow_")) and isinstance(v, (str, int, float)):
                ob[k] = v
        ob.parent = part
        ob.matrix_parent_inverse = part.matrix_world.inverted_safe()
        ob.matrix_world = frame @ L
        made.append(ob)
    return made


# Pads named as such go to their pad joint whatever folder they're in (Marta
# keeps her "Chin_pad" shin pads in a "legs-..." folder, which TIOW reads as
# Legs), and TIOW's own unpatched type names map onto the joints'.
PAD_NAMES = (("Knee Pads", re.compile(r"(shin|chin|knee)[ _-]?pads?|greaves?", re.I)),
             ("Shoulder Pads", re.compile(r"shoulder[ _-]?pads?|pauldrons?", re.I)))
TIOW_NAMES = {"Shin Pads": "Knee Pads", "Bodies": "Chests"}


def part_category(job):
    """The part type a request is handled as: the type saved in the part's
    .sockets.json, else a pad by its file name, else TIOW's category (its own
    names mapped onto ours)."""
    side = read_sidecar(str(job.get("path", ""))) if job.get("path") else None
    if side and isinstance(side.get("category"), str) and side["category"].strip():
        return side["category"].strip()
    stem = os.path.splitext(os.path.basename(str(job.get("path", ""))))[0]
    stem = str(((side or {}).get("original") or {}).get("name") or stem)
    for cat, rx in PAD_NAMES:
        if rx.search(stem):
            return cat
    cat = str(job.get("category") or "").strip()
    return TIOW_NAMES.get(cat, cat)


def load_stl(path, job, prefs, collection=True, variant=None):
    """Import one STL with its sidecar sockets and fits (no snapping).
    variant: (index, record) - bring it in as that variant of the part (the
    mesh moved by the record's align, the record's own sockets and fits).
    Returns (new objects, meshes, unit scale, sockets made, types added)."""
    ctx = bpy.context
    scene, view_layer = ctx.scene, ctx.view_layer
    override = _view3d_override()
    before = set(bpy.data.objects)
    with ctx.temp_override(**override):
        bpy.ops.wm.stl_import('EXEC_DEFAULT', filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    if not new:
        raise ValueError(f"importer created nothing from {os.path.basename(path)}")
    whole = read_sidecar(path)
    vrec = variant[1] if variant else None
    if vrec is not None:
        Tv = variant_align(vrec)
        for ob in new:
            if ob.type == 'MESH':
                ob.data.transform(Tv)
                if Tv.determinant() < 0:
                    ob.data.flip_normals()
                ob.data.update()

    # Default is 1:1 - one STL unit per Blender unit - because that is how
    # existing kitbash files were built (scenes left at metres, parts
    # imported by hand), and a converted part would arrive 1000x too small
    # next to them. The option converts mm to scene units for files set up
    # the Part Sockets way. Applied to the mesh, not the object, so no
    # stray object scale follows the part into Part Sockets.
    s = 1.0
    if prefs.millimetres and scene.unit_settings.scale_length > 0:
        s = 0.001 / scene.unit_settings.scale_length

    coll = None
    if prefs.by_category and collection:
        name = str(job.get("category") or "").strip() or prefs.fallback_collection
        coll = _target_collection(scene, view_layer, name[:63])

    cursor = scene.cursor.location.copy()
    side = whole
    if vrec is not None:
        side = vrec.get("sidecar") if isinstance(vrec.get("sidecar"), dict) else {}
    orig = (whole or {}).get("original") if isinstance((whole or {}).get("original"), dict) else {}
    # a creator's own scale for the whole kit (Springles at Josh's 110%): applied
    # to the mesh like the unit, and the sidecar's sockets and fits are in the
    # scaled file's coordinates
    k = 1.0
    try:
        k = float((side or {}).get("scale") or 1.0)
    except (TypeError, ValueError):
        k = 1.0
    for ob in new:
        if ob.type == 'MESH' and abs(s * k - 1.0) > 1e-12:
            ob.data.transform(Matrix.Scale(s * k, 4))
        if abs(k - 1.0) > 1e-12:
            ob["tiow_scale"] = k
        if (side or {}).get("noPad"):
            # the arm's own pauldron is part of it (Springles' heresy arms): no Pad anchor
            ob["tiow_nopad"] = True
        ex = (side or {}).get("exact")
        if isinstance(ex, list) and ex:
            # fits you corrected by hand (Save Correction): placed exactly, no rocking or settling
            ob["tiow_exact"] = json.dumps([str(t) for t in ex])
        if (side or {}).get("noHand"):
            # the arm's hand is part of it, holding its weapon or grip (CyberBrush): no wrist socket
            ob["tiow_nohand"] = True
        oh = (side or {}).get("offHand")
        if isinstance(oh, list) and len(oh) == 16:
            # a gun held in both hands: where its other hand's wrist is (part coordinates)
            ob["tiow_offhand"] = [float(x) * (s if i in (3, 7, 11) else 1.0) for i, x in enumerate(oh)]
        pv = (side or {}).get("pivot")
        if isinstance(pv, list) and len(pv) == 3:
            # the point it turns about in the hand it is held by (Springles: the wrist dome's tip)
            ob["tiow_pivot"] = [float(x) * s for x in pv]
        if coll is not None:
            for c in list(ob.users_collection):
                c.objects.unlink(ob)
            coll.objects.link(ob)
        if prefs.placement != 'FILE':
            ob.location = cursor
            if prefs.placement == 'BOUNDS' and ob.type == 'MESH' \
                    and ob.data.vertices:
                # centre the geometry on the cursor and leave the origin
                # where the file had it - Part Sockets sets the real one
                lo = Vector(ob.bound_box[0])
                hi = Vector(ob.bound_box[6])
                ob.location = cursor - ob.matrix_world.to_3x3() @ ((lo + hi) * 0.5)
        ob["tiow_src"] = path
        ob["tiow_unit"] = s
        if job.get("category"):
            ob["tiow_category"] = str(job["category"])
        if job.get("itemId"):
            ob["tiow_item"] = str(job["itemId"])
        if job.get("name"):
            ob["tiow_name"] = str(job["name"])
        # the names the snap rules read: the file's own from before any
        # library rename (its sockets file keeps them), or the variant's
        stem = os.path.splitext(os.path.basename(path))[0]
        if vrec is not None:
            ob["tiow_variant"] = int(variant[0])
            ob["tiow_orig"] = str(vrec.get("name") or stem)
            ob["tiow_folder"] = str(vrec.get("folder") or os.path.basename(os.path.dirname(path)))
            ob.name = str(vrec.get("title") or vrec.get("name") or stem)[:63]
        else:
            ob["tiow_orig"] = str(orig.get("name") or stem)
            ob["tiow_folder"] = str(orig.get("folder") or os.path.basename(os.path.dirname(path)))

    # A part lifted out of a kitbash file carries its sockets next to it.
    made, added = [], []
    meshes = [o for o in new if o.type == 'MESH']
    up = (side or {}).get("upright")
    if isinstance(up, list) and len(up) == 16 and len(meshes) == 1:
        # exported lying down or Y-up (Turtle Ninja's torsos): stand it up in the
        # Mar Fil kit frame (Z up, facing +Y), so a model built on it stands too
        ob = meshes[0]
        U = Matrix((up[0:4], up[4:8], up[8:12], up[12:16]))
        U.translation = U.translation * s
        if prefs.placement == 'FILE':
            ob.matrix_world = U
        else:
            lo = Vector(ob.bound_box[0]); hi = Vector(ob.bound_box[6])
            pivot = (lo + hi) * 0.5 if prefs.placement == 'BOUNDS' else Vector((0.0, 0.0, 0.0))
            R = U.to_3x3().to_4x4()
            ob.matrix_world = Matrix.Translation(cursor - R.to_3x3() @ pivot) @ R
    if side and len(meshes) == 1:
        added = ensure_types(scene, side.get("types"))
        made = rebuild_sockets(meshes[0], side, s, coll)
        for tname, m in (side.get("fits") or {}).items():
            if isinstance(m, list) and len(m) == 16:
                fit = Matrix((m[0:4], m[4:8], m[8:12], m[12:16]))
                fit.translation = fit.translation * s
                meshes[0][f"ws_fit::{tname}"] = [x for row in fit for x in row]
    if len(meshes) == 1 and vrec is None:
        # (a variant's folder fits were folded into its own sockets file)
        apply_folder_fits(meshes[0], path, s)
    return new, meshes, s, made, added


def import_request(job, prefs):
    """Import one request. Returns the new objects, or raises ValueError."""
    if job.get("category") or job.get("path"):
        job["category"] = part_category(job) or job.get("category")
    path = str(job.get("path", ""))
    if not path.lower().endswith(".stl"):
        raise ValueError(f"not an STL: {os.path.basename(path) or '?'}")
    if not os.path.isfile(path):
        raise ValueError(f"file not found: {path}")

    ctx = bpy.context
    view_layer = ctx.view_layer
    override = _view3d_override()
    # the model to snap onto: whatever was active when the part arrived
    focus = view_layer.objects.active
    if focus is not None and not focus.select_get():
        focus = None
    # a request from the Squad Builder names its model (and the socket the part
    # goes on), so a whole squad builds in one send whatever is selected
    model = str(job.get("model") or "")
    model_root = None
    if model:
        model_root = model_by_id(model)
        focus = None
        if model_root is not None:
            want = str(job.get("socket") or "")
            if want:
                _j, aliases = library_table(path)
                names = [want] + list(aliases.get(want) or [])
                focus = next((o for o in [model_root] + list(_descendants(model_root))
                              if o.get("ws_type") in names), None)
                if focus is None and want[-2:] in (" R", " L"):
                    # not there yet (a wing's socket comes with its connector): keep the side asked for
                    job["_side"] = want[-1]
            focus = focus or model_root
    # one file, both sides: the variant for the side it's going on
    data = read_sidecar(path) or {}
    vi = job.get("_variant")
    if vi is None and prefs.auto_snap and not job.get("_nosnap"):
        try:
            vi = pick_variant(job, data, focus)
        except Exception as exc:          # never let the side choice stop an import
            print("[TIOW Inbox] variant choice failed:", repr(exc))
            vi = None
    vrec = None
    if isinstance(vi, dict):              # a mirror made on the spot (Mirror)
        vrec, vi = vi, int(vi.get("_index", -1))
    elif isinstance(vi, int) and vi >= 0:
        vs = part_variants(data)
        vrec = vs[vi] if vi < len(vs) and isinstance(vs[vi], dict) else None
    orig = data.get("original") if isinstance(data.get("original"), dict) else {}
    if vrec is not None:
        job["_rname"] = str(vrec.get("name") or "")
        job["_folder"] = str(vrec.get("folder") or "")
    else:
        if orig.get("name"):
            job["_rname"] = str(orig["name"])
        if orig.get("folder"):
            job["_folder"] = str(orig["folder"])
    new, meshes, s, made, added = load_stl(path, job, prefs, variant=(vi, vrec) if vrec is not None else None)
    if model and len(meshes) == 1:
        meshes[0]["tiow_model"] = model
        if model_root is None:
            # the model's first part (its torso) is its root: where the builder put it
            meshes[0]["tiow_model_root"] = True
            at = job.get("at")
            if isinstance(at, (list, tuple)) and len(at) == 3:
                try:
                    R = meshes[0].matrix_world.to_3x3().to_4x4()
                    meshes[0].matrix_world = Matrix.Translation(Vector([float(x) * s for x in at])) @ R
                except (TypeError, ValueError):
                    pass
    found = ""
    if len(meshes) == 1:
        cat = str(job.get("category") or "")
        try:
            if cat == "Legs" and "ws_fit::Flat Waist" not in meshes[0].keys():
                # shin pads go on Mar Fil legs (Marta's flat legs come without the shin holes)
                found = auto_shin_anchors(meshes[0])
            elif str((library_table(path)[0].get(cat) or {}).get("socket")) == "Shoulder":
                got = copy_pad_anchor(meshes[0])
                found = f", {got}" if got else ""
                wrist = rule_wrist_socket(meshes[0])
                found += f", {wrist}" if wrist else ""
        except Exception as exc:          # never let a shape search stop an import
            print("[TIOW Inbox] anchor search failed:", repr(exc))
            found = f", anchor search failed ({type(exc).__name__}: {exc})"
    job["_found"] = found
    job["_sockets"], job["_types"], job["_unit"] = len(made), added, s
    job["_snap"] = ""
    if job.get("_nosnap"):
        return new
    if prefs.auto_snap and len(meshes) == 1:
        job["_snap"] = auto_snap(meshes[0], job, prefs, focus)

    for o in view_layer.objects:
        if o is not None and o.select_get():
            o.select_set(False)
    for ob in new:
        if view_layer.objects.get(ob.name) is not None:
            ob.select_set(True)
    if view_layer.objects.get(new[0].name) is not None:
        view_layer.objects.active = new[0]

    # one undo step per import, so Ctrl+Z takes the part back out
    try:
        with ctx.temp_override(**override):
            bpy.ops.ed.undo_push(message=f"TIOW import {new[0].name}")
    except (RuntimeError, TypeError):
        pass
    return new


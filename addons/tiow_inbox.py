# TIOW Inbox - import STLs sent from TIOW-FTRP into the open Blender scene.
#
# TIOW-FTRP's "Send to Blender" writes one small JSON file per item into
# %LOCALAPPDATA%\TIOW-FTRP\local-data\blender-inbox. This add-on checks that
# folder twice a second. For each request it imports the STL into the scene
# that is open, puts it in a collection named after the TIOW category, places
# it at the 3D cursor, and leaves it selected and active, so Part Sockets can
# work on it straight away.
#
# A part lifted out of a kitbash file (lift_parts_to_library.py) has a
# <part>.sockets.json beside its STL: its sockets and per-part fits are
# rebuilt on import, and any fit types they use that the scene lacks are
# added.
#
# Auto-snap: select the model you are building before you send a part. The
# part goes onto the free socket of its joint in that model (an arm onto
# Shoulder R, a pistol onto Hand R...), using Part Sockets' own snap. If that
# joint is taken, the part already there is swapped out, and anything it was
# holding (a pistol in its hand) moves across to the new part. Which joint
# each part type uses is the "joints" table in your library's _library.json.
#
# A folder is the whole interface: no ports, no threads. If Blender is closed,
# requests wait for a few minutes and are then dropped, so an old click does
# not appear in a file you open days later.
#
# One file, both sides (1.16): a part's mirror copy can live inside its
# .sockets.json as a "variant" instead of as a second STL. Sent from TIOW, the
# part arrives as the variant when it goes on that side (the side you picked,
# or the free one), exactly as the old copy did. Mirror (TIOW panel) flips the
# selected part: an arm or a hand-held part moves to the other side (swapping
# with what is there), legs or a torso flip where they stand.
#
# Squads (1.17): a request from the Squad Builder page names its model (and
# the socket the part goes on), so a whole squad arrives in one send and each
# part goes on its own model whatever is selected. A model's first part (its
# torso) is placed where the builder showed it.
#
# 1.17.1: browsers won't let a page write into AppData, so the Squad Builder
# writes its requests into the library's own _builder\inbox folder; this add-on
# watches that folder as well as TIOW's (pref "Squad Builder Inbox").

bl_info = {
    "name": "TIOW Inbox",
    "author": "Josh",
    "version": (1, 17, 2),
    "blender": (5, 1, 0),
    "location": "View3D > Sidebar > Sockets > TIOW Inbox",
    "description": "Imports STLs sent from TIOW-FTRP (Send to Blender) into "
                   "the open scene",
    "category": "Import-Export",
}

import json
import math
import os
import re
import sys
import time

import bpy
from bpy.props import BoolProperty, EnumProperty, IntProperty, StringProperty
from mathutils import Matrix, Vector

HEARTBEAT = ".listening"     # TIOW reads its age to say "sent" vs "queued"
POLL_SECONDS = 0.5
HEARTBEAT_SECONDS = 3.0

_state = {"last": "", "beat": {}}


def default_inbox():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(base, "TIOW-FTRP", "local-data", "blender-inbox")


def get_prefs():
    addon = bpy.context.preferences.addons.get(__name__)
    return addon.preferences if addon else None


def inbox_dir(prefs):
    return bpy.path.abspath(prefs.inbox_path) if prefs.inbox_path \
        else default_inbox()


def inbox_dirs(prefs):
    """TIOW's inbox, then the Squad Builder's (in the library's _builder folder,
    used only when that _builder folder exists: Prepare made it)."""
    dirs = [inbox_dir(prefs)]
    sb = bpy.path.abspath(prefs.builder_inbox) if getattr(prefs, "builder_inbox", "") else ""
    if sb and os.path.isdir(os.path.dirname(os.path.normpath(sb))) \
            and os.path.normcase(os.path.normpath(sb)) != os.path.normcase(os.path.normpath(dirs[0])):
        dirs.append(sb)
    return dirs


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


# ---------------------------------------------------------------- auto-snap

# Part type -> the joint it goes on. "socket": the socket name, or a list
# of socket names to choose from (belt bits). "sided": the name ends in R or L,
# taken from the part's name ("77-Arm-1-R-B", "Arm_L_03", "LeftOrientated").
# "fit": snap with this fit type's offset on that socket instead of the
# socket's own. "mirrorLeft": a part with no side in its name, going onto a
# left socket, whose folder only has a right-hand fit, is mirrored and placed
# as the mirror image of the right one (Mar Fil's shin pads and pauldrons
# come as right-hand parts; their "...-Mirrored" copies count as lefts).
# Shin and Pad anchors are exact three-point frames, so pads don't settle.
# "rock": before settling, let the part tilt up to this many degrees about
# the anchor so it sits flush on the surface instead of touching at one edge.
# "settle": after snapping, slide the part along this socket axis until it
# touches the model ("-Z" = into the surface for anchors). "touch": stop when
# that percent of the part's inside touches, not at the first touch, so a
# cuff round the knee or a lug can sink in. "sink": then press it in this far
# (mm), so a pad printed with its host merges into it. "pushOut": false =
# settle only closes a gap and never pushes a part off the model.
# "spans": other sockets the part also covers (a two-handed weapon comes
# with both arms: it snaps to Shoulder R and clears Shoulder L, and an arm
# later snapped onto Shoulder L replaces it). "mirrorSides": the part has a
# fit for one side only (Mar Fil's jump-pack fins are left pieces); on the
# other side it is mirrored. Your library's _library.json "joints" replaces
# this table. "Hands" are bare hands (Intercessors V2), on the arm's Hand
# socket like anything held; a hand carries a Grip socket at its wrist, where
# "Hand-less Weapons" (Mar Fil's '...-NoHand' parts) go. "Bikes": the Outrider
# bike's rear body, on the rider's legs (the legs are exported sitting on it);
# it carries one socket per "Bike Parts" piece, each saved for that piece
# (tiow_holds), so a bike part finds its own spot whatever is selected.
# "Cables" go on a Cable socket like the heavy weapons' (the Techmarine's arm
# cables, on their arm); "Servo Arms" and "Mechadendrites" on the Techmarine
# backpack (a servo arm's shoulder ball in its seat). "Two-Handed Held": a
# gun held in both hands with no arms of its own (Turtle Ninja's bolter
# poses): it goes in the right hand, and the left arm of the same pose set
# meets its other grip.
# Waists come in two kinds: Mar Fil's (plug and stomach plating on the legs,
# "Waist") and flat ones (Marta and Turtle Ninja legs, "Flat Waist"). Legs go
# on whichever their fits say ("byFit"). A Mar Fil torso has no Flat Waist, so
# flat legs bring an "adaptor" (a body adaptor from the Adaptors folder in
# Preferences) onto its Waist and stand on the adaptor's Flat Waist. A
# Turtle Ninja torso has both; "exclusive" sockets are alternatives, so legs
# on one replace legs on the other.
BELT = ["Hip R", "Hip L", "Belt Front", "Belt Back"]
BIKE = ["Bike Front", "Front Wing", "Front Wheel", "Rear Wheel", "Exhaust R", "Exhaust L",
        "Handle R", "Handle L", "Bike Guns"]
DEFAULT_JOINTS = {
    "Arms": {"socket": "Shoulder", "sided": True},
    "Two-Handed Guns": {"socket": "Shoulder R", "spans": ["Shoulder L"]},
    "Two-Handed Melee": {"socket": "Shoulder R", "spans": ["Shoulder L"]},
    "Two-Handed Held": {"socket": "Hand R"},
    "Heavy Weapons": {"socket": "Shoulder R", "spans": ["Shoulder L"]},
    "Pistols": {"socket": "Hand", "sided": True},
    "Melee": {"socket": "Hand", "sided": True},
    "Shields": {"socket": "Hand", "sided": True},
    "Hands": {"socket": "Hand", "sided": True},
    "Hand-less Weapons": {"socket": "Grip", "sided": True},
    "Forearm Armour": {"socket": "Forearm", "sided": True, "mirrorLeft": True},
    "Heads": {"socket": "Neck"},
    "Backpacks": {"socket": "Back"},
    "Jump Packs": {"socket": "Back"},
    "Backpack Toppers": {"socket": "Back Top"},
    "Heavy Weapon Cables": {"socket": "Cable"},
    "Cables": {"socket": "Cable"},
    "Servo Arms": {"socket": "Servo Arm"},
    "Mechadendrites": {"socket": "Mechadendrite"},
    "Bikes": {"socket": "Bike"},
    "Bike Parts": {"socket": BIKE},
    "Pack Fins": {"socket": "Pack Fin", "sided": True, "mirrorSides": True},
    "Legs": {"socket": ["Waist", "Flat Waist"], "byFit": True, "exclusive": ["Waist", "Flat Waist"],
             "adaptor": {"Flat Waist": "Waist"}},
    "Adapters": {"socket": "Waist", "exclusive": ["Waist", "Flat Waist"]},
    "Bases": {"socket": "Base"},
    "Shoulder Pads": {"socket": "Pad", "sided": True, "mirrorLeft": True},
    "Knee Pads": {"socket": "Shin", "sided": True, "mirrorLeft": True},
    "Accessories": {"socket": BELT, "rock": 8, "settle": "-Z", "sink": 0.1},
    "Grenades": {"socket": BELT, "rock": 8, "settle": "-Z", "sink": 0.1},
    "Seals": {"socket": BELT, "rock": 8, "settle": "-Z", "sink": 0.1},
    "Trophies": {"socket": BELT, "rock": 8, "settle": "-Z", "sink": 0.1},
}
# Socket names from before the library rename, so library parts also snap
# into files set up the old way.
DEFAULT_ALIASES = {
    "Shoulder R": ["arm__Torso_r"], "Hand R": ["Wrist_socket_r"],
    "Forearm R": ["Wrist_Armout_r"], "Shield R": ["Shield_to_hand_r"],
    "Neck": ["Head"], "Back": ["Backpack"], "Hip R": ["Right Hip"],
    "Hip L": ["Left Hip"], "Belt Front": ["Tabard"],
}
LIBRARY_FILE = "_library.json"
FITS_FILE = "_fits.json"
_lib_cache = {}


def library_table(stl_path):
    """(joints, aliases) from the nearest _library.json above the STL, else the defaults."""
    d = os.path.dirname(os.path.abspath(stl_path))
    for _ in range(12):
        f = os.path.join(d, LIBRARY_FILE)
        if os.path.isfile(f):
            try:
                key = (f, os.path.getmtime(f))
                if key not in _lib_cache:
                    with open(f, encoding="utf-8") as fh:
                        data = json.load(fh)
                    _lib_cache.clear()
                    _lib_cache[key] = (data.get("joints") or DEFAULT_JOINTS,
                                       data.get("jointAliases") or DEFAULT_ALIASES)
                return _lib_cache[key]
            except (OSError, ValueError, AttributeError):
                break
        up = os.path.dirname(d)
        if up == d:
            break
        d = up
    return DEFAULT_JOINTS, DEFAULT_ALIASES


def part_side(*texts):
    """'R', 'L' or None from words in the part's name and folder."""
    words = set()
    for t in texts:
        t = re.sub(r"([a-z])([A-Z])", r"\1 \2", str(t or ""))
        words |= set(re.split(r"[^a-z]+", t.lower()))
    r = bool(words & {"r", "right", "rh"})
    l = bool(words & {"l", "left", "lh"})
    return "R" if r and not l else "L" if l and not r else None


def _part_sockets():
    """Part Sockets' sockets and core modules, wherever it is installed
    (bl_ext.user_default.part_sockets as an extension, part_sockets as a legacy add-on)."""
    sk = co = None
    for n, m in list(sys.modules.items()):
        if n.endswith("part_sockets.sockets") and hasattr(m, "snap_part_to_socket"):
            sk = m
        elif n.endswith("part_sockets.core") and hasattr(m, "detach_part"):
            co = m
    return (sk, co) if sk and co else None


def _descendants(ob):
    for c in ob.children:
        yield c
        yield from _descendants(c)


def _snapped_to(sock, co, among, tname=None):
    """Visible parts sitting on this socket - only those snapped with fit
    type `tname` when given (an arm and its pauldron share a Shoulder socket)."""
    out = []
    for o in among:
        if o.type == 'MESH' and o.get("ws_type") is None and not o.hide_get() \
                and co.snap_socket_of(o) is sock:
            if tname is None or (o.get("ws_snap_type") or sock.get("ws_type")) == tname:
                out.append(o)
    return out


def wanted_sockets(spec, side, aliases):
    base = spec.get("socket")
    if isinstance(base, list):
        names = [str(b) for b in base if b]
        if side:      # this side's sockets first
            names.sort(key=lambda n: 0 if n.endswith(" " + side) else 1)
    elif not base:
        return []
    elif spec.get("sided"):
        names = [f"{base} {side}"] if side else [f"{base} R", f"{base} L"]
    else:
        names = [str(base)]
    out = []
    for n in names:
        out.append(n)
        out += [a for a in aliases.get(n, []) if a not in out]
    return out


def _fit_of_fn(spec, side):
    """fit_of(socket): the fit type a part of this kind uses on that socket."""
    def fit_of(sock):
        st = str(sock.get("ws_type"))
        if not spec.get("fit"):
            return st
        if not spec.get("sided"):
            return str(spec["fit"])
        end = st.rsplit(" ", 1)[-1]
        return f"{spec['fit']} {end if end in ('R', 'L') else (side or 'R')}"
    return fit_of


def choose_socket(names, focus, co, view_layer, fit_of, prefer=None):
    """The socket to snap onto in the model around `focus` (what was selected
    before the import), and the part of the same kind already on it.
    `fit_of(socket)` is the fit type the new part would use there. `prefer`:
    the new part's name (or a set of names) - a free anchor saved where its
    maker put that part (tiow_holds) is used before the others.
    Returns (socket, part_on_it_or_None) or (None, None)."""
    if focus is None:
        return None, None
    pref = {prefer} if isinstance(prefer, str) else set(prefer or ())

    def order(o):
        held = 0 if pref & _holds(o) else 1
        return (held, names.index(o["ws_type"]), o.name)
    # a selected socket, or a selected part of the same kind on a matching socket, wins
    if focus.get("ws_type") in names:
        on = _snapped_to(focus, co, view_layer.objects, fit_of(focus))
        return focus, (on[0] if on else None)
    if focus.type == 'MESH':
        s = co.snap_socket_of(focus)
        if s is not None and s.get("ws_type") in names and \
                (focus.get("ws_snap_type") or s.get("ws_type")) == fit_of(s):
            return s, focus
    # the selected part's own sockets next (select a left hand, the weapon
    # goes in that hand), then the rest of the model
    root = focus
    while root.parent is not None:
        root = root.parent
    if focus.type == 'MESH' and focus is not root:
        own = sorted((c for c in focus.children if c.get("ws_type") in names), key=order)
        if own:
            members = [root] + list(_descendants(root))
            for s in own:
                on = _snapped_to(s, co, members, fit_of(s))
                if not on:
                    return s, None
            on = _snapped_to(own[0], co, members, fit_of(own[0]))
            return own[0], (on[0] if on else None)
    root = focus
    while root.parent is not None:
        root = root.parent
    socks = [o for o in _descendants(root) if o.get("ws_type") in names]
    if not socks:
        return None, None
    socks.sort(key=order)
    members = [root] + list(_descendants(root))
    taken = None
    for s in socks:
        on = _snapped_to(s, co, members, fit_of(s))
        if not on:
            return s, None
        if taken is None:
            taken = (s, on[0])
    return taken


def _world_tris(ob, deps):
    """World-space vertices and triangles of the evaluated mesh."""
    import numpy as np
    eo = ob.evaluated_get(deps)
    me = eo.to_mesh()
    try:
        me.calc_loop_triangles()
        v = np.empty(len(me.vertices) * 3, np.float64)
        me.vertices.foreach_get("co", v)
        t = np.empty(len(me.loop_triangles) * 3, np.int32)
        me.loop_triangles.foreach_get("vertices", t)
    finally:
        eo.to_mesh_clear()
    mw = np.array(ob.matrix_world)
    v = v.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]
    return v, t.reshape(-1, 3)


# ---------------------------------------------------------------- bases settle onto the feet
# The legs' Base socket says where the ground is; a base whose top is lower
# than the soles there (a recessed or textured top) would leave the model
# floating. Heightfields on a 0.5 mm grid in the socket's frame - the legs'
# lowest surface and the base's top, from points spread over the triangles -
# give how far the base must rise for the lowest foot to touch it. A base is
# only ever raised (feet already on or in a scenic base stay as they are), and
# by BASE_SINK more, so the feet sit just into it for printing. The Squad
# Builder page does the same sums on its preview meshes.
BASE_CELL, BASE_STEP, BASE_LOW_BAND, BASE_SINK, BASE_MAX_RISE = 0.5, 0.25, 1000.0, 0.2, 25.0   # the whole legs: a foot up on a tall rock counts too


def _surface_points(P):
    """Triangles (n, 3, 3) -> points over them about BASE_STEP apart."""
    import numpy as np
    if not len(P):
        return np.zeros((0, 3))
    e = np.max(np.stack([np.linalg.norm(P[:, 1] - P[:, 0], axis=1), np.linalg.norm(P[:, 2] - P[:, 1], axis=1),
                         np.linalg.norm(P[:, 0] - P[:, 2], axis=1)]), axis=0)
    k = np.clip(np.ceil(e / BASE_STEP), 1, 60).astype(int)
    out = []
    for kk in np.unique(k):
        sel = P[k == kk]
        w = np.array([(i / kk, j / kk) for i in range(kk + 1) for j in range(kk + 1 - i)])
        u, v = w[:, 0][None, :, None], w[:, 1][None, :, None]
        out.append((sel[:, None, 0] + u * (sel[:, None, 1] - sel[:, None, 0]) + v * (sel[:, None, 2] - sel[:, None, 0])).reshape(-1, 3))
    return np.concatenate(out)


def _height_field(pts, lowest):
    import numpy as np
    c = np.floor(pts[:, :2] / BASE_CELL).astype(np.int64)
    key = c[:, 0] * 100003 + c[:, 1]
    order = np.argsort(key, kind="stable")
    key, z = key[order], pts[order, 2]
    uk, start = np.unique(key, return_index=True)
    red = (np.minimum if lowest else np.maximum).reduceat(z, start)
    return dict(zip(uk.tolist(), red.tolist()))


def base_gap(legs_tris, base_tris):
    """Both (n, 3, 3) in the Base socket's frame. How far the base must rise
    for the lowest foot to touch it (negative: the feet are already on or in
    it), or None when no foot is over the base."""
    import numpy as np
    if not len(legs_tris) or not len(base_tris):
        return None
    zl = legs_tris[:, :, 2].min()
    low = legs_tris[legs_tris[:, :, 2].min(axis=1) < zl + BASE_LOW_BAND]
    lo, hi = low[:, :, :2].reshape(-1, 2).min(axis=0) - 1.0, low[:, :, :2].reshape(-1, 2).max(axis=0) + 1.0
    bx = base_tris[:, :, :2]
    near = base_tris[np.all(bx.max(axis=1) >= lo, axis=1) & np.all(bx.min(axis=1) <= hi, axis=1)]
    if not len(near):
        return None
    sole = _height_field(_surface_points(low), True)
    top = _height_field(_surface_points(near), False)
    common = sole.keys() & top.keys()
    if not common:
        return None
    return float(min(sole[k] - top[k] for k in common))


def settle_base(base, sock):
    """Raise a base along its Base socket's Z until the lowest foot of the legs
    holding the socket touches it (plus BASE_SINK). Returns the rise in mm."""
    import numpy as np
    legs = sock.parent
    if legs is None or legs.type != 'MESH' or base.type != 'MESH':
        return 0.0
    deps = bpy.context.evaluated_depsgraph_get()
    F = np.array(sock.matrix_world)
    Fi = np.linalg.inv(F)
    def local(ob):
        v, t = _world_tris(ob, deps)
        v = v @ Fi[:3, :3].T + Fi[:3, 3]
        return v[t]
    unit = float(base.get("tiow_unit", 1.0)) or 1.0
    gap = base_gap(local(legs), local(base))
    if gap is None or gap <= -BASE_SINK * unit or gap > BASE_MAX_RISE * unit:
        return 0.0
    rise = gap + BASE_SINK * unit
    z = Vector(F[:3, 2]).normalized()
    base.matrix_world = Matrix.Translation(z * rise) @ base.matrix_world
    base["tiow_base_rise"] = rise
    bpy.context.view_layer.update()
    return rise


def _touch_depth(pv, pt, others, d, back, reach, frame, touch, deps):
    """Travel (from `back` behind the part) at which `touch` percent of the
    part's inner side has met the model, or None if too little of it is
    over the model at all."""
    import numpy as np
    from mathutils.bvhtree import BVHTree
    loc, rot, _s = frame.decompose()
    A = np.array(rot.to_matrix())
    inner = inner_side(pv, pt, A, np.array(loc), samples=400)
    if inner is None:
        return None
    start = inner - np.array(d) * back
    dist = np.full(len(start), np.inf)
    for ob in others:
        if ob is None or ob.type != 'MESH':
            continue
        ov, ot = _world_tris(ob, deps)
        if not len(ot):
            continue
        tb = BVHTree.FromPolygons(ov.tolist(), ot.tolist())
        for i, p in enumerate(start):
            hit = tb.ray_cast(Vector(p), d, reach)
            if hit[0] is not None and hit[3] < dist[i]:
                dist[i] = hit[3]
    dist = dist[np.isfinite(dist)]
    if len(dist) < max(10, len(start) // 5):
        return None
    return float(np.percentile(dist, touch))


def settle_onto(part, others, direction, sink=0.0, samples=4000, push_out=True,
                touch=0.0, frame=None, bias=None, dry=False):
    """Slide `part` along `direction` until it touches any of `others`.
    Contact is the shortest travel over the whole part, not one ray: rays
    go from the part's vertices along the direction into the model, and from
    the model's vertices back into the part. Returns the distance moved, or
    None if nothing is in the way. push_out=False: only close a gap - a part
    that already overlaps the model is left where it is (pauldrons overlap
    the arm by design: the arm's shoulder sits inside them). touch (percent)
    with frame (the anchor): stop when that much of the part's inner side
    touches rather than at the first touch, so a lug or a cuff round the knee
    can sink into the model. bias: the travel measured the same way when the
    fit was saved - the part then moves only by the difference, so on the
    model you saved the fit on it stays exactly where you put it (no sink).
    dry: just return the travel to contact, don't move anything."""
    import numpy as np
    from mathutils.bvhtree import BVHTree
    d = Vector(direction).normalized()
    deps = bpy.context.evaluated_depsgraph_get()
    pv, pt = _world_tris(part, deps)
    if not len(pt):
        return None
    dn = np.array(d)
    # start clear of the model: back off by twice the part's own depth along
    # d, so a part that arrives buried in the model still starts outside it
    depth = float((pv @ dn).max() - (pv @ dn).min())
    back = 2.0 * depth + 1.0
    pv0 = pv - dn * back
    pb = BVHTree.FromPolygons(pv0.tolist(), pt.tolist())
    lo, hi = pv0.min(0) - 0.5, pv0.max(0) + 0.5
    # lateral window: anything outside the part's shadow along d can't be hit
    a = np.array([1.0, 0, 0]) if abs(dn[0]) < 0.9 else np.array([0, 1.0, 0])
    u = np.cross(dn, a); u /= np.linalg.norm(u); w = np.cross(dn, u)
    pu, pw = pv0 @ u, pv0 @ w
    box = (pu.min() - 0.2, pu.max() + 0.2, pw.min() - 0.2, pw.max() + 0.2)
    reach = back + depth + 50.0
    rng = np.random.default_rng(0)
    best = None
    if touch and frame is not None:
        best = _touch_depth(pv, pt, others, d, back, reach, frame, float(touch), deps)
    own = pv0 if best is None else pv0[:0]
    if best is None and not len(own):
        return None
    pick = own if len(own) <= samples else own[rng.choice(len(own), samples, replace=False)]
    for ob in (others if len(pick) else ()):
        if ob is None or ob.type != 'MESH':
            continue
        ov, ot = _world_tris(ob, deps)
        if not len(ot):
            continue
        ou, ow = ov @ u, ov @ w
        near = (ou > box[0]) & (ou < box[1]) & (ow > box[2]) & (ow < box[3])
        if not near.any():
            continue
        tb = BVHTree.FromPolygons(ov.tolist(), ot.tolist())
        for p in pick:
            hit = tb.ray_cast(Vector(p), d, reach)
            if hit[0] is not None and (best is None or hit[3] < best):
                best = hit[3]
        cand = ov[near]
        if len(cand) > samples:
            cand = cand[rng.choice(len(cand), samples, replace=False)]
        for q in cand:
            hit = pb.ray_cast(Vector(q), -d, reach)
            if hit[0] is not None and (best is None or hit[3] < best):
                best = hit[3]
    if best is None:
        return None
    if dry:
        return best - back
    move = best - back + sink if bias is None else best - back - float(bias)
    if not push_out and move < 0.0:
        return 0.0
    part.matrix_world = Matrix.Translation(d * move) @ part.matrix_world
    return move


def _remove_part(ob):
    """Delete a TIOW-imported part with its own socket empties."""
    for c in list(ob.children):
        if c.type == 'EMPTY' and c.get("ws_type") is not None and not \
                [g for g in c.children if g.type == 'MESH']:
            bpy.data.objects.remove(c)
    me = ob.data if ob.type == 'MESH' else None
    bpy.data.objects.remove(ob)
    if me is not None and me.users == 0:
        bpy.data.meshes.remove(me)


def _fit_matrix(e, scale=1.0):
    m = e.get("m") if isinstance(e, dict) else e
    if not isinstance(m, list) or len(m) != 16:
        return None
    M = Matrix((m[0:4], m[4:8], m[8:12], m[12:16]))
    M.translation = M.translation * scale
    return M


def read_folder_fits(stl_path):
    """_fits.json beside the STL: one fit per joint for every part in that
    folder, saved once with Save Fit for Folder."""
    try:
        with open(os.path.join(os.path.dirname(str(stl_path)), FITS_FILE), encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def apply_folder_fits(part, stl_path, scale):
    """Per-part fits from the folder's _fits.json (a part's own sidecar fit wins)."""
    used = []
    for tname, e in read_folder_fits(stl_path).items():
        M = _fit_matrix(e, scale)
        if M is None or f"ws_fit::{tname}" in part.keys():
            continue
        part[f"ws_fit::{tname}"] = [x for row in M for x in row]
        if isinstance(e, dict) and ("rock" in e or "slide" in e):
            part[f"tiow_bias::{tname}"] = json.dumps({k: e[k] for k in ("rock", "slide") if k in e})
        used.append(tname)
    return used


def inner_side(pv, pt, A, piv, samples=220):
    """Points on the part's inner side: what the model sees looking out at
    the part along the anchor's Z (rays from behind the part onto it), so
    undercuts in the decoration on the outer face don't count."""
    import numpy as np
    from mathutils.bvhtree import BVHTree
    L = (pv - piv) @ A
    lo, hi = L.min(0), L.max(0)
    xs = np.linspace(lo[0], hi[0], 26)[1:-1]
    ys = np.linspace(lo[1], hi[1], 26)[1:-1]
    tree = BVHTree.FromPolygons(pv.tolist(), pt.tolist())
    z_dir = Vector(A[:, 2])
    out = []
    for x in xs:
        for y in ys:
            o = piv + A @ np.array([x, y, lo[2] - 1.0])
            hit = tree.ray_cast(Vector(o), z_dir, float(hi[2] - lo[2]) + 2.0)
            if hit[0] is not None:
                out.append(np.array(hit[0]))
    if len(out) < 10:
        return None
    out = np.array(out)
    if len(out) > samples:
        out = out[np.random.default_rng(0).choice(len(out), samples, replace=False)]
    return out


def rock_settle(part, hosts, frame, span=15.0, samples=220, bias=None, dry=False):
    """Tilt the part about the anchor point (up to `span` degrees about each
    of the anchor's axes) to where its inner side sits most flush on the
    hosts without cutting in. The slide along the anchor afterwards does the
    final contact. bias: the tilt it wanted (in the anchor's axes) when the
    fit was saved - only the difference is applied, so on the model you saved
    the fit on the part stays exactly where you put it. dry: return the tilt
    it wants (anchor axes, 3x3) without moving anything. Returns the angle
    turned, in degrees."""
    import numpy as np
    from mathutils.bvhtree import BVHTree
    deps = bpy.context.evaluated_depsgraph_get()
    pv, pt = _world_tris(part, deps)
    if not len(pt) or not hosts:
        return 0.0
    loc, rot, _s = frame.decompose()
    A = np.array(rot.to_matrix())
    piv = np.array(loc)
    inner = inner_side(pv, pt, A, piv, samples)
    if inner is None:
        return 0.0
    trees = []
    for h in hosts:
        if h is None or h.type != 'MESH':
            continue
        mw = h.matrix_world
        trees.append((BVHTree.FromObject(h, deps), np.array(mw.inverted_safe()), mw))
    if not trees:
        return 0.0

    def signed(W):
        best = np.full(len(W), 9.0)
        for tree, inv, mw in trees:
            Lh = W @ inv[:3, :3].T + inv[:3, 3]
            for i, q in enumerate(Lh):
                hit = tree.find_nearest(Vector(q), 5.0)
                if hit[0] is None:
                    continue
                sd = (Vector(q) - hit[0]).dot(hit[1])
                if sd < best[i]:
                    best[i] = sd
        return best

    def R3(ax, deg):
        return np.array(Matrix.Rotation(math.radians(deg), 3, Vector(ax)))

    def score(Rw):
        # as it sits now: cutting in costs a lot, and the closest third of the
        # inner side should sit close. Anything already deep in the model (a
        # cuff round the knee, a lug in a socket) counts as a gap, so it
        # neither pulls the part in nor pushes it away.
        W = (inner - piv) @ Rw.T + piv
        sd = signed(W)
        sd[(sd >= 9.0) | (sd < -1.5)] = 2.0
        cut = np.clip(-sd, 0, None); gap = np.clip(sd, 0, 2.0)
        near = np.sort(gap)[:max(1, len(gap) // 3)]
        return 25 * cut.mean() + near.mean() + 0.2 * gap.mean()

    # tip forward/back (about X) and side to side (about Y); never spun about
    # Z, which would turn it out of line with the anchor
    best_R = np.eye(3); best = score(best_R)
    for sp, st in ((span, span / 6.0), (span / 6.0, span / 30.0)):
        base = best_R.copy()
        steps = np.arange(-sp, sp + 1e-9, st)
        for a in steps:
            for b in steps:
                Rw = A @ (R3((1, 0, 0), a) @ R3((0, 1, 0), b)) @ A.T @ base
                sc = score(Rw)
                if sc < best - 1e-9:
                    best, best_R = sc, Rw
    if dry:
        return (A.T @ best_R @ A).tolist()
    if bias is not None:
        B = np.array(bias, float).reshape(3, 3)
        best_R = A @ (A.T @ best_R @ A) @ B.T @ A.T
    if np.allclose(best_R, np.eye(3)):
        return 0.0
    M3 = Matrix(best_R.tolist()).to_4x4()
    T = Matrix.Translation(Vector(piv)) @ M3 @ Matrix.Translation(-Vector(piv))
    part.matrix_world = T @ part.matrix_world
    return math.degrees(Matrix(best_R.tolist()).to_quaternion().angle)


def _occupants(sock, co, view_layer, own_type_only=False, skip=()):
    t = sock.get("ws_type") if own_type_only else None
    return [o for o in _snapped_to(sock, co, view_layer.objects, t) if o not in skip]


def _model_around(sock, levels=1):
    """The part a socket is on (and, with levels > 1, the parts it hangs
    from). Pads rest on the part their anchor is on: a pauldron on the arm,
    a shin pad on the legs, a pouch on the belt."""
    out, ob = [], sock.parent
    while ob is not None and len(out) < levels:
        if ob.type == 'MESH' and ob.get("ws_type") is None:
            out.append(ob)
        ob = ob.parent
    return out


def _bias_of(part, tname):
    """How the settle judged the by-eye placement the fit was saved from."""
    try:
        b = json.loads(part.get(f"tiow_bias::{tname}", "{}"))
        return b if isinstance(b, dict) else {}
    except (TypeError, ValueError):
        return {}


def _settle_axis(spec):
    a = str(spec.get("settle", "")).upper()
    if not a or a[-1] not in "XYZ":
        return None
    axis = Vector({"X": (1, 0, 0), "Y": (0, 1, 0), "Z": (0, 0, 1)}[a[-1]])
    return -axis if a.startswith("-") else axis


def _part_key(part):
    """The part's file name without extension as its maker named it (before a
    library rename; a variant's own), or its name if it has no file."""
    if part.get("tiow_orig"):
        return str(part["tiow_orig"])
    src = str(part.get("tiow_src") or "")
    return os.path.splitext(os.path.basename(src))[0] if src else part.name


def _pname(part):
    """The name the snap rules read: the maker's file name (see _part_key)."""
    return str(part.get("tiow_orig") or part.name)


def _pfolder(part):
    """The folder the maker had the part in (the variant's own for a variant)."""
    if part.get("tiow_folder"):
        return str(part["tiow_folder"])
    return os.path.basename(os.path.dirname(str(part.get("tiow_src", ""))))


def _holds(sock):
    """The parts an anchor was saved for (tiow_holds: file names, '|' between
    alternatives for the same spot, e.g. the Outrider bike's two gun mounts)."""
    return {h.strip() for h in str(sock.get("tiow_holds") or "").split("|") if h.strip()}


def place_on(part, sock, spec, tname, unit, sk, co, skip=()):
    """Snap, rock flush, then settle. Returns (note, error). An anchor saved
    where its maker put one particular part (tiow_holds: that part's file
    name - Mar Fil's Chaplain belt bits) takes that part exactly there."""
    ctx = bpy.context
    err, _ = sk.snap_part_to_socket(ctx, part, sock, tname=tname)
    if err:
        return "", err
    if _part_key(part) in _holds(sock):
        return ", where the kit puts it", None
    try:
        exact = json.loads(part.get("tiow_exact", "[]"))
    except (TypeError, ValueError):
        exact = []
    if (tname or sock.get("ws_type")) in exact:
        return ", as you corrected it", None
    note = ""
    if sock.get("ws_type") == "Base" and str(part.get("tiow_category") or "") == "Bases":
        try:
            rise = settle_base(part, sock)
            if rise > 0.05:
                note += f", raised {rise:.1f} mm to meet the feet"
        except Exception as exc:          # never let it spoil a snap
            print("[TIOW Inbox] base settle failed:", repr(exc))
    hosts = _model_around(sock)
    bias = _bias_of(part, tname or sock.get("ws_type"))
    turned = meet_off_hand(part, sock, tname or str(sock.get("ws_type", "")))
    if turned:
        note += turned
    if spec and spec.get("rock"):
        turned = rock_settle(part, hosts, sock.matrix_world, float(spec["rock"]), bias=bias.get("rock"))
        if turned > 0.5:
            note += f", tilted {turned:.0f} deg to sit flush"
    axis = _settle_axis(spec) if spec else None
    if axis is not None:
        others = hosts + _occupants(sock, co, ctx.view_layer, False, (part,) + tuple(skip))
        moved = settle_onto(part, others, sock.matrix_world.to_3x3() @ axis,
                            sink=float(spec.get("sink", 0.0)) * unit,
                            push_out=bool(spec.get("pushOut", True)),
                            touch=float(spec.get("touch") or 0.0), frame=sock.matrix_world,
                            bias=None if bias.get("slide") is None else float(bias["slide"]) * unit)
        if moved:
            note += ", settled onto the model"
    return note, None


def meet_off_hand(part, sock, tname):
    """A gun held in both hands whose hands sit on ball wrists (Springles):
    after it goes in one hand, turn it about that wrist so its other hand
    reaches the model's other wrist as nearly as it can, both hands lying
    along their forearms. Returns a note."""
    import numpy as np
    oh = part.get("tiow_offhand")
    if oh is None or len(oh) != 16 or not tname.startswith("Hand "):
        return ""
    other = "Hand L" if tname.endswith("R") else "Hand R"
    root = sock
    while root.parent is not None:
        root = root.parent
    cands = [o for o in _descendants(root) if o.get("ws_type") == other]
    if not cands:
        return ""
    W = np.array(part.matrix_world)
    pv = part.get("tiow_pivot")
    O = (W @ np.array(list(pv) + [1.0]))[:3] if pv is not None and len(pv) == 3 else np.array(sock.matrix_world.translation)
    H = W @ np.array(oh, float).reshape(4, 4)               # off-hand wrist now (world)
    p = H[:3, 3]
    tgt = min(cands, key=lambda o: np.linalg.norm(np.array(o.matrix_world.translation) - p))
    T = np.array(tgt.matrix_world)
    q = T[:3, 3]
    if np.linalg.norm(p - O) < 1e-6 or np.linalg.norm(q - O) < 1e-6:
        return ""
    unit = lambda v: v / (np.linalg.norm(v) + 1e-12)
    S = np.array(sock.matrix_world)
    src = [unit(p - O), unit(H[:3, 1]), unit(S[:3, 1])]
    dst = [unit(q - O), unit(T[:3, 1]), unit(S[:3, 1])]
    wts = [4.0, 1.0, 1.0]
    # the grip hand keeps lying along its forearm: its axis (the socket's Y in
    # the part) is one of the pairs, in the part's current pose
    B = sum(w * np.outer(d, a) for w, a, d in zip(wts, src, dst))
    U, _sv, Vt = np.linalg.svd(B)
    R = U @ np.diag([1.0, 1.0, np.sign(np.linalg.det(U @ Vt))]) @ Vt
    ang = math.degrees(math.acos(max(-1.0, min(1.0, (np.trace(R) - 1) / 2))))
    before = np.linalg.norm(p - q)
    after = np.linalg.norm(R @ (p - O) + O - q)
    unit_mm = float(part.get("tiow_unit", 1.0)) or 1.0
    # only when the hands can actually meet (a two-handed gun on, say, a pair
    # of melee arms stays upright in the right hand)
    if ang < 0.5 or after > before - 0.05 or after > 3.0 * unit_mm:
        return ""
    M = np.eye(4)
    M[:3, :3] = R
    M[:3, 3] = O - R @ O
    part.matrix_world = Matrix(M.tolist()) @ part.matrix_world
    return f", turned {ang:.0f} deg about the wrist to meet the other hand ({after / unit_mm:.1f} mm off)"


def _has_fit(scene, part, tname):
    if f"ws_fit::{tname}" in part.keys():
        return True
    t = next((x for x in scene.ws_types if x.name == tname), None)
    return bool(t and t.captured)


def park_at(part, sock, tname):
    """No fit yet: put the part's middle on the socket so it can be placed by
    eye, and remember the socket for Save Fit for Folder."""
    lo = Vector(part.bound_box[0]); hi = Vector(part.bound_box[6])
    centre = part.matrix_world @ ((lo + hi) * 0.5)
    part.matrix_world = Matrix.Translation(sock.matrix_world.translation - centre) @ part.matrix_world
    part["tiow_target"] = sock.name
    part["tiow_fit_type"] = tname


def _spans_of(ob):
    try:
        v = json.loads(ob.get("tiow_spans", "[]"))
        return v if isinstance(v, list) else []
    except (TypeError, ValueError):
        return []


def _spec_for(ob):
    joints, _ = library_table(ob.get("tiow_src", ""))
    spec = joints.get(str(ob.get("tiow_category") or ""))
    return spec if isinstance(spec, dict) else None


def _model_socket(focus, names):
    """A socket of one of these types in the model around `focus`."""
    if focus is None:
        return None
    if focus.get("ws_type") in names:
        return focus
    root = focus
    while root.parent is not None:
        root = root.parent
    socks = [o for o in _descendants(root) if o.get("ws_type") in names]
    socks.sort(key=lambda o: (names.index(o["ws_type"]), o.name))
    return socks[0] if socks else None


def adaptor_files(prefs):
    """The body adaptors (STLs) in the Adaptors folder, in number order."""
    d = bpy.path.abspath(str(getattr(prefs, "adaptor_dir", "") or ""))
    try:
        names = [f for f in os.listdir(d) if f.lower().endswith(".stl")]
    except OSError:
        return []
    key = lambda f: [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", f)]
    return [os.path.join(d, f) for f in sorted(names, key=key)]


def bring_adaptor(via_sock, prefs, unit, path=None):
    """Import the chosen body adaptor and snap it onto `via_sock` (a Mar Fil
    torso's Waist), replacing what was there. Returns (adaptor, note)."""
    files = adaptor_files(prefs)
    if path is None:
        if not files:
            return None, f" - no body adaptors in {prefs.adaptor_dir or '(Adaptors folder not set)'}"
        i = min(max(int(prefs.adaptor_default), 1), len(files)) - 1
        path = files[i]
    job = {"path": path, "category": "Adapters", "_unit": unit}
    new, meshes, s, made, added = load_stl(path, job, prefs)
    if len(meshes) != 1:
        return None, " - the adaptor file is not one mesh"
    ad = meshes[0]
    note = auto_snap(ad, job, prefs, via_sock)
    if "snapped to" not in note:
        _remove_part(ad)
        return None, f" - adaptor not placed{note}"
    return ad, f", adaptor {os.path.splitext(os.path.basename(path))[0]} added (Next Adaptor swaps it)"


def auto_snap(part, job, prefs, focus):
    """Snap a freshly imported part onto the selected model. Returns a
    short note for the status line ('' if nothing to do)."""
    ctx = bpy.context
    ps = _part_sockets()
    if ps is None:
        return ""
    sk, co = ps
    unit = float(job.get("_unit", 1.0))
    joints, aliases = library_table(job.get("path", ""))
    spec = joints.get(str(job.get("category") or ""))
    if not isinstance(spec, dict):
        return ""
    # the names the rules read (the file's own from before a library rename,
    # or the variant's)
    folder = job.get("_folder") or os.path.basename(os.path.dirname(str(job.get("path", ""))))
    jname = job.get("_rname") or job.get("name")
    pname = _pname(part)
    side = part_side(pname, jname, folder) if spec.get("sided") else \
        _side_with_mirrored(pname, jname, folder) if isinstance(spec.get("socket"), list) else None
    if spec.get("mirrorLeft"):
        # Mar Fil ship right-hand pads; their '...-Mirrored' copies are lefts
        side = _side_with_mirrored(pname, jname, folder)
    hand = spec.get("socket") == "Hand" and spec.get("sided")
    if hand and side is None:
        # a '...-Mirrored' copy is a left hand; failing that, the fist says
        side = _side_with_mirrored(pname, jname, folder)
        if side is None:
            # a sidecar fit for one hand only says which (Turtle Ninja's claws)
            fs = [s_ for s_ in "RL" if any(k == f"ws_fit::{n}" for k in part.keys()
                                            for n in wanted_sockets(spec, s_, aliases))]
            side = fs[0] if len(fs) == 1 else None
        if side is None:
            try:
                side = hand_side_by_rule(part)
            except Exception as exc:      # never let a shape search stop a snap
                print("[TIOW Inbox] hand rule failed:", repr(exc))
    goes = None
    if spec.get("sided") and focus is not None:
        # a sided part goes on the side you picked, when it can go there: a
        # selected Shin L anchor or a left arm (its own Pad L) takes a right pad
        # mirrored; a selected left hand takes a hand-less weapon with a Grip L
        # fit, whatever folder it came from. (side stays the part's own side:
        # that's what says a pad needs mirroring)
        sides = {s_: set(wanted_sockets(spec, s_, aliases)) for s_ in ("R", "L")}
        picked = focus if focus.get("ws_type") is not None else None
        if picked is None and focus.type == 'MESH':
            own = [c for c in focus.children if any(c.get("ws_type") in v for v in sides.values())]
            picked = own[0] if len(own) == 1 else None
        mirrors = spec.get("mirrorLeft") or spec.get("mirrorSides")
        for s_, v in sides.items():
            if picked is not None and picked.get("ws_type") in v and \
                    (mirrors or any(f"ws_fit::{n}" in part.keys() for n in v)):
                goes = s_
    names = wanted_sockets(spec, goes or side, aliases)
    if spec.get("byFit"):
        # legs: the waist their fits are for (Mar Fil's plug, or flat)
        have = [n for n in names if f"ws_fit::{n}" in part.keys()]
        if have:
            names = have
    elif spec.get("sided") and side is None and goes is None and \
            not (spec.get("mirrorLeft") or spec.get("mirrorSides")):
        # no side in its name (Turtle Ninja arms): the side it has a fit for
        have = [n for n in names if f"ws_fit::{n}" in part.keys()]
        if have:
            names = have
    elif isinstance(spec.get("socket"), list) and not spec.get("sided") and \
            not (focus is not None and focus.get("ws_type") in names):
        # belt bits: the anchors the part has a fit for first (a loincloth
        # with a Belt Front fit goes to the front, not the first free hip)
        have = [n for n in names if f"ws_fit::{n}" in part.keys()]
        if have:
            names = have
    if not names:
        return ""
    if focus is None:
        return f" - select a model to snap it onto ({names[0]})"

    fit_of = _fit_of_fn(spec, side)

    if any(n.startswith("Forearm") for n in names):
        ensure_forearm_sockets(focus, aliases)
    sock, old = choose_socket(names, focus, co, ctx.view_layer, fit_of, prefer=_part_key(part))
    brought = ""
    if sock is None and isinstance(spec.get("adaptor"), dict):
        # flat legs on a Mar Fil torso: a body adaptor goes on its Waist first
        for n in names:
            via = spec["adaptor"].get(n)
            vs = _model_socket(focus, wanted_sockets({"socket": via}, None, aliases)) if via else None
            if vs is None:
                continue
            ad, brought = bring_adaptor(vs, prefs, unit)
            if ad is not None:
                sock, old = choose_socket(names, ad, co, ctx.view_layer, fit_of, prefer=_part_key(part))
                break
    if sock is None:
        return f" - no {' / '.join(names[:2])} socket on the selected model" + brought
    fit = fit_of(sock)
    tname = None if fit == sock.get("ws_type") else fit
    mirrored = ""
    if hand and f"ws_fit::{fit}" not in part.keys():
        hs = _hand_side_of(fit, aliases)
        if hs:
            try:
                got, _med = rule_hand_fit(part, hs, fit)
                mirrored += got
            except Exception as exc:
                print("[TIOW Inbox] hand rule failed:", repr(exc))
    if (spec.get("mirrorLeft") or spec.get("mirrorSides")) and not _has_fit(ctx.scene, part, fit):
        # a part that only has a left fit (CyberBrush's left pauldrons) is mirrored onto the right too
        left_only = fit.endswith(" R") and f"ws_fit::{fit[:-2]} L" in part.keys()
        mirrored = mirror_for_left(part, fit, side, both=bool(spec.get("mirrorSides")) or left_only)
    if not _has_fit(ctx.scene, part, fit):
        sk.ensure_type(ctx.scene, fit)
        park_at(part, sock, fit)
        return (f" - parked on {sock['ws_type']}: place it by eye, then "
                f"Save Fit for Folder (once for this folder)")
    sk.ensure_type(ctx.scene, str(sock.get("ws_type")))
    if tname:
        sk.ensure_type(ctx.scene, tname)
    if old is part:
        old = None
    # a two-handed part already covering this socket goes, like the part on it
    root = sock
    while root.parent is not None:
        root = root.parent
    members = [root] + list(_descendants(root))
    spanners = [o for o in members if o is not part and o is not old and sock.name in _spans_of(o)]
    extra_out = []
    if old is None and spanners:
        old, extra_out = spanners[0], spanners[1:]
    elif spanners:
        extra_out = spanners
    excl = [str(n) for n in (spec.get("exclusive") or [])]
    if sock.get("ws_type") in excl and sock.parent is not None:
        for s2 in sock.parent.children:
            if s2 is not sock and s2.get("ws_type") in excl and s2.get("ws_type") != sock.get("ws_type"):
                for o in _snapped_to(s2, co, members):
                    if o is not part and o is not old and o not in extra_out:
                        extra_out.append(o)
    spanned = []
    for n in spec.get("spans") or []:
        wanted = wanted_sockets({"socket": n}, None, aliases)
        for s2 in members:
            if s2 is not sock and s2.get("ws_type") in wanted:
                spanned.append(s2)
                for o in _snapped_to(s2, co, members):
                    if o is not part and o is not old and o not in extra_out:
                        extra_out.append(o)
    # what the outgoing part is holding, by socket type, to hand across
    held = []
    if old is not None:
        for os_ in [c for c in old.children if c.get("ws_type") is not None]:
            for m in [g for g in os_.children if g.type == 'MESH'] or \
                    _snapped_to(os_, co, ctx.view_layer.objects):
                held.append((os_["ws_type"], m))
    extra, err = place_on(part, sock, spec, tname, unit, sk, co,
                          skip=(old,) if old is not None else ())
    if err:
        return f" - not snapped: {err}"
    note = brought + f", snapped to {sock['ws_type']} on {sock.parent.name if sock.parent else sock.name}" + mirrored + extra
    if spanned:
        part["tiow_spans"] = json.dumps([s2.name for s2 in spanned])
        note += " (and " + ", ".join(s2["ws_type"] for s2 in spanned) + ")"
    for o in extra_out:
        if o.name not in bpy.data.objects:
            continue
        for os_ in [c for c in o.children if c.get("ws_type") is not None]:
            for m in [g for g in os_.children if g.type == 'MESH'] or \
                    _snapped_to(os_, co, ctx.view_layer.objects):
                co.detach_part(m, go_home=True)
        if o.get("tiow_src") and prefs.replaced == 'DELETE':
            gone = o.name
            _remove_part(o)
            note += f", replaced {gone}"
        else:
            co.detach_part(o, go_home=True)
            note += f", {o.name} sent home"
    if str(spec.get("socket")) == "Shoulder":
        got = copy_pad_anchor(part)
        if got:
            note += f", {got}"
    if old is not None:
        moved_over = 0
        mine = {c.get("ws_type"): c for c in part.children if c.get("ws_type") is not None}
        for t, m in held:
            target = mine.get(t)
            if target is not None:
                mt = m.get("ws_snap_type")
                _, e2 = place_on(m, target, _spec_for(m), None if mt in (None, t) else mt,
                                 unit, sk, co, skip=(old,))
                if not e2:
                    moved_over += 1
                    continue
            # nowhere for it on the new part (flat legs on an adaptor that Mar Fil
            # legs replace): a TIOW part goes with its holder, yours goes home
            if m.get("tiow_src") and prefs.replaced == 'DELETE':
                _remove_part(m)
            else:
                co.detach_part(m, go_home=True)
        if old.get("tiow_src") and prefs.replaced == 'DELETE':
            gone = old.name
            _remove_part(old)
            note += f", replaced {gone}"
        else:
            co.detach_part(old, go_home=True)
            note += f", {old.name} sent home"
        if moved_over:
            note += f" ({moved_over} held part(s) moved across)"
    if prefs.stand_on_base and sock.get("ws_type") == "Base":
        try:
            tilt = stand_on_base(sock)
            note += f", model stood flat on it ({tilt:.0f} deg)" if tilt >= 0.5 else ", model stood on it"
        except Exception as exc:          # never let the levelling spoil a snap
            print("[TIOW Inbox] stand on base failed:", repr(exc))
    return note


# ---------------------------------------------------------------- standing on the base

def base_socket_of(ob):
    """The Base socket of the model around `ob` (one with a base on it first)."""
    if ob is None:
        return None
    root = ob
    while root.parent is not None:
        root = root.parent
    socks = [o for o in [root] + list(_descendants(root)) if o.get("ws_type") == "Base"]
    if not socks:
        return None
    ps = _part_sockets()
    if ps is not None:
        on = [s for s in socks if _snapped_to(s, ps[1], bpy.context.view_layer.objects)]
        if on:
            return on[0]
    return socks[0]


def stand_on_base(sock):
    """Turn the whole model about its Base socket so the ground under its feet
    is flat on the grid: the socket's Z straight up (the smallest turn, so the
    model keeps facing the way it did), and the base's underside (or, with no
    base on it, the socket) dropped onto the grid where it stands. Only the
    model's root moves - every joint stays as it is - plus any part snapped in
    without being parented. Returns the tilt it took out, in degrees."""
    import numpy as np
    vl = bpy.context.view_layer
    root = sock
    while root.parent is not None:
        root = root.parent
    members = {root} | set(_descendants(root))
    ps = _part_sockets()
    loose = []
    if ps is not None:
        loose = [o for o in vl.objects if o not in members and ps[1].snap_socket_of(o) in members]
    before = root.matrix_world.copy()
    S = sock.matrix_world
    up = Vector(S.col[2][:3]).normalized()
    tilt = math.degrees(up.angle(Vector((0.0, 0.0, 1.0)))) if up.length > 1e-9 else 0.0
    p = S.translation.copy()
    turn = up.rotation_difference(Vector((0.0, 0.0, 1.0))).to_matrix().to_4x4()
    root.matrix_world = Matrix.Translation(p) @ turn @ Matrix.Translation(-p) @ before
    vl.update()
    low = sock.matrix_world.translation.z
    bases = _snapped_to(sock, ps[1], vl.objects) if ps is not None else []
    for b in bases:
        n = len(b.data.vertices)
        if n:
            co = np.empty(n * 3)
            b.data.vertices.foreach_get("co", co)
            M = np.array(b.matrix_world)
            low = min(low, float((co.reshape(-1, 3) @ M[2, :3] + M[2, 3]).min()))
    root.matrix_world = Matrix.Translation((0.0, 0.0, -low)) @ root.matrix_world
    vl.update()
    delta = root.matrix_world @ before.inverted_safe()
    for o in loose:
        o.matrix_world = delta @ o.matrix_world
    return tilt


# ---------------------------------------------------------------- anchors

ANCHORS_THREE = ("Shin R", "Shin L", "Pad R", "Pad L")
ANCHORS_TWO = ANCHORS_THREE[:2]              # older two-click shins (knee, ankle)
ANCHORS_ONE = ("Belt Front", "Belt Back", "Hip R", "Hip L")
CLICKS = {
    "Shin": ("the CIRCLE at one end of the ANKLE",
             "the CIRCLE at the other end of the ankle",
             "the TOP of the HOLE in the front of the shin"),
    "Pad": ("the FRONT CORNER of the arm's mini shoulder pad",
            "its BACK CORNER",
            "its TOP, at the inner edge by the shoulder joint"),
}


def _three_point_frame(anchor, pts, nrm, forward=None, outward=None):
    """Anchor frame from three points: the first two set a line, the third
    sits off it and is the anchor's origin.
    Shin: ankle circle, ankle circle, top of the shin hole -> X across the
    ankle, Y up the shin (from between the ankle circles to the hole), Z out
    of the front of the shin (the hole's opening).
    Pad: front corner, back corner, top of the arm's mini shoulder pad by the
    joint -> Y forward along the corners, Z from the corners' line to the top
    point, X = Y x Z. Which way along the corners is forward comes from
    `outward` (from the middle of the model out to this shoulder: X points
    out on a right arm, in on a left one), or failing that from `forward`.
    Left and right frames are mirror images, so a pad's left fit is its
    right fit mirrored across X. The order of the two corners or the two
    ankle circles doesn't matter."""
    a, b, c = pts
    if (a - b).length < 1e-6:
        raise ValueError("the first two clicks are on the same spot")
    line = (b - a).normalized()
    mid = (a + b) * 0.5
    off = (c - mid) - line * (c - mid).dot(line)
    if off.length < 0.05 * (a - b).length:
        raise ValueError("the third point is in line with the first two")
    if anchor.startswith("Shin"):
        x, y = line, off.normalized()
        z = x.cross(y)
        if z.dot(nrm[2]) < 0:
            x, z = -x, -z
    else:
        y = line
        z = off.normalized()
        x = y.cross(z)
        if outward is not None:
            # lateral: stays right however far the arm swings up or forward
            if x.dot(Vector(outward)) * (1 if anchor.endswith("R") else -1) < 0:
                y, x = -y, -x
        elif forward is not None and y.dot(Vector(forward)) < 0:
            y, x = -y, -x
    M = Matrix((x.normalized(), y.normalized(), z.normalized())).transposed().to_4x4()
    M.translation = c
    return M


def _forward_of(part):
    ps = _part_sockets()
    s0 = ps[1].snap_socket_of(part) if ps else None
    return (s0.matrix_world if s0 is not None else part.matrix_world).to_3x3() @ Vector((0, 1, 0))


def _outward_of(part, point):
    """From the middle of the model out to this side, for a part snapped onto
    a sided socket (an arm on Shoulder R): this socket minus its opposite
    number, or failing that the point minus the model's root, level. None
    if the part isn't on the model."""
    ps = _part_sockets()
    s0 = ps[1].snap_socket_of(part) if ps else None
    if s0 is None:
        return None
    t = str(s0.get("ws_type", ""))
    if t[-2:] in (" R", " L") and s0.parent is not None:
        other = t[:-1] + ("L" if t.endswith("R") else "R")
        for c in s0.parent.children:
            if c.get("ws_type") == other:
                v = s0.matrix_world.translation - c.matrix_world.translation
                if v.length > 1e-6:
                    return v.normalized()
    root = s0
    while root.parent is not None:
        root = root.parent
    up = (root.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
    v = Vector(point) - root.matrix_world.translation
    v -= up * v.dot(up)
    return v.normalized() if v.length > 1e-6 else None


def make_anchor(part, anchor, points, normals, forward=None, kind="clicked"):
    """Create (or replace) an anchor socket on `part` from surface points
    (world space). Shin and Pad: three points (see _three_point_frame); an
    older two-point Shin (knee, ankle) still works. Belt and hip: one point -
    Z out of the surface, Y as close to up as it gets."""
    pts = [Vector(p) for p in points]
    nrm = [Vector(n).normalized() for n in normals]
    M = None
    if anchor in ANCHORS_THREE and len(pts) >= 3:
        outward = None
        if forward is None and anchor.startswith("Pad"):
            outward = _outward_of(part, pts[2])
            if outward is None:
                forward = _forward_of(part)
        M = _three_point_frame(anchor, pts[:3], nrm[:3], forward, outward)
    elif anchor in ANCHORS_TWO:
        if len(pts) < 2 or (pts[0] - pts[1]).length < 1e-6:
            raise ValueError("needs a knee point and an ankle point")
        y = (pts[0] - pts[1]).normalized()
        z = nrm[0] + nrm[1]
        if z.length < 1e-6:
            z = nrm[0].copy()
        origin = pts[0]
    elif anchor.startswith("Pad"):
        raise ValueError("a Pad anchor needs three points")
    else:
        z = nrm[0].copy()
        origin = pts[0]
        y = Vector((0, 0, 1))
        if abs(y.dot(z.normalized())) > 0.95:
            y = part.matrix_world.to_3x3() @ Vector((0, 1, 0))
    if M is None:
        z = (z - y * z.dot(y)).normalized()
        x = y.cross(z).normalized()
        M = Matrix((x, y, z)).transposed().to_4x4()
        M.translation = origin
    for c in list(part.children):
        if c.type == 'EMPTY' and c.get("ws_type") == anchor:
            bpy.data.objects.remove(c)
    ob = bpy.data.objects.new(f"{part.name}_socket_{anchor}"[:63], None)
    coll = part.users_collection[0] if part.users_collection else bpy.context.scene.collection
    coll.objects.link(ob)
    ob.empty_display_type = 'ARROWS'
    dims = part.dimensions
    # three-point anchors sit in a hole or on a small plate: big enough to
    # see, and drawn in front of the mesh
    ob.empty_display_size = max((0.15 if anchor in ANCHORS_THREE else 0.05) * max(dims), 1e-3)
    ob.show_in_front = anchor in ANCHORS_THREE
    ob["ws_type"] = anchor
    ob["tiow_anchor"] = kind
    # the points themselves, in the part's own coordinates, so the anchor can
    # be copied onto other parts with the same shape
    inv = part.matrix_world.inverted_safe()
    ob["tiow_points"] = json.dumps([list(inv @ p) for p in pts])
    ob.parent = part
    ob.matrix_parent_inverse = part.matrix_world.inverted_safe()
    ob.matrix_world = M
    ps = _part_sockets()
    if ps:
        ps[0].ensure_type(bpy.context.scene, anchor)
    return ob


def _sidecar_for_write(part):
    """(path, the whole sockets file, the dict this part's own data is in) -
    the variant's entry for a part brought in as a variant - or None."""
    src = part.get("tiow_src")
    if not src or not os.path.isfile(str(src)):
        return None
    path = os.path.splitext(str(src))[0] + SIDECAR
    try:
        with open(path, encoding="utf-8") as f:
            whole = json.load(f)
        if not isinstance(whole, dict):
            whole = {}
    except (OSError, ValueError):
        whole = {}
    whole.setdefault("schemaVersion", 1)
    whole.setdefault("part", os.path.splitext(os.path.basename(str(src)))[0])
    vi = part.get("tiow_variant")
    if vi is None:
        return path, whole, whole
    vs = whole.get("variants")
    try:
        vi = int(vi)
    except (TypeError, ValueError):
        return None
    if not isinstance(vs, list) or not 0 <= vi < len(vs) or not isinstance(vs[vi], dict):
        return None                       # a mirror made on the spot that couldn't be saved
    sub = vs[vi].get("sidecar")
    if not isinstance(sub, dict):
        sub = vs[vi]["sidecar"] = {}
    return path, whole, sub


def _write_sidecar(path, whole):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(whole, f, indent=1)
    os.replace(tmp, path)


def remember_anchor(part, sock):
    """Write an anchor into the part's <part>.sockets.json beside its STL, so
    the part brings it along every time it is sent from TIOW (and other parts
    with the same shape can copy it)."""
    got = _sidecar_for_write(part)
    if got is None:
        return None
    path, whole, data = got
    unit = float(part.get("tiow_unit", 1.0)) or 1.0
    loc, rot, _s = part.matrix_world.decompose()
    frame = Matrix.LocRotScale(loc, rot, Vector((1, 1, 1)))
    L = frame.inverted_safe() @ sock.matrix_world
    L.translation = L.translation / unit
    entry = {"type": sock["ws_type"], "name": sock.name, "matrix": [x for row in L for x in row],
             "display_type": "ARROWS", "display_size": float(sock.empty_display_size) / unit,
             "props": {"tiow_anchor": str(sock.get("tiow_anchor", "clicked"))}}
    try:
        pts = json.loads(sock.get("tiow_points", "[]"))
        # stored in file units, in the STL's own coordinates
        if pts:
            entry["points"] = [list((frame.inverted_safe() @ (part.matrix_world @ Vector(p))) / unit) for p in pts]
    except (TypeError, ValueError):
        pass
    socks = [s for s in data.get("sockets", []) if isinstance(s, dict) and s.get("type") != sock["ws_type"]]
    data["sockets"] = socks + [entry]
    _write_sidecar(path, whole)
    return path


def forget_anchors(part, types):
    """Take anchors of these types out of the part's <part>.sockets.json.
    Returns how many were removed."""
    if not part.get("tiow_src") or not os.path.isfile(os.path.splitext(str(part["tiow_src"]))[0] + SIDECAR):
        return 0
    got = _sidecar_for_write(part)
    if got is None:
        return 0
    path, whole, data = got
    socks = data.get("sockets")
    if not isinstance(socks, list):
        return 0
    keep = [s for s in socks if not (isinstance(s, dict) and s.get("type") in types)]
    if len(keep) == len(socks):
        return 0
    data["sockets"] = keep
    try:
        _write_sidecar(path, whole)
    except OSError:
        return 0
    return len(socks) - len(keep)


# ---------------------------------------------------------------- shapes (numpy only)

def read_stl_np(path):
    """Vertices (merged) and triangles of an STL file, in file units."""
    import numpy as np
    with open(path, "rb") as f:
        data = f.read()
    tri = None
    if len(data) >= 84:
        n = int(np.frombuffer(data[80:84], np.uint32)[0])
        if 84 + 50 * n == len(data):
            rec = np.frombuffer(data[84:84 + 50 * n], dtype=[("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")])
            tri = rec["v"].reshape(-1, 3, 3).astype(np.float64)
    if tri is None:
        txt = data.decode("latin-1").split()
        vs = [i for i, w in enumerate(txt) if w == "vertex"]
        tri = np.array([[float(txt[i + 1]), float(txt[i + 2]), float(txt[i + 3])] for i in vs]).reshape(-1, 3, 3)
    V, inv = np.unique(tri.reshape(-1, 3).round(5), axis=0, return_inverse=True)
    return V, inv.reshape(-1, 3)


def mesh_np(ob):
    """Merged vertices and triangles of an object's mesh, in its own coordinates."""
    import numpy as np
    me = ob.data
    me.calc_loop_triangles()
    v = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", v)
    t = np.empty(len(me.loop_triangles) * 3, np.int32); me.loop_triangles.foreach_get("vertices", t)
    V, inv = np.unique(v.reshape(-1, 3).round(5), axis=0, return_inverse=True)
    return V, inv.reshape(-1)[t].reshape(-1, 3)


def _vertex_normals(V, T):
    import numpy as np
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    N = np.zeros_like(V)
    for i in range(3):
        np.add.at(N, T[:, i], fn)
    return N / (np.linalg.norm(N, axis=1)[:, None] + 1e-12)


def _spheres(V, N, r, sgn, cell=0.1, minvotes=40):
    """Centres of spherical patches of radius r: every vertex votes for the
    point one radius inside (balls, sgn=+1) or outside (sockets, sgn=-1)
    along its normal; a sphere shows up as a pile of votes. Least-squares
    refined. Returns [(centre, radius, vertices on it)]."""
    import numpy as np
    C = V - sgn * r * N
    found = []
    for shift in (0.0, 0.5):
        key = np.floor(C / cell + shift).astype(np.int64)
        uk, inv, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True)
        for k in np.argsort(-cnt)[:12]:
            if cnt[k] < minvotes:
                break
            c = C[inv.reshape(-1) == k].mean(0)
            rr = r
            for _ in range(6):      # the band follows the fitted radius: Mar Fil's two rigs then agree to 0.03 deg
                d = np.linalg.norm(V - c, axis=1)
                P = V[np.abs(d - rr) < 0.08]
                if len(P) < 20:
                    break
                A = np.c_[2 * P, np.ones(len(P))]
                x = np.linalg.lstsq(A, (P ** 2).sum(1), rcond=None)[0]
                c, rr = x[:3], float(np.sqrt(max(x[3] + x[:3] @ x[:3], 0.0)))
            d = np.linalg.norm(V - c, axis=1)
            on = int((np.abs(d - rr) < 0.05).sum())
            if abs(rr - r) < 0.25 and on >= minvotes and \
                    all(np.linalg.norm(c - f[0]) > 0.8 for f in found):
                found.append((c, rr, on))
    return found


def find_shin_points(V, T):
    """Mar Fil legs: for each lower leg, the two ankle circles (ends of the
    ankle cylinder: balls of r ~1.75-1.85) and the top of the hole in the
    shin (a socket of r ~1.97). Returns [(ankle a, ankle b, hole top,
    hole opening direction)] in the mesh's coordinates."""
    import numpy as np
    N = _vertex_normals(V, T)
    holes = []
    for r in (1.92, 1.97, 2.02):
        for c, rr, on in _spheres(V, N, r, -1, minvotes=60):
            if all(np.linalg.norm(c - h[0]) > 1.0 for h in holes):
                holes.append((c, rr, on))
    balls = []
    if not holes:
        return []
    # look for the ankle balls round the holes only: over the whole legs other
    # round bits (knees, hips) can take every place in the vote count
    H = np.array([h[0] for h in holes])
    near = (np.linalg.norm(V[:, None, :] - H[None], axis=2) < 11.0).any(1)
    Vb, Nb = V[near], N[near]
    for r in (1.65, 1.72, 1.79, 1.86, 1.93):
        for c, rr, on in _spheres(Vb, Nb, r, +1, minvotes=25):
            if all(np.linalg.norm(c - b[0]) > 0.8 for b in balls):
                balls.append((c, rr, on))
    if balls:
        top = max(b[2] for b in balls)
        balls = [b for b in balls if b[2] >= 0.3 * top]
    out = []
    for hc, hr, _on in holes:
        best = None
        for i in range(len(balls)):
            for j in range(i + 1, len(balls)):
                a, b = balls[i][0], balls[j][0]
                w = np.linalg.norm(a - b)
                if not (4.0 < w < 6.5):
                    continue
                L = np.linalg.norm(hc - 0.5 * (a + b))
                sc = abs(L - 6.7) + abs(np.linalg.norm(hc - a) - np.linalg.norm(hc - b))
                if L < 4.5 or L > 9.0:
                    continue
                if best is None or sc < best[0]:
                    best = (sc, a, b)
        if best is None:
            continue
        _sc, a, b = best
        # the circles are the ends of the ankle cylinder: one radius out along its axis
        u = (b - a) / np.linalg.norm(b - a)
        ra = next(x[1] for x in balls if np.allclose(x[0], a)); rb = next(x[1] for x in balls if np.allclose(x[0], b))
        ea, eb = a - u * ra, b + u * rb
        mid = 0.5 * (a + b)
        up = hc - mid; up -= u * (up @ u); up /= np.linalg.norm(up)
        d = np.linalg.norm(V - hc, axis=1)
        cup = V[np.abs(d - hr) < 0.06]
        if len(cup) < 10:
            continue
        top = cup[np.argmax((cup - hc) @ up)]
        # the rim's top is nearly flat across the ankle: which vertex wins jumps
        # by up to 0.25 sideways, so put the point level with the hole's centre
        top = top - u * ((top - hc) @ u)
        opening = hc - cup.mean(0); opening /= np.linalg.norm(opening)
        out.append((ea, eb, top, opening))
    return out


def auto_shin_anchors(legs):
    """Put Shin R and Shin L anchors on a Mar Fil legs part from its own
    shape (ankle circles and the shin holes), on whichever side doesn't have
    one yet. Returns a note for the status line."""
    have = {c.get("ws_type") for c in legs.children} & {"Shin R", "Shin L"}
    if len(have) == 2:
        return ""
    V, T = mesh_np(legs)
    if not len(T):
        return ""
    found = find_shin_points(V, T)
    if len(found) != 2:
        return f", no shin anchors (found {len(found)} of the 2 Mar Fil shin holes)"
    mw = legs.matrix_world
    R3 = mw.to_3x3()
    frames = []
    for ea, eb, top, opening in found:
        pts = [mw @ Vector(p) for p in (ea, eb, top)]
        n = (R3 @ Vector(opening)).normalized()
        frames.append((pts, n, _three_point_frame("Shin", pts, [n, n, n])))
    # X runs across the ankle towards the model's left on both legs: the leg
    # further along the other's X is the left one
    (pa, na, Fa), (pb, nb, Fb) = frames
    a_is_right = (Fb.translation - Fa.translation).dot(Fa.to_3x3() @ Vector((1, 0, 0))) > 0
    made = []
    for (pts, n, _F), side in (((pa, na, Fa), "R" if a_is_right else "L"), ((pb, nb, Fb), "L" if a_is_right else "R")):
        if f"Shin {side}" not in have:
            make_anchor(legs, f"Shin {side}", pts, [n, n, n], kind="auto")
            made.append(side)
    return ", Shin anchors found" if len(made) == 2 else f", Shin {made[0]} anchor found"


def _kabsch(P, Q):
    import numpy as np
    cp, cq = P.mean(0), Q.mean(0)
    U, _S, Vt = np.linalg.svd((P - cp).T @ (Q - cq))
    D = np.diag([1.0, 1.0, np.sign(np.linalg.det(Vt.T @ U.T))])
    R = Vt.T @ D @ U.T
    return R, cq - R @ cp


def _icp(src, tree, R, t, iters):
    import numpy as np
    d = None
    for _ in range(iters):
        P = src @ R.T + t
        Q = np.empty_like(P); d = np.empty(len(P))
        for i, p in enumerate(P):
            hit = tree.find_nearest(Vector(p))
            Q[i] = hit[0]; d[i] = hit[3]
        keep = d <= np.quantile(d, 0.85)
        R2, t2 = _kabsch(P[keep], Q[keep])
        R, t = R2 @ R, R2 @ t + t2
    P = src @ R.T + t
    d = np.array([tree.find_nearest(Vector(p))[3] for p in P])
    return R, t, d


_refs_cache = {}


def builtin_refs(kind):
    """Reference anchors that come with the add-on: arms whose three points
    are known (76-Arm-1-R-A, from Josh's pauldron example), with the surface
    around them, so other arms of the same make can copy them without
    anything clicked. Packed at the end of this file."""
    if "data" not in _refs_cache:
        import base64
        import zlib
        try:
            _refs_cache["data"] = json.loads(zlib.decompress(base64.b64decode("".join(_REFS_PACKED))))
        except (ValueError, zlib.error):
            _refs_cache["data"] = {}
    return [r for r in (_refs_cache["data"].get(kind) or []) if isinstance(r, dict)]


def _surface_sample(V, T, n, seed=0):
    """n points spread evenly over the mesh's surface (vertices bunch up
    where the sculpt is dense, which drags a shape match)."""
    import numpy as np
    tri = V[T]
    area = np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1)
    rng = np.random.default_rng(seed)
    i = rng.choice(len(T), n, p=area / area.sum())
    u, w = rng.random(n), rng.random(n)
    m = u + w > 1
    u[m], w[m] = 1 - u[m], 1 - w[m]
    t = tri[i]
    return t[:, 0] + u[:, None] * (t[:, 1] - t[:, 0]) + w[:, None] * (t[:, 2] - t[:, 0])


def _region_around(V, T, P, radius=5.0, n=1500):
    """The surface within `radius` of the three points' middle, evenly sampled."""
    import numpy as np
    S = _surface_sample(V, T, 300000)
    region = S[np.linalg.norm(S - P.mean(0), axis=1) < radius]
    if len(region) > n:
        region = region[np.random.default_rng(0).choice(len(region), n, replace=False)]
    return region


def _shoulder_pivots(V, T, k=4):
    """Where the arm's shoulder joint may be: the highest of the round
    (r ~2) bits of the arm - a Mar Fil arm's shoulder end is one."""
    import numpy as np
    N = _vertex_normals(V, T)
    found = []
    for r in (1.9, 2.0, 2.1):
        for c, _rr, _on in _spheres(V, N, r, +1, minvotes=25):
            if all(np.linalg.norm(c - q) > 0.8 for q in found):
                found.append(c)
    found.sort(key=lambda c: -c[2])
    return found[:k]


def _rot(axis, deg):
    import numpy as np
    a = math.radians(deg); c, s_ = math.cos(a), math.sin(a)
    if axis == 0:
        return np.array([[1, 0, 0], [0, c, -s_], [0, s_, c]])
    if axis == 1:
        return np.array([[c, 0, s_], [0, 1, 0], [-s_, 0, c]])
    return np.array([[c, -s_, 0], [s_, c, 0], [0, 0, 1]])


_swings_cache = {}


def _swings(n=8000, seed=2, max_deg=120.0):
    """Rotations spread evenly up to max_deg from none (about 3100 of them)."""
    import numpy as np
    if "R" not in _swings_cache:
        rng = np.random.default_rng(seed)
        q = rng.normal(size=(n, 4))
        q /= np.linalg.norm(q, axis=1)[:, None]
        w, x, y, z = q.T
        R = np.stack([1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w),
                      2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w),
                      2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)], 1).reshape(-1, 3, 3)
        ang = np.degrees(np.arccos(np.clip((np.trace(R, axis1=1, axis2=2) - 1) / 2, -1, 1)))
        _swings_cache["R"] = R[ang < max_deg]
    return _swings_cache["R"]


def swing_match(region, ref_joint, joint, nearest):
    """The reference shoulder swung about this arm's own shoulder joint (the
    two joints held together): every swing up to 120 deg scored on a few
    points, the best 40 nudged, the best 6 polished. Finds arms raised far
    forward or out (Mar Fil's arm 3, power fists 166-174: 90-97 deg from the
    reference), which the old grid of starts missed. (median, R, t)."""
    import numpy as np
    rng = np.random.default_rng(1)
    tiny = region[rng.choice(len(region), min(80, len(region)), replace=False)]
    small = region[rng.choice(len(region), min(250, len(region)), replace=False)]
    mid = region[rng.choice(len(region), min(700, len(region)), replace=False)]
    joint, ref_joint = np.asarray(joint, float), np.asarray(ref_joint, float)
    seeds = []
    for R in _swings():
        t = joint - R @ ref_joint
        _q, d = nearest(tiny @ R.T + t)
        seeds.append((float(np.median(d)), R, t))
    seeds.sort(key=lambda x: x[0])
    nudged = []
    for _m, R, t in seeds[:40]:
        R, t, d = _icp_np(small, nearest, R, t, 6)
        nudged.append((float(np.median(d)), R, t))
    nudged.sort(key=lambda x: x[0])
    best = None
    for _m, R, t in nudged[:6]:
        R, t, d = _icp_np(mid, nearest, R, t, 15)
        if best is None or np.median(d) < best[0]:
            best = (float(np.median(d)), R, t)
    R, t, d = _icp_np(region, nearest, best[1], best[2], 30)
    return float(np.median(d)), R, t


def match_shoulder(region, piv, V, T, tree, joints=()):
    """Fit a reference arm's shoulder (`region`, its joint at `piv`) onto
    another arm (mesh V, T; BVH `tree`), all in file coordinates. With the
    arm's shoulder joint known (`joints`: (this arm's, the reference's)) the
    reference is swung about it (swing_match). Otherwise, as Mar Fil place
    each arm differently in its file, the start points are this arm's
    possible shoulder joints, each tried at a grid of swings, scored, and the
    best few polished. Returns (median distance, R, t) or None."""
    import numpy as np
    if joints:
        near = _nearest_with(tree, 1.0)
        best = None
        for here, ref_j in joints:
            got = swing_match(region, ref_j, here, near)
            if best is None or got[0] < best[0]:
                best = got
        return best
    pivots = [(p, piv) for p in _shoulder_pivots(V, T)]
    if not pivots:
        return None
    rng = np.random.default_rng(1)
    small = region[rng.choice(len(region), min(300, len(region)), replace=False)]
    tiny = small[:100]
    mid = region[rng.choice(len(region), min(700, len(region)), replace=False)]
    seeds = []
    for p, q in pivots:
        for pitch in range(-90, 91, 15):
            Rp = _rot(0, pitch)
            for yaw in (-40, -20, 0, 20, 40):
                for roll in (-20, 0, 20):
                    R0 = _rot(2, yaw) @ _rot(1, roll) @ Rp
                    t0 = p - R0 @ q
                    d = [tree.find_nearest(Vector(q))[3] for q in tiny @ R0.T + t0]
                    seeds.append((float(np.median(d)), R0, t0))
    seeds.sort(key=lambda x: x[0])
    short = []
    for _m, R, t in seeds[:10]:
        R, t, d = _icp(small, tree, R, t, 8)
        short.append((float(np.median(d)), R, t))
    short.sort(key=lambda x: x[0])
    best = None
    for _m, R, t in short[:3]:
        R, t, d = _icp(mid, tree, R, t, 30)
        if best is None or np.median(d) < best[0]:
            best = (float(np.median(d)), R, t)
    R, t, d = _icp(region, tree, best[1], best[2], 40)
    return float(np.median(d)), R, t


def _pad_references(part, side):
    """Arms with known Pad anchors to copy from, best first: ones you clicked
    in the same folder, then folders beside it (a kit's Mirrored folder),
    then the ones that come with the add-on. Yields (name, mesh region
    around the points, the three points, all in that arm's file
    coordinates and already mirrored for the other side when needed, and
    where its shoulder joint is)."""
    import numpy as np
    MXv = np.array([-1.0, 1, 1])
    src = str(part.get("tiow_src") or "")
    if src:
        here = os.path.dirname(src)
        parent = os.path.dirname(here)
        folders = [here] + sorted(os.path.join(parent, d) for d in os.listdir(parent)
                                  if os.path.isdir(os.path.join(parent, d)) and os.path.join(parent, d) != here) \
            if os.path.isdir(parent) else [here]
        for folder in folders:
            try:
                names = sorted(os.listdir(folder))
            except OSError:
                continue
            for fn in names:
                if not fn.endswith(SIDECAR):
                    continue
                stl_path = os.path.join(folder, fn[:-len(SIDECAR)] + ".stl")
                if os.path.normcase(stl_path) == os.path.normcase(src) or not os.path.isfile(stl_path):
                    continue
                whole = read_sidecar(stl_path)
                # the file's own anchors, then its variants' (in their own coordinates)
                entries = [(whole, None, os.path.splitext(fn[:-len(SIDECAR)])[0])]
                for v in part_variants(whole):
                    if isinstance(v, dict) and isinstance(v.get("sidecar"), dict) and not v.get("duplicate"):
                        entries.append((v["sidecar"], variant_align(v), str(v.get("name") or "variant")))
                for data, Tv, ref_name in entries:
                    for s in (data or {}).get("sockets", []):
                        t = str(s.get("type", ""))
                        pts = s.get("points")
                        if not t.startswith("Pad ") or not isinstance(pts, list) or len(pts) != 3:
                            continue
                        if (s.get("props") or {}).get("tiow_anchor") != "clicked":
                            continue
                        try:
                            RV, RT = read_stl_np(stl_path)
                        except (OSError, ValueError):
                            continue
                        if Tv is not None:
                            Ta = np.array([list(r) for r in Tv], float)
                            RV = RV @ Ta[:3, :3].T + Ta[:3, 3]
                            if np.linalg.det(Ta[:3, :3]) < 0:
                                RT = RT[:, ::-1]
                        P = np.array(pts, float)
                        region = _region_around(RV, RT, P)
                        piv = _shoulder_pivots(RV, RT, 1)
                        if not piv:
                            continue
                        piv = piv[0]
                        joint = _joint_from_fits(data)
                        if not t.endswith(" " + side):
                            region, P, piv = region * MXv, P * MXv, piv * MXv
                            joint = None if joint is None else joint * MXv
                        yield ref_name, region, P, piv, joint
    for r in builtin_refs("Pad"):
        try:
            P = np.array(r["points"], float).reshape(3, 3)
            region = np.array(r["region"], float).reshape(-1, 3)
            piv = np.array(r["pivot"], float).reshape(3)
            joint = np.array(r["joint"], float).reshape(3) if r.get("joint") else None
        except (KeyError, TypeError, ValueError):
            continue
        if str(r.get("side", "R")) != side:
            P, region, piv = P * MXv, region * MXv, piv * MXv
            joint = None if joint is None else joint * MXv
        yield str(r.get("name", "built-in")), region, P, piv, joint


def _joint_from_fits(data):
    """Where an arm's shoulder joint is in its file: the point its Shoulder fit
    puts on the socket. None if its sockets file has no shoulder fit."""
    import numpy as np
    for k, m in ((data or {}).get("fits") or {}).items():
        if str(k).startswith("Shoulder") and isinstance(m, list) and len(m) == 16:
            F = np.array(m, float).reshape(4, 4)
            return np.linalg.inv(F)[:3, 3]
    return None


def _part_joint(part):
    """The same for an imported part, from its ws_fit::Shoulder ... (file units)."""
    import numpy as np
    unit = float(part.get("tiow_unit", 1.0)) or 1.0
    for k in part.keys():
        if k.startswith("ws_fit::Shoulder"):
            F = np.array(list(part[k]), float).reshape(4, 4)
            return np.linalg.inv(F)[:3, 3] / unit
    return None


def _side_with_mirrored(*texts):
    """part_side, and a Mar Fil '...-Mirrored' file counts as a left."""
    side = part_side(*texts)
    if side is None:
        words = set()
        for t in texts:
            t = re.sub(r"([a-z])([A-Z])", r"\1 \2", str(t or ""))
            words |= set(re.split(r"[^a-z]+", t.lower()))
        if words & {"mirrored", "mirror"}:
            side = "L"
    return side


# the same mini shoulder pad fits to 0.05-0.14 (median); another make's
# shoulder doesn't get under 0.25. Swung about the arm's own joint (which
# rules out a match in the wrong place) Mar Fil's power fists and Veteran
# Squad arms come to 0.18-0.23 and the pauldron sits right on all of them;
# Bladeguard arms have their own shoulder sculpts (0.19-0.41) and still get
# a usable anchor, flagged as rough above 0.25 so it can be checked.
MATCH_LIMIT = 0.2
JOINT_MATCH_LIMIT = 0.45
ROUGH_MATCH = 0.25


def copy_pad_anchor(part):
    """An arm with no Pad anchor of its own gets one copied from an arm whose
    points are known (one you clicked in the same kit, or Mar Fil's
    assault arm that comes with the add-on): that arm's mini shoulder pad is
    matched onto this arm and the three points carried across. The copy is
    saved with the arm (its .sockets.json), so it's instant next time."""
    import numpy as np
    from mathutils.bvhtree import BVHTree
    have = [c for c in part.children if str(c.get("ws_type", "")).startswith("Pad ")]
    if have or part.get("tiow_nopad"):
        return ""
    side = None
    for k in part.keys():                 # the shoulder it fits says which side it is
        if k.startswith("ws_fit::Shoulder ") and k[-1] in "RL":
            side = k[-1]
    side = side or _side_with_mirrored(_pname(part), _part_key(part), _pfolder(part)) or "R"
    tree = None
    unit = float(part.get("tiow_unit", 1.0)) or 1.0
    best = None
    here = _part_joint(part)
    for ref_name, region, P, piv, ref_joint in _pad_references(part, side):
        if len(region) < 50:
            continue
        if tree is None:
            # this arm in its own file coordinates (mesh coordinates / unit)
            V, T = mesh_np(part)
            V = V / unit
            tree = BVHTree.FromPolygons(V.tolist(), T.tolist())
        joints = [(here, ref_joint)] if here is not None and ref_joint is not None else []
        got = match_shoulder(region, piv, V, T, tree, joints)
        if got is None:
            continue
        med, R, t = got
        limit = JOINT_MATCH_LIMIT if joints else MATCH_LIMIT
        if best is None or med - limit < best[0] - best[3]:
            best = (med, P @ R.T + t, ref_name, limit)
        if med < 0.1 or (joints and med <= MATCH_LIMIT):
            break
    if best is None:
        return ""
    if best[0] > best[3]:
        return f"no Pad {side} anchor (its shoulder doesn't match {best[2]}: click its three points)"
    pts_w, nrm_w = [], []
    for p in best[1]:
        ok, loc, nrm, _i = part.closest_point_on_mesh(Vector(p * unit))
        q = loc if ok else Vector(p * unit)
        pts_w.append(part.matrix_world @ q)
        nrm_w.append((part.matrix_world.to_3x3() @ (nrm if ok else Vector((0, 0, 1)))).normalized())
    sock = make_anchor(part, f"Pad {side}", pts_w, nrm_w, kind="copied")
    sock["tiow_from"] = best[2]
    try:
        remember_anchor(part, sock)
    except OSError:
        pass
    rough = f" (rough match {best[0]:.2f}: check the pauldron, or click its three points)" if best[0] > ROUGH_MATCH else ""
    return f"Pad {side} anchor copied from {best[2]}{rough}"


def mirror_for_left(part, fit, side, both=False):
    """A right-hand pad going onto a left anchor: mirror its mesh and give it
    the right-hand fit mirrored across the anchor's X. both: also a left-hand
    part going onto a right socket (fins). Returns a note."""
    if fit.endswith(" L") and side != "L":
        right = fit[:-2] + " R"
    elif both and fit.endswith(" R") and side != "R":
        right = fit[:-2] + " L"
    else:
        return ""
    key = f"ws_fit::{right}"
    if key not in part.keys():
        return ""
    m = list(part[key])
    F = Matrix((m[0:4], m[4:8], m[8:12], m[12:16]))
    MX = Matrix.Scale(-1, 4, (1, 0, 0))
    part.data.transform(MX)
    part.data.flip_normals()
    part.data.update()
    FL = MX @ F @ MX
    part[f"ws_fit::{fit}"] = [x for row in FL for x in row]
    part["tiow_mirrored"] = True
    if not part.name.endswith("(mirrored)"):
        part.name = (part.name + " (mirrored)")[:63]
    return ", mirrored for the left" if fit.endswith(" L") else ", mirrored for the right"


# ---------------------------------------------------------------- one file, both sides (1.16)
#
# A part's other-side copy can live in its .sockets.json instead of a second
# STL: "variants": [{"side": "L" (or null), "mirror": true, "align": 16
# floats (this STL's coordinates -> the variant's), "name": the copy's own
# file name, "folder": the folder it was in, "from": its old library path,
# "sidecar": its own sockets, fits, category...}]. "duplicate": the same part
# twice (kept for the record, never used). "synth": a plain mirror the Mirror
# button made (sockets and fits mirrored), saved so anchors clicked on it stay.

MXM = Matrix.Scale(-1.0, 4, Vector((1.0, 0.0, 0.0)))


def _m16(m):
    return Matrix(([float(x) for x in m[0:4]], [float(x) for x in m[4:8]],
                   [float(x) for x in m[8:12]], [float(x) for x in m[12:16]]))


def _flat(M):
    return [float(x) for row in M for x in row]


def part_variants(data):
    vs = (data or {}).get("variants")
    return vs if isinstance(vs, list) else []


def variant_align(v):
    """The variant's align matrix (a plain X mirror if it has none)."""
    a = v.get("align") if isinstance(v, dict) else None
    if isinstance(a, list) and len(a) == 16:
        try:
            return _m16(a)
        except (TypeError, ValueError):
            pass
    return MXM.copy() if (v or {}).get("mirror", True) else Matrix.Identity(4)


def _swap_side(t):
    """'Shoulder R' <-> 'Shoulder L' (and the old '_r' / '_l' names)."""
    t = str(t)
    for a, b in ((" R", " L"), ("_r", "_l"), ("_R", "_L")):
        if t.endswith(a):
            return t[:-len(a)] + b
        if t.endswith(b):
            return t[:-len(b)] + a
    return t


def _mirror_name(s):
    """The name of a part's mirror image: '-Mirrored' taken off, else R and
    L swapped, else '-Mirrored' added (so the side rules read it right)."""
    s = re.sub(r"\.\d{3}$", "", str(s))
    if re.search(r"(?i)mirrored", s):
        return re.sub(r"(?i)[ _-]*\(?mirrored\)?", "", s).strip(" _-") or s
    swap = {"R": "L", "L": "R", "Right": "Left", "Left": "Right", "right": "left", "left": "right"}
    out, n = re.subn(r"(?<![A-Za-z0-9])(R|L|Right|Left|right|left)(?![A-Za-z0-9])",
                     lambda m: swap[m.group(1)], s)
    if n:
        return out
    out, n = re.subn(r"^(R|L)(?=[A-Z][a-z])", lambda m: swap[m.group(1)], s)
    return out if n else s + "-Mirrored"


def mirrored_sidecar(data, extra_fits=None):
    """A part's sockets file for its plain mirror image: matrices mirrored
    across X (kept right-handed), points and pivots mirrored, R and L swapped."""
    out = {}
    for k, v in (data or {}).items():
        if k in ("variants", "original", "schemaVersion", "part", "_about"):
            continue
        out[k] = json.loads(json.dumps(v))
    fits = dict(extra_fits or {})
    fits.update((data or {}).get("fits") or {})
    out["fits"] = {_swap_side(t): _flat(MXM @ _m16(m) @ MXM)
                   for t, m in fits.items() if isinstance(m, list) and len(m) == 16}
    socks = []
    for s in (data or {}).get("sockets") or []:
        if not isinstance(s, dict) or not isinstance(s.get("matrix"), list) or len(s["matrix"]) != 16:
            continue
        s2 = json.loads(json.dumps(s))
        s2["type"] = _swap_side(s.get("type", ""))
        if s.get("name"):
            s2["name"] = _mirror_name(s["name"])
        s2["matrix"] = _flat(MXM @ _m16(s["matrix"]) @ MXM)
        if isinstance(s.get("points"), list):
            s2["points"] = [[-float(p[0]), float(p[1]), float(p[2])] for p in s["points"]
                            if isinstance(p, list) and len(p) == 3]
        socks.append(s2)
    out["sockets"] = socks
    if isinstance(out.get("ruled"), dict):
        out["ruled"] = {_swap_side(k): v for k, v in out["ruled"].items()}
    for key in ("upright", "offHand"):
        m = (data or {}).get(key)
        if isinstance(m, list) and len(m) == 16:
            out[key] = _flat(MXM @ _m16(m) @ MXM)
    pv = (data or {}).get("pivot")
    if isinstance(pv, list) and len(pv) == 3:
        out["pivot"] = [-float(pv[0]), float(pv[1]), float(pv[2])]
    ty = (data or {}).get("types")
    if isinstance(ty, dict):
        t2 = {}
        for name, spec in ty.items():
            spec = json.loads(json.dumps(spec))
            if isinstance(spec, dict) and isinstance(spec.get("mat"), list) and len(spec["mat"]) == 16:
                spec["mat"] = _flat(MXM @ _m16(spec["mat"]) @ MXM)
            t2[_swap_side(name)] = spec
        out["types"] = t2
    return out


def pick_variant(job, data, focus):
    """Index of the variant a request arrives as, or None for the part as
    its file is. Only for sided parts with a maker's copy for the other side
    folded in: the side you picked wins (a selected socket, or a part on it,
    or the arm whose hand it goes in), else the free side, its own side first."""
    vs = part_variants(data)
    if not vs or focus is None:
        return None
    joints, aliases = library_table(job.get("path", ""))
    spec = joints.get(str(job.get("category") or ""))
    if not isinstance(spec, dict) or not spec.get("sided"):
        return None
    sides = {}
    for i, v in enumerate(vs):
        if isinstance(v, dict) and not v.get("synth") and not v.get("duplicate") \
                and v.get("side") in ("R", "L") and isinstance(v.get("sidecar"), dict):
            sides.setdefault(v["side"], i)
    if len(sides) != 1:
        return None
    other = next(iter(sides))
    own = "R" if other == "L" else "L"
    ps = _part_sockets()
    if ps is None:
        return None
    co = ps[1]
    mine = wanted_sockets(spec, own, aliases)
    theirs = [n for n in wanted_sockets(spec, other, aliases) if n not in mine]
    stem = os.path.splitext(os.path.basename(str(job.get("path", ""))))[0]
    keys = {str(((data or {}).get("original") or {}).get("name") or stem), str(vs[sides[other]].get("name") or "")}
    sock, _old = choose_socket(mine + theirs, focus, co, bpy.context.view_layer,
                               _fit_of_fn(spec, own), prefer=keys)
    if sock is not None and sock.get("ws_type") in theirs:
        return sides[other]
    return None


def _model_root(ob):
    while ob.parent is not None:
        ob = ob.parent
    return ob


def model_by_id(model):
    """The root of the Squad Builder model with this id, or None."""
    for o in bpy.context.view_layer.objects:
        if o is not None and o.get("tiow_model") == model and o.get("tiow_model_root"):
            return o
    return None


def _held_by(part, co):
    """[(socket type, part on it)] for the part's own sockets."""
    out = []
    for os_ in [c for c in part.children if c.get("ws_type") is not None]:
        for m in [g for g in os_.children if g.type == 'MESH'] or \
                _snapped_to(os_, co, bpy.context.view_layer.objects):
            if m is not part and all(m is not h for _t, h in out):
                out.append((str(os_["ws_type"]), m))
    return out


def _is_tiow(ob):
    return bool(ob.get("tiow_src")) and os.path.isfile(str(ob.get("tiow_src")))


def _counterpart(part, whole, other):
    """What the Mirror button turns `part` into, as import_request's _variant:
    -1 (the file itself) for a variant; for the file itself, the maker's copy
    for the other side (sided) or its mirror image, else a plain mirror made
    now and saved with the part (a record, if it couldn't be saved)."""
    if part.get("tiow_variant") is not None:
        return -1
    vs = part_variants(whole)
    cands = [(i, v) for i, v in enumerate(vs) if isinstance(v, dict)
             and isinstance(v.get("sidecar"), dict) and not v.get("duplicate")]
    if other:
        pick = [c for c in cands if c[1].get("side") == other]
    else:
        pick = [c for c in cands if variant_align(c[1]).determinant() < 0]
    pick.sort(key=lambda c: (bool(c[1].get("synth")), c[0]))
    if pick:
        return pick[0][0]
    src = str(part["tiow_src"])
    ff = {}
    for t, e in read_folder_fits(src).items():
        m = e.get("m") if isinstance(e, dict) else e
        if isinstance(m, list) and len(m) == 16:
            ff[t] = m
    rec = {"side": other, "mirror": True, "synth": True, "align": _flat(MXM),
           "name": _mirror_name(_part_key(part)), "folder": _pfolder(part),
           "title": _mirror_name(part.name), "sidecar": mirrored_sidecar(whole, ff)}
    path = os.path.splitext(src)[0] + SIDECAR
    try:
        w2 = dict(whole or {})
        w2.setdefault("schemaVersion", 1)
        w2.setdefault("part", os.path.splitext(os.path.basename(src))[0])
        vs2 = list(part_variants(w2)) + [rec]
        w2["variants"] = vs2
        _write_sidecar(path, w2)
        return len(vs2) - 1
    except OSError:
        rec["_index"] = -1
        return rec


def _reimport(part, which, prefs):
    """A fresh copy of `part` brought in as `which` (see _counterpart), with
    its anchors, not snapped."""
    job = {"path": str(part["tiow_src"]), "category": str(part.get("tiow_category") or ""),
           "name": str(part.get("tiow_name") or _part_key(part)), "_variant": which, "_nosnap": True}
    if part.get("tiow_item"):
        job["itemId"] = str(part["tiow_item"])
    new = import_request(job, prefs)
    meshes = [o for o in new if o.type == 'MESH']
    if len(meshes) != 1:
        raise ValueError(f"{os.path.basename(job['path'])} is not one mesh")
    return meshes[0]


def _align_of(part):
    """The align the part was brought in with (identity for the file itself)."""
    vi = part.get("tiow_variant")
    if vi is None:
        return Matrix.Identity(4)
    try:
        vi = int(vi)
    except (TypeError, ValueError):
        return MXM.copy()
    vs = part_variants(read_sidecar(str(part.get("tiow_src", ""))))
    if 0 <= vi < len(vs) and isinstance(vs[vi], dict):
        return variant_align(vs[vi])
    return MXM.copy()


def _place(part, sock, fit, sk, co, skip=()):
    """Snap `part` onto `sock` with fit type `fit` (as auto_snap does).
    Returns '' or a note on what went wrong."""
    scene = bpy.context.scene
    st = str(sock.get("ws_type"))
    sk.ensure_type(scene, st)
    tname = None if (not fit or fit == st) else fit
    if tname:
        sk.ensure_type(scene, tname)
    if not _has_fit(scene, part, tname or st):
        park_at(part, sock, tname or st)
        return f"{part.name} parked on {st} (no fit for it: place it by eye)"
    _n, err = place_on(part, sock, _spec_for(part), tname, float(part.get("tiow_unit", 1.0)), sk, co, skip=skip)
    return f"{part.name} not snapped: {err}" if err else ""


def _mirror_onto(part, sock, fit, which, flip, prefs, sk, co, notes):
    """Bring `part` in again as `which`, onto `sock` with fit `fit`, and take
    out the old one. What it holds follows: mirrored onto the other side's
    socket when the part changed sides (flip), else onto the same socket of
    the new part as it is. Returns the new part."""
    held = _held_by(part, co)
    new = _reimport(part, which, prefs)
    if sock is not None:
        n = _place(new, sock, fit, sk, co, skip=(part,))
        if n:
            notes.append(n)
    for stype, h in held:
        want = _swap_side(stype) if flip else stype
        target = next((c for c in new.children if c.get("ws_type") == want), None)
        hfit = h.get("ws_snap_type") or stype
        if target is None:
            co.detach_part(h, go_home=True)
            notes.append(f"{h.name} sent home (no {want} on the mirrored part)")
        elif flip and _is_tiow(h):
            hs = "L" if want.endswith((" L", "_l", "_L")) else "R" if want.endswith((" R", "_r", "_R")) else None
            _mirror_onto(h, target, _swap_side(hfit), _counterpart(h, read_sidecar(h["tiow_src"]) or {}, hs),
                         True, prefs, sk, co, notes)
        elif flip:
            co.detach_part(h, go_home=True)
            notes.append(f"{h.name} sent home (not from TIOW, so it can't be mirrored)")
        else:
            n = _place(h, target, hfit, sk, co, skip=(part,))
            if n:
                notes.append(n)
    _remove_part(part)
    return new


def mirror_part(part, prefs):
    """The Mirror button. A part on a left/right socket (an arm, a pistol, a
    pauldron, a pouch on a hip) moves to the other side as its mirror image,
    with what it holds, and the part there comes across mirrored the other
    way. Anything else (legs, a head, a torso) is flipped where it stands and
    keeps what's on it. Returns (new part, note)."""
    ps = _part_sockets()
    if ps is None:
        raise ValueError("Part Sockets isn't enabled")
    sk, co = ps
    if not _is_tiow(part):
        raise ValueError(f"{part.name} didn't come from TIOW, so there's no file to mirror")
    vl = bpy.context.view_layer
    whole = read_sidecar(part["tiow_src"]) or {}
    sock = co.snap_socket_of(part)
    spec = _spec_for(part) or {}
    st = str(sock.get("ws_type")) if sock is not None else ""
    notes = []
    if sock is not None and spec.get("spans"):
        raise ValueError(f"{part.name} is held in both hands - it can't be mirrored")
    if sock is not None and _swap_side(st) != st:
        other_t = _swap_side(st)
        root = _model_root(sock)
        targets = [o for o in [root] + list(_descendants(root)) if o.get("ws_type") == other_t]
        if not targets:
            raise ValueError(f"no {other_t} socket on the model to mirror {part.name} onto")
        target = targets[0]
        fit = str(part.get("ws_snap_type") or st)
        there = [o for o in _snapped_to(target, co, vl.objects, _swap_side(fit)) if o is not part]
        own = "L" if st.endswith((" L", "_l", "_L")) else "R"
        other = "R" if own == "L" else "L"
        new = _mirror_onto(part, target, _swap_side(fit), _counterpart(part, whole, other),
                           True, prefs, sk, co, notes)
        note = f"{new.name} on {other_t}"
        for b in there:
            if _is_tiow(b):
                bfit = str(b.get("ws_snap_type") or other_t)
                nb = _mirror_onto(b, sock, _swap_side(bfit),
                                  _counterpart(b, read_sidecar(b["tiow_src"]) or {}, own),
                                  True, prefs, sk, co, notes)
                note += f", {nb.name} on {st}"
            else:
                co.detach_part(b, go_home=True)
                notes.append(f"{b.name} sent home (not from TIOW, so it can't be mirrored)")
    elif sock is not None:
        new = _mirror_onto(part, sock, str(part.get("ws_snap_type") or st), _counterpart(part, whole, None),
                           False, prefs, sk, co, notes)
        note = f"{new.name} flipped on {st}"
    else:
        # on nothing (a torso): flipped where it stands, the parts on it stay put
        W = part.matrix_world.copy()
        k = float(part.get("tiow_unit", 1.0)) * float(part.get("tiow_scale", 1.0))
        Tcur = _align_of(part)
        held = _held_by(part, co)
        new = _reimport(part, _counterpart(part, whole, None), prefs)
        K = _align_of(new) @ Tcur.inverted()
        K.translation = K.translation * k
        new.matrix_world = W @ MXM @ K.inverted()
        for stype, h in held:
            target = next((c for c in new.children if c.get("ws_type") == stype), None)
            if target is None:
                co.detach_part(h, go_home=True)
                notes.append(f"{h.name} sent home (no {stype} on the mirrored part)")
                continue
            n = _place(h, target, h.get("ws_snap_type") or stype, sk, co, skip=(part,))
            if n:
                notes.append(n)
        _remove_part(part)
        note = f"{new.name} flipped where it stands"
    if prefs.stand_on_base:
        bs = base_socket_of(new)
        if bs is not None and _snapped_to(bs, co, vl.objects):
            try:
                stand_on_base(bs)
            except Exception as exc:      # never let the levelling spoil a mirror
                print("[TIOW Inbox] stand on base failed:", repr(exc))
    for o in list(vl.objects):
        if o is not None:
            o.select_set(False)
    new.select_set(True)
    vl.objects.active = new
    return new, note + ("; " + "; ".join(notes) if notes else "")


class TIOW_OT_mirror_part(bpy.types.Operator):
    """Mirror the selected part. An arm, a hand-held part, a pauldron or a hip
    pouch moves to the other side as its mirror image (what it holds comes
    too, and the part already there swaps over). Legs, a head or a torso flip
    where they stand. Uses the maker's own mirror copy when the library has one"""
    bl_idname = "tiow.mirror_part"
    bl_label = "Mirror"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, ctx):
        o = ctx.view_layer.objects.active
        return ctx.mode == 'OBJECT' and o is not None and o.type == 'MESH' and bool(o.get("tiow_src"))

    def execute(self, ctx):
        prefs = get_prefs()
        try:
            _new, note = mirror_part(ctx.view_layer.objects.active, prefs)
        except (ValueError, OSError, RuntimeError) as exc:
            self.report({'ERROR'}, str(exc))
            _set_status(f"Mirror: {exc}")
            return {'CANCELLED'}
        _set_status("Mirrored: " + note)
        self.report({'INFO'}, "Mirrored: " + note)
        return {'FINISHED'}


# ---------------------------------------------------------------- wrist rules
#
# A hand is a hand: any hand-held part goes onto any arm, whatever kit or
# maker either came from, without a fit saved for that pair. Both ends are
# found from the shape, the same way every time:
#
# Arm (its Hand R / Hand L socket): the wrist face - the outermost flat face of
# wrist size at the far end of the arm from the shoulder. Origin at its
# centre, Y into the arm (along the forearm), and the roll from where the
# forearm's armour sits round the wrist (on a marine arm the vambrace side is
# a fixed way round from 'up', on every kit tried).
#
# Hand-held part (its Hand R / Hand L fit): the wrist stump - a round flat
# cap on a short neck - with a fist behind it. Every stump cap on the part is
# tried with the reference fist (Mar Fil's, shipped below) fitted behind it
# at every roll; the best is the hand. Origin at the cap's centre, Y out of
# the hand, the roll from the fist (knuckles), so a weapon held at a
# different angle in the fist still comes out the right way up.
#
# Both are worked out once and saved in the part's .sockets.json (marked
# "ruled"), so the next import is instant. A socket or fit you made yourself
# always wins over the rule.

WRIST_RULE = "wrist-1"
ARMOUR_ANGLE = -86.0     # deg: the forearm armour sits this far round from the wrist's up (right arm)
HAND_SEAT = 0.19         # mm: the stump sits this far into the arm's wrist face (Josh's placements)
FIST_LIMIT = 0.3         # mm: median distance above which the reference fist isn't a hand
_fist_cache = {}
HANDLESS = re.compile(r"fist|claw|gauntlet|handled|with ?handle|arm ?\+ ?hand", re.I)


def _fist_points():
    """The reference fist, a right hand, in its own frame (Y out of the hand,
    Z its top)."""
    import numpy as np
    if "p" not in _fist_cache:
        import base64
        import zlib
        try:
            d = json.loads(zlib.decompress(base64.b64decode("".join(_FIST_PACKED))))
            _fist_cache["p"] = np.array(d["points"], float).reshape(-1, 3)
        except (ValueError, KeyError, zlib.error):
            _fist_cache["p"] = np.zeros((0, 3))
    return _fist_cache["p"]


def _tri_info(V, T):
    import numpy as np
    A, B, C = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    n = np.cross(B - A, C - A)
    a = np.linalg.norm(n, axis=1)
    return (A + B + C) / 3, n / np.maximum(a[:, None], 1e-12), a / 2


def _components(idx, cen, link):
    """Triangles (by index) grouped into patches whose centres are within
    `link` of each other (grid neighbours, then label spreading)."""
    import numpy as np
    n = len(idx)
    if n == 0:
        return []
    P = cen[idx]
    key = np.floor(P / link).astype(np.int64)
    key -= key.min(0)
    d1, d2 = int(key[:, 1].max()) + 3, int(key[:, 2].max()) + 3
    code = (key[:, 0] + 1) * d1 * d2 + (key[:, 1] + 1) * d2 + (key[:, 2] + 1)
    order = np.argsort(code, kind="stable")
    cs = code[order]
    A_, B_ = [], []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                nc = cs + dx * d1 * d2 + dy * d2 + dz
                lo = np.searchsorted(cs, nc, "left")
                cnt = np.searchsorted(cs, nc, "right") - lo
                tot = int(cnt.sum())
                if tot == 0:
                    continue
                a = np.repeat(np.arange(n), cnt)
                b = lo[a] + (np.arange(tot) - np.repeat(np.cumsum(cnt) - cnt, cnt))
                keep = a < b
                a, b = order[a[keep]], order[b[keep]]
                close = np.sum((P[a] - P[b]) ** 2, axis=1) < link * link
                A_.append(a[close])
                B_.append(b[close])
    lab = np.arange(n)
    if A_:
        a, b = np.concatenate(A_), np.concatenate(B_)
        while True:
            m = np.minimum(lab[a], lab[b])
            new = lab.copy()
            np.minimum.at(new, a, m)
            np.minimum.at(new, b, m)
            new = new[new]
            if np.array_equal(new, lab):
                break
            lab = new
    _u, inv = np.unique(lab, return_inverse=True)
    srt = np.argsort(inv, kind="stable")
    cuts = np.cumsum(np.bincount(inv))[:-1]
    return [idx[g] for g in np.split(srt, cuts)]


def _flat_patches(V, T, cen, n, a, idx, area):
    """Flat faces among triangles `idx`: (triangles, normal, area), each
    between area[0] and area[1] mm2."""
    import numpy as np
    bins = {}
    for i, k in zip(idx, map(tuple, np.round(n[idx] * 12).astype(int))):
        bins.setdefault(k, []).append(i)
    seen = set()
    for ii in bins.values():
        ii = np.array(ii)
        if a[ii].sum() < area[0]:
            continue
        nn = (n[ii] * a[ii, None]).sum(0)
        nn /= np.linalg.norm(nn)
        ii = ii[(n[ii] @ nn) > 0.995]
        off = cen[ii] @ nn
        for o in np.unique(np.round(off / 0.04)):
            sel = ii[np.abs(off / 0.04 - o) < 0.75]
            if a[sel].sum() < area[0]:
                continue
            for g in _components(sel, cen, 0.8):
                A = float(a[g].sum())
                key = (len(g), int(g.min()))
                if area[0] <= A <= area[1] and key not in seen:
                    seen.add(key)
                    yield g, nn, A


def _face_circle(V, T, g, nn):
    """Centre and radius of a flat face's outline (circle fit to its edge)."""
    import numpy as np
    E = np.sort(np.concatenate([T[g][:, [0, 1]], T[g][:, [1, 2]], T[g][:, [2, 0]]]), axis=1)
    u, c = np.unique(E, axis=0, return_counts=True)
    B = V[np.unique(u[c == 1])]
    X0, _Y, Z0 = _plane_basis(nn).T
    c0 = B.mean(0)
    P2 = np.c_[(B - c0) @ X0, (B - c0) @ Z0]
    s, *_ = np.linalg.lstsq(np.c_[2 * P2, np.ones(len(P2))], (P2 ** 2).sum(1), rcond=None)
    r = math.sqrt(max(s[2] + s[0] ** 2 + s[1] ** 2, 0.0))
    return c0 + s[0] * X0 + s[1] * Z0, r, B


def _plane_basis(nn):
    """3x3 with columns (X, nn, Z): any right-handed frame with Y = nn."""
    import numpy as np
    X0 = np.cross(nn, [0, 0, 1.0]) if abs(nn[2]) < 0.9 else np.cross(nn, [1.0, 0, 0])
    X0 /= np.linalg.norm(X0)
    return np.c_[X0, nn, np.cross(X0, nn)]


def _icp_np(src, nearest, R, t, iters, trim=0.85):
    import numpy as np
    for _ in range(iters):
        P = src @ R.T + t
        Q, d = nearest(P)
        keep = d <= np.quantile(d, trim)
        R2, t2 = _kabsch(P[keep], Q[keep])
        R, t = R2 @ R, R2 @ t + t2
    _Q, d = nearest(src @ R.T + t)
    return R, t, d


def _bvh_nearest(V, T):
    """Closest points on a mesh (V, T) to points P: (points, distances)."""
    import numpy as np
    from mathutils.bvhtree import BVHTree
    tree = BVHTree.FromPolygons(V.tolist(), T.tolist())
    return _nearest_with(tree, 1.0)


def _object_nearest(part, unit):
    """The same on a part already in the scene, in its file coordinates."""
    from mathutils.bvhtree import BVHTree
    return _nearest_with(BVHTree.FromObject(part, bpy.context.evaluated_depsgraph_get()), unit)


def _nearest_with(tree, unit):
    import numpy as np

    def nearest(P):
        Q = np.array(P, float)
        d = np.full(len(P), 1e9)
        for i, p in enumerate(P * unit if unit != 1.0 else P):
            hit = tree.find_nearest(Vector(p))
            if hit[0] is not None:
                Q[i] = hit[0]
                d[i] = hit[3]
        if unit != 1.0:
            Q[d < 1e9] /= unit
            d[d < 1e9] /= unit
        return Q, d
    return nearest


def _mirrored(nearest):
    """`nearest` for the mirror image (x -> -x) of the same mesh."""
    import numpy as np
    MXv = np.array([-1.0, 1, 1])

    def near(P):
        Q, d = nearest(np.asarray(P) * MXv)
        return Q * MXv, d
    return near


def arm_wrist_frame(V, T, joint, side="R", round_tol=0.12):
    """The arm's wrist socket (4x4, file coordinates) from its shape, or None.
    `joint`: where the shoulder joint is, so the wrist is the far end.
    round_tol: how far the face's rim may stray from a circle (share of r)."""
    import numpy as np
    V = np.asarray(V, float)
    T = np.asarray(T)
    joint = np.asarray(joint, float)
    if side == "L":            # the right-arm rule on the mirror image
        V, T, joint = V * [-1.0, 1, 1], T[:, ::-1], joint * [-1.0, 1, 1]
    cen, n, a = _tri_info(V, T)
    dist = np.linalg.norm(cen - joint, axis=1)
    idx = np.where(dist > 0.55 * dist.max())[0]
    cand = []
    for g, nn, A in _flat_patches(V, T, cen, n, a, idx, (3.0, 25.0)):
        c = (cen[g] * a[g, None]).sum(0) / A
        out = c - joint
        if out @ nn >= 0.3 * np.linalg.norm(out):        # faces away from the shoulder
            cand.append((float(np.linalg.norm(out)), g, nn))
    # the outermost face, if round (a wrist is round, Mar Fil's r 1.7-1.9);
    # failing that a wrist-sized round face just behind it (within 1.5 mm: the
    # Chaplain's rosary cross hangs past his wrist). A gun held in the arm has
    # round faces too, but further in or of another size, so it still finds none
    cand.sort(key=lambda x: -x[0])
    for i, (_d, g, nn) in enumerate(cand):
        if i and cand[0][0] - _d > 1.5:
            return None
        origin, r, B = _face_circle(V, T, g, nn)
        rim = B - origin
        rim = np.linalg.norm(rim - (rim @ nn)[:, None] * nn, axis=1)
        if rim.std() <= round_tol * r and (1.0 <= r <= 2.8 if i == 0 else 1.6 <= r <= 2.0):
            break
        if i == 0 and len(cand) == 1:
            return None
    else:
        return None
    Y = -nn
    B = _plane_basis(Y)
    e1, e3 = B[:, 0], B[:, 2]
    Z = e3
    S = _surface_sample(V, T, 200000)
    L = S - origin
    dep = L @ Y
    lat = L - dep[:, None] * Y
    rad = np.linalg.norm(lat, axis=1)
    k = (dep > 0.3) & (dep < 2.5) & (rad > 1.9) & (rad < 4.5)
    if k.sum() > 50:
        b = lat[k].mean(0)
        beta = math.degrees(math.atan2(b @ e1, b @ e3))
        z = math.radians(beta - ARMOUR_ANGLE)
        Z = math.sin(z) * e1 + math.cos(z) * e3
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = np.cross(Y, Z), Y, Z, origin
    if side == "L":
        MX = np.diag([-1.0, 1, 1, 1])
        M = MX @ M @ MX
    return M


def _stub_caps(V, T, cen, n, a):
    """Round flat caps on the end of a short neck: the wall right behind the
    cap all the way round, nothing in front. [(centre, normal out, radius)]."""
    import numpy as np
    out = []
    for g, nn, A in _flat_patches(V, T, cen, n, a, np.arange(len(T)), (2.5, 16.0)):
        c, r, _B = _face_circle(V, T, g, nn)
        L = V - c
        h = L @ nn
        rad = np.linalg.norm(L - h[:, None] * nn, axis=1)
        if np.any((h > 0.05) & (h < 1.5) & (rad < 0.8 * r)):
            continue
        wall = (h < -0.15) & (h > -0.8) & (rad > 0.6 * r) & (rad < 1.4 * r)
        if wall.sum() < 12:
            continue
        X0, _Y, Z0 = _plane_basis(nn).T
        W = L[wall]
        ang = np.degrees(np.arctan2(W @ Z0, W @ X0))
        if len(np.unique(np.floor(ang / 15))) / 24.0 < 0.85:
            continue
        out.append((c, nn, r))
    return out


def hand_caps(V, T):
    """The wrist-stump candidates on a part (see _stub_caps)."""
    import numpy as np
    V = np.asarray(V, float)
    cen, n, a = _tri_info(V, np.asarray(T))
    return _stub_caps(V, np.asarray(T), cen, n, a)


def hand_wrist_frame(V, T, side="R", nearest=None, caps=None, quick=False):
    """The hand's wrist frame (4x4, file coordinates) and how well the fist
    matched (median mm), or (None, None). nearest: closest points on this
    part (file coordinates); caps: from hand_caps. quick: stop after the
    rough fit (to compare sides)."""
    import numpy as np
    V = np.asarray(V, float)
    T = np.asarray(T)
    MXv = np.array([-1.0, 1, 1])
    ref = _fist_points()
    if len(ref) < 100:
        return None, None
    if caps is None:
        caps = hand_caps(V, T)
    if not caps:
        return None, None
    if nearest is None:
        nearest = _bvh_nearest(V, T)
    if side == "L":          # the right-hand rule on the mirror image
        nearest = _mirrored(nearest)
        caps = [(c * MXv, nn * MXv, r) for c, nn, r in caps]
    rng = np.random.default_rng(0)
    tiny = ref[rng.choice(len(ref), 150, replace=False)]
    mid = ref[rng.choice(len(ref), 600, replace=False)]
    seeds = []
    for ci, (c, nn, _r) in enumerate(caps):
        B = _plane_basis(nn)
        for roll in range(0, 360, 15):
            R0 = B @ _rot(1, roll)
            _Q, d = nearest(tiny @ R0.T + c)
            seeds.append((float(np.median(d)), ci, R0, c))
    seeds.sort(key=lambda s_: s_[0])
    best = None
    for _m, ci, R, t in seeds[:(4 if quick else 10)]:
        R, t, d = _icp_np(mid, nearest, R, t, 12 if quick else 20)
        if best is None or np.median(d) < best[0]:
            best = (float(np.median(d)), ci, R, t)
    md, ci, R, t = best
    if quick:
        return None, md
    c, nn, _r = caps[ci]
    half = 2 * np.outer(nn, nn) - np.eye(3)          # the fist the other way up
    R2, t2, d2 = _icp_np(mid, nearest, half @ R, half @ (t - c) + c, 20)
    if np.median(d2) < md:
        R, t = R2, t2
    R, t, d = _icp_np(ref, nearest, R, t, 25)
    Y = nn
    Z = R[:, 2] - (R[:, 2] @ Y) * Y
    Z /= np.linalg.norm(Z)
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = np.cross(Y, Z), Y, Z, c - HAND_SEAT * Y
    if side == "L":
        MX = np.diag([-1.0, 1, 1, 1])
        M = MX @ M @ MX
    return M, float(np.median(d))


def _remember_rule(part, fits=None, sockets=None):
    """Save rule results in the part's .sockets.json: fits {type: 4x4 file
    coordinates}; sockets via remember_anchor. Never overwrites a fit that
    wasn't made by the rule."""
    src = part.get("tiow_src")
    if not src or not os.path.isfile(str(src)):
        return None
    for s in sockets or []:
        remember_anchor(part, s)
    if not fits:
        return None
    got = _sidecar_for_write(part)
    if got is None:
        return None
    path, whole, data = got
    data.setdefault("sockets", [])
    have = data.setdefault("fits", {})
    ruled = data.setdefault("ruled", {})
    for t, M in fits.items():
        if t in have and t not in ruled:
            continue
        have[t] = [float(x) for x in M.ravel()]
        ruled[t] = WRIST_RULE
    _write_sidecar(path, whole)
    return path


def _part_np(part):
    """This part's mesh in its own file coordinates (mesh / unit)."""
    unit = float(part.get("tiow_unit", 1.0)) or 1.0
    V, T = mesh_np(part)
    return V / unit, T, unit


def _mirror_twin(src, stem=None):
    """Mar Fil ship some left parts as '<name>-Mirrored.stl' (in a
    '...-Mirrored' folder) beside the right one '<name>.stl'. That right
    one's path, or None. `stem`: the maker's name for this file (after a
    library rename the twin is found by the name its sockets file keeps)."""
    own, ext = os.path.splitext(os.path.basename(str(src)))
    m = re.match(r"(.+?)[ _-]*mirrored$", str(stem or own), re.I)
    if not m:
        return None
    want = m.group(1)
    here = os.path.dirname(str(src))
    parent = os.path.dirname(here)
    try:
        folders = [here] + sorted(os.path.join(parent, d) for d in os.listdir(parent)
                                  if os.path.isdir(os.path.join(parent, d)))
    except OSError:
        folders = [here]
    for d in folders:
        p = os.path.join(d, want + ext)
        if os.path.isfile(p):
            return p
    for d in folders:                     # renamed: the name its sockets file keeps
        try:
            names = sorted(os.listdir(d))
        except OSError:
            continue
        for fn in names:
            if not fn.endswith(SIDECAR):
                continue
            stl = os.path.join(d, fn[:-len(SIDECAR)] + ".stl")
            o = ((read_sidecar(stl) or {}).get("original") or {})
            if isinstance(o, dict) and o.get("name") == want and os.path.isfile(stl):
                return stl
    return None


def _arm_joint(part, V, T):
    import numpy as np
    joint = _part_joint(part)
    if joint is None:
        piv = _shoulder_pivots(V, T, 1)
        joint = piv[0] if piv else V[np.argmax(V[:, 2])]
    return np.asarray(joint, float)


def rule_wrist_socket(part, side=None):
    """An arm with no Hand socket gets one from the wrist rule. Returns a note."""
    import numpy as np
    have = {str(c.get("ws_type", "")) for c in part.children}
    src = str(part.get("tiow_src", ""))
    if side is None:
        for k in part.keys():
            if k.startswith("ws_fit::Shoulder ") and k[-1] in "RL":
                side = k[-1]
        side = side or _side_with_mirrored(_pname(part), _part_key(part), _pfolder(part)) or "R"
    tname = f"Hand {side}"
    if tname in have or part.get("tiow_nohand"):
        return ""
    V, T, unit = _part_np(part)
    joint = _arm_joint(part, V, T)
    M = arm_wrist_frame(V, T, joint, side)
    if M is None:
        if HANDLESS.search(f"{part.name} {_pname(part)} {os.path.basename(src)}"):
            return ""                     # a power fist or claw is the hand
        return f"no {tname} found (no round wrist face at the end of the arm)"
    how = "found at the wrist"
    # (a variant is an exact mirror: its own wrist says it all)
    twin = _mirror_twin(src, _part_key(part)) if side == "L" and part.get("tiow_variant") is None else None
    if twin:
        # Mar Fil turn the forearm of some '-Mirrored' arms, so its armour
        # no longer says which way the hand goes: the right arm's wrist,
        # mirrored, does (the wrist face stays this arm's own)
        try:
            VR, TR = read_stl_np(twin)
            MR = arm_wrist_frame(VR, TR, joint * [-1.0, 1, 1], "R")
        except (OSError, ValueError):
            MR = None
        if MR is not None:
            Y = M[:3, 1]
            Z = MR[:3, 2] * [-1.0, 1, 1]
            Z = Z - (Z @ Y) * Y
            if np.linalg.norm(Z) > 1e-6:
                Z /= np.linalg.norm(Z)
                M[:3, 0], M[:3, 2] = np.cross(Y, Z), Z
                how = f"found at the wrist, turned as {os.path.splitext(os.path.basename(twin))[0]} mirrored"
    loc, rot, _s = part.matrix_world.decompose()
    frame = Matrix.LocRotScale(loc, rot, Vector((1, 1, 1)))
    L = Matrix(M.tolist())
    L.translation = L.translation * unit
    ob = bpy.data.objects.new(f"{part.name}_socket_{tname}"[:63], None)
    coll = part.users_collection[0] if part.users_collection else bpy.context.scene.collection
    coll.objects.link(ob)
    ob.empty_display_type = 'ARROWS'
    ob.empty_display_size = max(0.1 * max(part.dimensions), 1e-3)
    ob["ws_type"] = tname
    ob["tiow_anchor"] = "rule"
    ob.parent = part
    ob.matrix_parent_inverse = part.matrix_world.inverted_safe()
    ob.matrix_world = frame @ L
    ps = _part_sockets()
    if ps:
        ps[0].ensure_type(bpy.context.scene, tname)
    try:
        _remember_rule(part, sockets=[ob])
    except OSError:
        pass
    return f"{tname} {how}"


# Forearm armour (vambrace plates such as CyberBrush's Space Bug Hunter
# forearms) sits on a "Forearm R/L" socket. Mar Fil's assault arms carry one
# (Wrist_Armout_r), always the same step from their Hand socket; any other arm
# gets one from its Hand socket by that step when forearm armour arrives.
FOREARM_FROM_HAND = {
    "R": ((0.08116, 0.99192, -0.09753, -2.35307), (-0.01201, 0.09881, 0.99503, 1.89372),
          (0.99663, -0.07959, 0.01993, 0.07161), (0.0, 0.0, 0.0, 1.0)),
    "L": ((0.08116, -0.99192, 0.09753, 2.35307), (0.01201, 0.09881, 0.99503, 1.89372),
          (-0.99663, -0.07959, 0.01993, 0.07161), (0.0, 0.0, 0.0, 1.0)),
}


def ensure_forearm_sockets(focus, aliases=None):
    """Every arm in the model around `focus` that has a Hand socket and no
    Forearm socket on that side gets one (Hand socket @ FOREARM_FROM_HAND).
    Returns how many were made."""
    if focus is None:
        return 0
    aliases = aliases or DEFAULT_ALIASES
    root = focus
    while root.parent is not None:
        root = root.parent
    made = 0
    ps = _part_sockets()
    for part in [root] + list(_descendants(root)):
        if part.type != 'MESH' or part.get("ws_type") is not None:
            continue
        kids = [c for c in part.children if c.get("ws_type") is not None]
        for sd in "RL":
            hn = [f"Hand {sd}"] + list(aliases.get(f"Hand {sd}") or [])
            fn = [f"Forearm {sd}"] + list(aliases.get(f"Forearm {sd}") or [])
            if any(str(c.get("ws_type")) in fn for c in kids):
                continue
            hand = next((c for c in kids if str(c.get("ws_type")) in hn), None)
            if hand is None:
                continue
            unit = float(part.get("tiow_unit", 1.0)) or 1.0
            C = Matrix(FOREARM_FROM_HAND[sd])
            C.translation = C.translation * unit
            tname = f"Forearm {sd}"
            ob = bpy.data.objects.new(f"{part.name}_socket_{tname}"[:63], None)
            coll = part.users_collection[0] if part.users_collection else bpy.context.scene.collection
            coll.objects.link(ob)
            ob.empty_display_type = 'ARROWS'
            ob.empty_display_size = hand.empty_display_size if hand.type == 'EMPTY' else 1.0
            ob["ws_type"] = tname
            ob["tiow_anchor"] = "rule"
            ob.parent = part
            ob.matrix_parent_inverse = part.matrix_world.inverted_safe()
            ob.matrix_world = hand.matrix_world @ C
            if ps:
                ps[0].ensure_type(bpy.context.scene, tname)
            made += 1
    return made


def _hand_side_of(fit, aliases):
    """'R' / 'L' if this fit type is a hand socket (or one of its old names)."""
    for t in ("Hand R", "Hand L"):
        if fit == t or fit in (aliases.get(t) or []):
            return t[-1]
    return None


def _set_rule_fit(part, tname, M, unit):
    import numpy as np
    F = np.linalg.inv(M)
    Fs = Matrix(F.tolist())
    Fs.translation = Fs.translation * unit
    part[f"ws_fit::{tname}"] = [x for row in Fs for x in row]
    try:
        _remember_rule(part, fits={tname: F})
    except OSError:
        pass


def rule_hand_fit(part, side, tname=None):
    """A hand-held part with no fit for this hand socket gets one from the
    wrist rule. Returns (note, how well the fist matched or None)."""
    tname = tname or f"Hand {side}"
    if f"ws_fit::{tname}" in part.keys():
        return "", 0.0
    V, T, unit = _part_np(part)
    M, med = hand_wrist_frame(V, T, side, _object_nearest(part, unit))
    if M is None or med is None or med > FIST_LIMIT:
        return "", med
    _set_rule_fit(part, tname, M, unit)
    return f", {tname} found from the hand (fist {med:.2f})", med


def hand_side_by_rule(part):
    """'R' or 'L' for a hand-held part that doesn't say which: the side whose
    fist fits best, with that side's Hand fit set. None if neither is a hand.
    (Both sides fitted in full: on 102 Mar Fil hand-held parts the right side
    always won, by 1.1x or more; a quick fit got 4 of 10 wrong.)"""
    for s_ in ("R", "L"):
        if f"ws_fit::Hand {s_}" in part.keys():
            return s_
    V, T, unit = _part_np(part)
    caps = hand_caps(V, T)
    if not caps:
        return None
    near = _object_nearest(part, unit)
    got = {}
    for s_ in ("R", "L"):
        M, md = hand_wrist_frame(V, T, s_, near, caps)
        if M is not None and md is not None and md <= FIST_LIMIT:
            got[s_] = (md, M)
    if not got:
        return None
    s_ = min(got, key=lambda k: got[k][0])
    _set_rule_fit(part, f"Hand {s_}", got[s_][1], unit)
    return s_


class TIOW_OT_place_anchor(bpy.types.Operator):
    """Click on a part to put an anchor socket on it. Shin: the circle at each
    end of the ankle, then the top of the hole in the shin. Pad: the front and
    back corners of the arm's mini shoulder pad, then its top by the joint.
    Belt and hip: click once where the item should sit. Esc or right-click
    cancels"""
    bl_idname = "tiow.place_anchor"
    bl_label = "Place Anchor"
    bl_options = {'REGISTER', 'UNDO'}

    anchor: StringProperty(name="Anchor", default="Shin R")

    def _hit(self, ctx, event):
        from bpy_extras import view3d_utils
        # the button lives in the sidebar, so work in the 3D View's main region
        region, rv3d = self._region, self._rv3d
        co2 = (event.mouse_x - region.x, event.mouse_y - region.y)
        if not (0 <= co2[0] < region.width and 0 <= co2[1] < region.height):
            return None
        o = view3d_utils.region_2d_to_origin_3d(region, rv3d, co2)
        d = view3d_utils.region_2d_to_vector_3d(region, rv3d, co2)
        deps = ctx.evaluated_depsgraph_get()
        hit, loc, nrm, _i, ob, _m = ctx.scene.ray_cast(deps, o, d)
        if not hit or ob is None or ob.type != 'MESH' or ob.name.startswith("WS_"):
            return None
        return ob, loc, nrm

    def _prompt(self, ctx):
        if self.anchor in ANCHORS_THREE:
            steps = CLICKS[self.anchor.split()[0]]
            step = f"click {steps[len(self.pts)]}   ({len(self.pts) + 1} of 3)"
        else:
            step = "click where it should sit"
        ctx.workspace.status_text_set(f"{self.anchor}: {step}   (Esc / right-click: cancel)")

    def invoke(self, ctx, event):
        if ctx.area is None or ctx.area.type != 'VIEW_3D':
            self.report({'ERROR'}, "Run this from the 3D View")
            return {'CANCELLED'}
        self._region = next((r for r in ctx.area.regions if r.type == 'WINDOW'), None)
        self._rv3d = ctx.area.spaces.active.region_3d
        if self._region is None or self._rv3d is None:
            self.report({'ERROR'}, "Run this from the 3D View")
            return {'CANCELLED'}
        self.pts, self.nrms, self.part = [], [], None
        ctx.window_manager.modal_handler_add(self)
        self._prompt(ctx)
        return {'RUNNING_MODAL'}

    def _done(self, ctx):
        ctx.workspace.status_text_set(None)

    def modal(self, ctx, event):
        if event.type in {'ESC', 'RIGHTMOUSE'} and event.value == 'PRESS':
            self._done(ctx)
            return {'CANCELLED'}
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            reg = getattr(self, "_region", None)
            if reg is not None and not (reg.x <= event.mouse_x < reg.x + reg.width
                                        and reg.y <= event.mouse_y < reg.y + reg.height):
                return {'PASS_THROUGH'}
            got = self._hit(ctx, event)
            if got is None:
                self.report({'WARNING'}, "Click on a part")
                return {'RUNNING_MODAL'}
            ob, loc, nrm = got
            if self.part is not None and ob is not self.part:
                self.report({'WARNING'}, f"Click on {self.part.name} again")
                return {'RUNNING_MODAL'}
            self.part = ob
            self.pts.append(loc.copy()); self.nrms.append(nrm.copy())
            need = 3 if self.anchor in ANCHORS_THREE else 1
            if len(self.pts) < need:
                self._prompt(ctx)
                return {'RUNNING_MODAL'}
            self._done(ctx)
            try:
                sock = make_anchor(self.part, self.anchor, self.pts, self.nrms)
            except ValueError as exc:
                self.report({'ERROR'}, str(exc))
                return {'CANCELLED'}
            kept = ""
            if self.anchor in ANCHORS_THREE:
                try:
                    if remember_anchor(self.part, sock):
                        kept = " (saved with the part in the library)"
                except OSError as exc:
                    kept = f" (couldn't save it with the part: {exc})"
            self.report({'INFO'}, f"{self.anchor} anchor on {self.part.name}{kept}")
            for o in ctx.view_layer.objects:
                o.select_set(False)
            sock.select_set(True)
            ctx.view_layer.objects.active = sock
            return {'FINISHED'}
        return {'PASS_THROUGH'}


class TIOW_OT_find_shins(bpy.types.Operator):
    """Find the Shin R and Shin L anchors on the selected Mar Fil legs from
    their shape: the ankle circles and the hole in each shin. Replaces any
    shin anchors they have, clicked ones and saved clicks included"""
    bl_idname = "tiow.find_shins"
    bl_label = "Find Shin Anchors"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, ctx):
        return ctx.active_object is not None and ctx.active_object.type == 'MESH'

    def execute(self, ctx):
        legs = ctx.active_object
        old = [c for c in legs.children if c.get("ws_type") in ("Shin R", "Shin L")]
        for c in old:
            bpy.data.objects.remove(c)
        forgot = forget_anchors(legs, ("Shin R", "Shin L"))
        note = auto_shin_anchors(legs)
        if "found" not in note or "no shin" in note:
            self.report({'WARNING'}, f"Couldn't find two shins on {legs.name}{note}: click their three points instead")
            return {'CANCELLED'}
        self.report({'INFO'}, f"Shin R and Shin L found on {legs.name}" + (" (saved clicks forgotten)" if forgot else ""))
        return {'FINISHED'}


def save_folder_fit(part):
    """Write this part's current placement on its socket to _fits.json in
    the part's source folder, for every part in that folder."""
    ps = _part_sockets()
    if ps is None:
        raise ValueError("Part Sockets isn't enabled")
    sk, co = ps
    src = part.get("tiow_src")
    if not src:
        raise ValueError(f"{part.name} didn't come from TIOW, so there's no folder to save to")
    sock = co.snap_socket_of(part)
    tname = part.get("ws_snap_type") if sock is not None else None
    if sock is None and part.get("tiow_target"):
        sock = bpy.data.objects.get(part["tiow_target"])
        tname = part.get("tiow_fit_type")
    if sock is None or sock.get("ws_type") is None:
        raise ValueError(f"{part.name} isn't on a socket - send it with the model selected first")
    tname = tname or sock["ws_type"]
    t = sk.ensure_type(bpy.context.scene, tname)
    base = sock.matrix_world @ Matrix.Translation((0.0, 0.0, t.gap))
    loc, rot, _ = (base.inverted_safe() @ part.matrix_world).decompose()
    M = Matrix.LocRotScale(loc, rot, Vector((1, 1, 1)))
    prefs = get_prefs()
    scene = bpy.context.scene
    unit = 1.0
    if prefs is not None and prefs.millimetres and scene.unit_settings.scale_length > 0:
        unit = 0.001 / scene.unit_settings.scale_length
    Mfile = M.copy(); Mfile.translation = Mfile.translation / unit
    entry = {"m": [x for row in Mfile for x in row]}
    # how the settle judges this placement, so other pads from the folder
    # land exactly like this on this model and only move by the difference
    # on another one
    spec = _spec_for(part)
    if spec:
        hosts = _model_around(sock)
        if spec.get("rock"):
            tilt = rock_settle(part, hosts, sock.matrix_world, float(spec["rock"]), dry=True)
            if isinstance(tilt, list):
                entry["rock"] = [x for row in tilt for x in row]
        axis = _settle_axis(spec)
        if axis is not None:
            others = hosts + _occupants(sock, co, bpy.context.view_layer, False, (part,))
            s0 = settle_onto(part, others, sock.matrix_world.to_3x3() @ axis, push_out=True,
                             touch=float(spec.get("touch") or 0.0), frame=sock.matrix_world, dry=True)
            if s0 is not None:
                entry["slide"] = s0 / unit
    if part.get("tiow_variant") is not None:
        # a variant is in its own coordinates: the fit is saved with it, not
        # for the folder (the folder's other parts are the other way round)
        got = _sidecar_for_write(part)
        if got is None:
            raise ValueError(f"{part.name} is a mirror made on the spot - its fit can't be saved")
        path, whole, sub = got
        sub.setdefault("fits", {})[tname] = entry["m"]
        _write_sidecar(path, whole)
    else:
        path = os.path.join(os.path.dirname(src), FITS_FILE)
        data = read_folder_fits(src)
        data[tname] = entry
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1)
        os.replace(tmp, path)
    part[f"ws_fit::{tname}"] = [x for row in M for x in row]
    if "rock" in entry or "slide" in entry:
        part[f"tiow_bias::{tname}"] = json.dumps({k: entry[k] for k in ("rock", "slide") if k in entry})
    for k in ("tiow_target", "tiow_fit_type"):
        if k in part.keys():
            del part[k]
    if co.snap_socket_of(part) is None:
        sk.snap_part_to_socket(bpy.context, part, sock, tname=None if tname == sock["ws_type"] else tname)
    return path, tname


# ---------------------------------------------------------------- corrections
# Every misfit lives in one of two places, and is fixed once there:
#  - the PART's fit (this weapon sits a little forward in every hand): saved in
#    the part's own .sockets.json, so it lands like this on every host;
#  - the HOST's SOCKET (heads sit low on this torso, whatever the head): the
#    socket is moved in the host's .sockets.json, so every part lands right.
# Whole folder: the same correction for every part in that folder (one kit's
# arms, its torsos...). Both sides: the other side gets the mirror image (a
# left hand, a left pad, the left shoulder; a maker's left copy too).
# The correction is the move you made, expressed in the socket's frame, so a
# sibling with a slightly different fit moves by the same amount.
MX4 = Matrix(((-1.0, 0.0, 0.0, 0.0), (0.0, 1.0, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0)))


def _unscaled(M):
    loc, rot, _s = M.decompose()
    return Matrix.LocRotScale(loc, rot, Vector((1.0, 1.0, 1.0)))


def _m16(m):
    return Matrix((m[0:4], m[4:8], m[8:12], m[12:16]))


def _flat16(M):
    return [float(x) for row in M for x in row]


def _scaled(M, k):
    M = M.copy()
    M.translation = M.translation * k
    return M


def _other_side(t):
    t = str(t)
    return t[:-2] + " L" if t.endswith(" R") else t[:-2] + " R" if t.endswith(" L") else None


def _folder_sidecars(src):
    """(stl path, sidecar path) for every part in the STL's folder."""
    d = os.path.dirname(str(src))
    out = []
    try:
        names = sorted(os.listdir(d))
    except OSError:
        return out
    for n in names:
        if n.lower().endswith(".stl"):
            p = os.path.join(d, n)
            out.append((p, os.path.splitext(p)[0] + SIDECAR))
    return out


def _subs(whole):
    """The part's own entry and each variant's: [(sub, variant index or None)]."""
    out = [(whole, None)]
    for i, v in enumerate(whole.get("variants") or []):
        if isinstance(v, dict) and isinstance(v.get("sidecar"), dict):
            out.append((v["sidecar"], i))
    return out


def _is_this(mine, vidx, want):
    """Is this sub the one the object in the scene was brought in as?"""
    if not mine:
        return False
    if want is None:
        return vidx is None
    try:
        return vidx is not None and int(want) == vidx
    except (TypeError, ValueError):
        return False


def _load_whole(path):
    try:
        with open(path, encoding="utf-8") as f:
            w = json.load(f)
        return w if isinstance(w, dict) else None
    except (OSError, ValueError):
        return None


def _snap_of(part):
    """(socket, fit type name, gap) the part sits on."""
    ps = _part_sockets()
    if ps is None:
        raise ValueError("Part Sockets isn't enabled")
    sk, co = ps
    sock = co.snap_socket_of(part)
    if sock is None and part.parent is not None and part.parent.get("ws_type") is not None:
        sock = part.parent
    if sock is None or sock.get("ws_type") is None:
        raise ValueError(f"{part.name} isn't on a socket")
    tname = str(part.get("ws_snap_type") or sock["ws_type"])
    gap = float(sk.ensure_type(bpy.context.scene, tname).gap)
    return sock, tname, gap


def _same_file(a, b):
    try:
        return os.path.normcase(os.path.abspath(str(a))) == os.path.normcase(os.path.abspath(str(b)))
    except (TypeError, ValueError):
        return False


def correct_part(part, folder=False, both=True):
    """Save how `part` now sits on its socket as its fit (and, with `folder`,
    move every part in its folder the same way). Other copies in the scene
    move too. Returns a note."""
    src = part.get("tiow_src")
    if not src:
        raise ValueError(f"{part.name} didn't come from the library, so there's no sockets file to save to")
    sock, tname, gap = _snap_of(part)
    unit = float(part.get("tiow_unit", 1.0)) or 1.0
    base = sock.matrix_world @ Matrix.Translation((0.0, 0.0, gap))
    Fnew = base.inverted_safe() @ _unscaled(part.matrix_world)
    old = part.get(f"ws_fit::{tname}")
    E = Fnew @ _m16(list(old)).inverted_safe() if old is not None and len(old) == 16 else None
    other = _other_side(tname) if both else None
    EM = MX4 @ E @ MX4 if (E is not None and other) else None
    changed, files = 0, 0
    targets = _folder_sidecars(src) if folder else [(str(src), os.path.splitext(str(src))[0] + SIDECAR)]
    vi = part.get("tiow_variant")
    for stl, scp in targets:
        whole = _load_whole(scp)
        if whole is None:
            whole = {"schemaVersion": 1, "part": os.path.splitext(os.path.basename(stl))[0]} if _same_file(stl, src) else None
        if whole is None:
            continue
        mine = _same_file(stl, src)
        touched = False
        for sub, vidx in _subs(whole):
            fits = sub.setdefault("fits", {}) if (mine or "fits" in sub) else {}
            this_one = _is_this(mine, vidx, vi)
            if this_one:
                fits[tname] = _flat16(_scaled(Fnew, 1.0 / unit))
                ex = [t for t in sub.get("exact", []) if t != tname] + [tname]
                sub["exact"] = ex
                touched = True
            elif E is not None and tname in fits and isinstance(fits[tname], list) and len(fits[tname]) == 16:
                fits[tname] = _flat16(_scaled(E @ _scaled(_m16(fits[tname]), unit), 1.0 / unit))
                touched = True
            if EM is not None and other in fits and isinstance(fits[other], list) and len(fits[other]) == 16:
                fits[other] = _flat16(_scaled(EM @ _scaled(_m16(fits[other]), unit), 1.0 / unit))
                touched = True
        if touched:
            _write_sidecar(scp, whole)
            files += 1
    # the folder's shared fits (Save Fit for Folder) move the same way
    if E is not None:
        fp = os.path.join(os.path.dirname(str(src)), FITS_FILE)
        data = read_folder_fits(src)
        hit = False
        for t, R in ((tname, E), (other, EM)):
            if t and R is not None and isinstance(data.get(t), (dict, list)):
                m = _fit_matrix(data[t], unit)
                if m is not None:
                    if isinstance(data[t], dict):
                        data[t]["m"] = _flat16(_scaled(R @ m, 1.0 / unit))
                    else:
                        data[t] = _flat16(_scaled(R @ m, 1.0 / unit))
                    hit = True
        if hit and folder:
            tmp = fp + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=1)
            os.replace(tmp, fp)
    # copies already in the scene
    part[f"ws_fit::{tname}"] = _flat16(Fnew)
    part["tiow_exact"] = json.dumps(sorted(set(json.loads(part.get("tiow_exact", "[]"))) | {tname}))
    folder_dir = os.path.normcase(os.path.dirname(os.path.abspath(str(src))))
    ps = _part_sockets()
    for o in list(bpy.context.view_layer.objects):
        if o is part or o.type != 'MESH' or not o.get("tiow_src"):
            continue
        file_same = _same_file(o["tiow_src"], src)
        same = file_same and o.get("tiow_variant") == vi and not o.get("tiow_mirrored")
        if not (file_same or (folder and os.path.normcase(os.path.dirname(os.path.abspath(str(o["tiow_src"])))) == folder_dir)):
            continue
        try:
            s2, t2, g2 = _snap_of(o)
        except ValueError:
            continue
        have = o.get(f"ws_fit::{t2}")
        if t2 == tname and same:
            M = Fnew
        elif t2 == tname and E is not None and have is not None:
            M = E @ _m16(list(have))
        elif t2 == other and EM is not None and have is not None:
            M = EM @ _m16(list(have))
        else:
            continue
        o[f"ws_fit::{t2}"] = _flat16(M)
        o.matrix_world = s2.matrix_world @ Matrix.Translation((0.0, 0.0, g2)) @ M @ Matrix.Diagonal(o.matrix_world.to_scale().to_4d())
        changed += 1
    where = "every part in its folder" if folder else "it"
    note = f"{tname} fit saved for {where} ({files} sockets file{'s' if files != 1 else ''})"
    if EM is not None:
        note += f", {other} mirrored"
    if changed:
        note += f", {changed} other cop{'ies' if changed != 1 else 'y'} in the scene moved"
    return note


def correct_socket(part, folder=False, both=True):
    """Keep `part` where it is now and move the socket it sits on to suit, in
    the host's sockets file (with `folder`, the same socket on every part in
    the host's folder). Returns a note."""
    sock, tname, gap = _snap_of(part)
    host = sock.parent
    if host is None or not host.get("tiow_src"):
        raise ValueError(f"the {sock['ws_type']} socket isn't on a part from the library")
    F = part.get(f"ws_fit::{tname}")
    if F is None or len(F) != 16:
        raise ValueError(f"{part.name} has no {tname} fit to keep - use Fix the Part instead")
    F = _m16(list(F))
    stype = str(sock["ws_type"])
    Knew = _unscaled(part.matrix_world) @ F.inverted_safe() @ Matrix.Translation((0.0, 0.0, -gap))
    C = sock.matrix_world.inverted_safe() @ Knew                 # the move, in the socket's own frame
    other = _other_side(stype) if both else None
    CM = MX4 @ C @ MX4 if other else None
    unit = float(host.get("tiow_unit", 1.0)) or 1.0
    hsrc = str(host["tiow_src"])
    hvi = host.get("tiow_variant")
    frame = _unscaled(host.matrix_world)
    Lnew = frame.inverted_safe() @ Knew
    targets = _folder_sidecars(hsrc) if folder else [(hsrc, os.path.splitext(hsrc)[0] + SIDECAR)]
    files = 0
    for stl, scp in targets:
        mine = _same_file(stl, hsrc)
        whole = _load_whole(scp)
        if whole is None:
            whole = {"schemaVersion": 1, "part": os.path.splitext(os.path.basename(stl))[0]} if mine else None
        if whole is None:
            continue
        touched = False
        for sub, vidx in _subs(whole):
            socks = sub.setdefault("sockets", []) if mine else sub.get("sockets") or []
            this_one = _is_this(mine, vidx, hvi)
            found = False
            for e in socks:
                if not isinstance(e, dict) or not isinstance(e.get("matrix"), list) or len(e["matrix"]) != 16:
                    continue
                if e.get("type") == stype:
                    if this_one:
                        e["matrix"] = _flat16(_scaled(Lnew, 1.0 / unit))
                    else:
                        e["matrix"] = _flat16(_scaled(_scaled(_m16(e["matrix"]), unit) @ C, 1.0 / unit))
                    e.setdefault("props", {})["tiow_corrected"] = 1
                    found = touched = True
                elif CM is not None and e.get("type") == other:
                    e["matrix"] = _flat16(_scaled(_scaled(_m16(e["matrix"]), unit) @ CM, 1.0 / unit))
                    e.setdefault("props", {})["tiow_corrected"] = 1
                    touched = True
            if this_one and not found:
                socks.append({"type": stype, "name": sock.name, "matrix": _flat16(_scaled(Lnew, 1.0 / unit)),
                              "display_type": "ARROWS", "display_size": float(sock.empty_display_size) / unit,
                              "props": {"tiow_corrected": 1}})
                touched = True
        if touched:
            _write_sidecar(scp, whole)
            files += 1
    # the scene: this socket (the part stays put), and the same sockets on copies of the host
    keep = part.matrix_world.copy()
    sock.matrix_world = Knew
    part.matrix_world = keep
    moved = 0
    hdir = os.path.normcase(os.path.dirname(os.path.abspath(hsrc)))
    for o in list(bpy.context.view_layer.objects):
        if o.type != 'MESH' or not o.get("tiow_src"):
            continue
        if not (_same_file(o["tiow_src"], hsrc) or (folder and os.path.normcase(os.path.dirname(os.path.abspath(str(o["tiow_src"])))) == hdir)):
            continue
        for c in o.children:
            t = c.get("ws_type")
            if c is sock or t is None:
                continue
            if t == stype:
                c.matrix_world = Knew if (o is host) else c.matrix_world @ C
                moved += 1
            elif CM is not None and t == other:
                c.matrix_world = c.matrix_world @ CM
                moved += 1
    bpy.context.view_layer.update()
    where = f"every part in {os.path.basename(os.path.dirname(hsrc))}" if folder else host.name
    note = f"{stype} socket moved on {where} ({files} sockets file{'s' if files != 1 else ''})"
    if CM is not None:
        note += f", {other} mirrored"
    if moved:
        note += f", {moved} other socket{'s' if moved != 1 else ''} in the scene moved with their parts"
    return note


class TIOW_OT_save_correction(bpy.types.Operator):
    """Save where you've moved the selected part, once, so it's right everywhere.
    Fix the Part: this part lands like this on every model (its own fit).
    Fix the Socket: everything lands like this on this host (the socket on the
    torso, arm or legs it sits on moves)"""
    bl_idname = "tiow.save_correction"
    bl_label = "Save Correction"
    bl_options = {'REGISTER', 'UNDO'}

    what: EnumProperty(name="Fix", default='PART', items=(
        ('PART', "Fix the Part", "This part is off wherever it goes: save how it sits now as its own fit"),
        ('SOCKET', "Fix the Socket", "Everything is off on this host: move the host's socket so the part sits as it is now")))

    @classmethod
    def poll(cls, ctx):
        o = ctx.active_object
        return ctx.mode == 'OBJECT' and o is not None and o.type == 'MESH'

    def execute(self, ctx):
        prefs = get_prefs()
        folder = bool(prefs and prefs.correct_folder)
        both = bool(prefs is None or prefs.correct_both)
        try:
            fn = correct_part if self.what == 'PART' else correct_socket
            note = fn(ctx.active_object, folder=folder, both=both)
        except (ValueError, OSError) as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        _set_status(note)
        self.report({'INFO'}, note + ". Run Prepare Squad Builder to update the page")
        return {'FINISHED'}


class TIOW_OT_save_folder_fit(bpy.types.Operator):
    """Remember how the selected part sits on its socket, for every part in
    the same library folder. Place one pad by eye (it can overlap a little),
    select it, click this - the rest of that folder then lands the same way"""
    bl_idname = "tiow.save_folder_fit"
    bl_label = "Save Fit for Folder"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, ctx):
        o = ctx.active_object
        return ctx.mode == 'OBJECT' and o is not None and o.type == 'MESH'

    def execute(self, ctx):
        try:
            path, tname = save_folder_fit(ctx.active_object)
        except (ValueError, OSError) as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        self.report({'INFO'}, f"'{tname}' fit saved for {os.path.basename(os.path.dirname(path))}")
        return {'FINISHED'}


# ---------------------------------------------------------------- polling

def _beat(inbox):
    now = time.time()
    if now - _state["beat"].get(inbox, 0.0) < HEARTBEAT_SECONDS:
        return
    _state["beat"][inbox] = now
    p = os.path.join(inbox, HEARTBEAT)
    try:
        with open(p, "a"):
            pass
        os.utime(p, None)
    except OSError:
        pass


def _redraw():
    wm = bpy.context.window_manager
    for win in getattr(wm, "windows", []):
        for area in win.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


def _set_status(msg):
    _state["last"] = msg
    print(f"[TIOW Inbox] {msg}")
    _redraw()


def process_inbox():
    """Handle every waiting request. Returns how many were imported."""
    prefs = get_prefs()
    if prefs is None or not prefs.listening:
        return 0
    jobs = []
    for inbox in inbox_dirs(prefs):
        try:
            os.makedirs(inbox, exist_ok=True)
        except OSError:
            continue
        _beat(inbox)
        if bpy.context.mode != 'OBJECT':
            # leave requests unclaimed; they import when you Tab back out
            continue
        try:
            jobs += [(inbox, n) for n in sorted(os.listdir(inbox)) if n.endswith(".json")]
        except OSError:
            continue

    done = 0
    for inbox, name in jobs:
        src = os.path.join(inbox, name)
        claimed = f"{src}.{os.getpid()}.claimed"
        try:
            os.replace(src, claimed)      # a second Blender loses this race
        except OSError:
            continue
        try:
            age = time.time() - os.path.getmtime(claimed)
            with open(claimed, encoding="utf-8") as f:
                job = json.load(f)
            if not isinstance(job, dict):
                raise ValueError("not a request")
            if age > prefs.max_age_minutes * 60:
                _set_status(f"Skipped stale request for "
                            f"{job.get('name', name)} "
                            f"({int(age // 60)} min old)")
                continue
            new = import_request(job, prefs)
            where = new[0].users_collection[0].name if new[0].users_collection else "scene"
            extra = ""
            if job.get("_sockets"):
                extra = f" with {job['_sockets']} socket(s)"
            if job.get("_types"):
                extra += f", fit types added: {', '.join(job['_types'])}"
            extra += (job.get("_found") or "") + (job.get("_snap") or "")
            _set_status(f"Imported {new[0].name} into {where}{extra}")
            done += 1
        except (OSError, ValueError, RuntimeError) as exc:
            _set_status(f"Could not import {name}: {exc}")
        finally:
            try:
                os.remove(claimed)
            except OSError:
                pass
    return done


def _timer():
    try:
        process_inbox()
    except Exception as exc:          # a timer that raises is unregistered
        print(f"[TIOW Inbox] {exc!r}")
    return POLL_SECONDS


# ---------------------------------------------------------------- UI

class TIOW_AddonPrefs(bpy.types.AddonPreferences):
    bl_idname = __name__

    listening: BoolProperty(
        name="Listen for TIOW", default=True,
        description="Import items sent from TIOW-FTRP's Send to Blender")
    inbox_path: StringProperty(
        name="Inbox Folder", subtype='DIR_PATH', default="",
        description="Empty uses TIOW-FTRP's own: "
                    "%LOCALAPPDATA%\\TIOW-FTRP\\local-data\\blender-inbox")
    builder_inbox: StringProperty(
        name="Squad Builder Inbox", subtype='DIR_PATH',
        default="D:\\Kitbash Library\\_builder\\inbox",
        description="Where the Squad Builder page sends parts: the inbox folder inside your "
                    "library's _builder folder (browsers can't write into AppData). Watched "
                    "only when that _builder folder exists. Empty = off")
    placement: EnumProperty(
        name="Place", default='BOUNDS',
        items=(('BOUNDS', "Centred on 3D Cursor",
                "Move the part so its geometry is centred on the cursor; "
                "the origin stays where the file had it"),
               ('ORIGIN', "Origin at 3D Cursor",
                "Put the file's origin on the cursor"),
               ('FILE', "As in File", "Leave the STL coordinates untouched")))
    by_category: BoolProperty(
        name="Collection per TIOW Category", default=True,
        description="Put each part in a collection named after its TIOW "
                    "category (Arms, Heads...), which Cycle Variant uses as "
                    "its pool")
    fallback_collection: StringProperty(
        name="Uncategorised Collection", default="TIOW Imports")
    millimetres: BoolProperty(
        name="Convert mm to Scene Units", default=False,
        description="Off: 1 STL unit = 1 Blender unit, the same as importing "
                    "by hand, so new parts match the ones already in your "
                    "files. On: treat STL units as millimetres and scale to "
                    "the scene's unit scale")
    max_age_minutes: IntProperty(
        name="Drop Requests Older Than (min)", default=5, min=1, max=1440)
    auto_snap: BoolProperty(
        name="Snap onto Selected Model", default=True,
        description="Put each part on the free socket of its joint in the "
                    "model you have selected (arms on Shoulder, pistols on "
                    "Hand...). Needs Part Sockets")
    replaced: EnumProperty(
        name="Swapped-out Part", default='DELETE',
        items=(('DELETE', "Delete if from TIOW",
                "Parts that came from TIOW are deleted when another part takes "
                "their socket (send them again to get them back); your own "
                "parts go to their Dressing Room home"),
               ('HOME', "Send Home",
                "Every swapped-out part goes to its Dressing Room home, or the "
                "world origin")))
    adaptor_dir: StringProperty(
        name="Body Adaptors", subtype='DIR_PATH', default="D:\\new cults\\body adaptor",
        description="Folder of body adaptors (lower_body_(torso)_1..6 with their "
                    ".sockets.json). Flat-topped legs (Marta, Turtle Ninja) bring one "
                    "onto a Mar Fil torso's Waist")
    stand_on_base: BoolProperty(
        name="Stand on the Base", default=True,
        description="When a base (or terrain) snaps onto the legs' Base socket, turn the whole "
                    "model so the base sits flat on the grid - so the pose reads as it will "
                    "stand. Only the model's root moves; the joints don't change")
    correct_folder: BoolProperty(
        name="Whole Folder", default=False,
        description="Save Correction applies the same move to every part in the folder (one kit's "
                    "arms, its torsos...), not just this file")
    correct_both: BoolProperty(
        name="Both Sides", default=True,
        description="Save Correction also gives the other side the mirror image (left hand, left pad, "
                    "left shoulder, a maker's left copy)")
    adaptor_default: IntProperty(
        name="Adaptor", default=3, min=1, max=99,
        description="Which adaptor flat legs bring (number in the folder, in order); "
                    "Next Adaptor swaps the one on the model")

    def draw(self, ctx):
        col = self.layout.column()
        col.prop(self, "listening")
        col.prop(self, "inbox_path")
        if not self.inbox_path:
            col.label(text=default_inbox(), icon='FILE_FOLDER')
        col.prop(self, "builder_inbox")
        col.prop(self, "placement")
        col.prop(self, "by_category")
        sub = col.row()
        sub.enabled = self.by_category
        sub.prop(self, "fallback_collection")
        col.prop(self, "millimetres")
        col.prop(self, "max_age_minutes")
        col.prop(self, "auto_snap")
        sub = col.row()
        sub.enabled = self.auto_snap
        sub.prop(self, "replaced")
        col.prop(self, "adaptor_dir")
        col.prop(self, "adaptor_default")
        col.prop(self, "stand_on_base")


class TIOW_PT_inbox(bpy.types.Panel):
    bl_label = "TIOW Inbox"
    bl_idname = "TIOW_PT_inbox"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Sockets"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, ctx):
        prefs = get_prefs()
        if prefs is None:
            return
        col = self.layout.column()
        col.prop(prefs, "listening",
                 icon='LINKED' if prefs.listening else 'UNLINKED')
        col.prop(prefs, "placement", text="")
        col.prop(prefs, "auto_snap")
        row = col.row(align=True)
        row.prop(prefs, "stand_on_base", text="Stand on Base")
        row.operator("tiow.stand_on_base", text="Level Now", icon='MESH_PLANE')
        col.operator("tiow.mirror_part", icon='MOD_MIRROR')
        box = self.layout.box()
        box.label(text="Anchors (click on the part)")
        grid = box.grid_flow(columns=2, align=True, row_major=True)
        for a in ANCHORS_THREE + ANCHORS_ONE:
            grid.operator("tiow.place_anchor", text=a).anchor = a
        box.operator("tiow.find_shins", icon='VIEWZOOM')
        box.operator("tiow.save_folder_fit", icon='PINNED')
        box = self.layout.box()
        box.label(text="Save Correction (move the part, then)")
        row = box.row(align=True)
        row.operator("tiow.save_correction", text="Fix the Part", icon='OBJECT_DATA').what = 'PART'
        row.operator("tiow.save_correction", text="Fix the Socket", icon='EMPTY_ARROWS').what = 'SOCKET'
        row = box.row(align=True)
        row.prop(prefs, "correct_folder")
        row.prop(prefs, "correct_both")
        row = self.layout.row(align=True)
        row.prop(prefs, "adaptor_default", text="Adaptor")
        row.operator("tiow.next_adaptor", text="Next Adaptor", icon='FILE_REFRESH')
        if ctx.mode != 'OBJECT' and prefs.listening:
            col.label(text="Waiting for Object Mode", icon='INFO')
        if _state["last"]:
            col.label(text=_state["last"])


def find_adaptor(ob):
    """The body adaptor in the model around `ob` (or `ob` itself)."""
    if ob is None:
        return None
    if ob.get("tiow_category") == "Adapters":
        return ob
    root = ob
    while root.parent is not None:
        root = root.parent
    ps = _part_sockets()
    for o in [root] + list(_descendants(root)):
        if o.get("tiow_category") == "Adapters":
            return o
    if ps is not None:
        _, co = ps
        mine = {root} | set(_descendants(root))
        for o in bpy.context.view_layer.objects:
            if o.get("tiow_category") == "Adapters" and co.snap_socket_of(o) in mine:
                return o
    return None


def next_adaptor(ob, prefs, step=1):
    """Swap the model's body adaptor for the next one in the folder; the legs
    on it move across. Returns a status note."""
    ad = find_adaptor(ob)
    if ad is None:
        return "no body adaptor on the selected model"
    files = adaptor_files(prefs)
    if not files:
        return f"no body adaptors in {prefs.adaptor_dir}"
    cur = os.path.normcase(os.path.abspath(str(ad.get("tiow_src") or "")))
    norm = [os.path.normcase(os.path.abspath(f)) for f in files]
    i = norm.index(cur) if cur in norm else -1
    path = files[(i + step) % len(files)]
    unit = float(ad.get("tiow_unit", 1.0))
    job = {"path": path, "category": "Adapters", "_unit": unit}
    new, meshes, s, made, added = load_stl(path, job, prefs)
    if len(meshes) != 1:
        return "the adaptor file is not one mesh"
    note = auto_snap(meshes[0], job, prefs, ad)
    prefs.adaptor_default = files.index(path) + 1
    return f"{os.path.splitext(os.path.basename(path))[0]}{note}"


class TIOW_OT_stand_on_base(bpy.types.Operator):
    """Turn the selected model so its base (the legs' Base socket) sits flat on
    the grid: only the model's root moves, the joints don't change"""
    bl_idname = "tiow.stand_on_base"
    bl_label = "Stand on Base"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, ctx):
        return ctx.mode == 'OBJECT' and ctx.view_layer.objects.active is not None

    def execute(self, ctx):
        sock = base_socket_of(ctx.view_layer.objects.active)
        if sock is None:
            self.report({'WARNING'}, "No Base socket on the selected model (legs carry it)")
            return {'CANCELLED'}
        tilt = stand_on_base(sock)
        msg = f"Stood {sock.parent.name if sock.parent else 'the model'} on its base (took out {tilt:.1f} deg)"
        _set_status(msg)
        self.report({'INFO'}, msg)
        return {'FINISHED'}


class TIOW_OT_next_adaptor(bpy.types.Operator):
    """Swap the body adaptor on the selected model for the next one in the
    Body Adaptors folder (the legs stay on). It also becomes the one flat legs bring"""
    bl_idname = "tiow.next_adaptor"
    bl_label = "Next Adaptor"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, ctx):
        prefs = get_prefs()
        ob = ctx.view_layer.objects.active
        msg = next_adaptor(ob, prefs)
        _set_status(msg)
        self.report({'INFO'}, msg)
        return {'FINISHED'}


classes = (TIOW_AddonPrefs, TIOW_OT_place_anchor, TIOW_OT_find_shins, TIOW_OT_save_folder_fit, TIOW_OT_save_correction, TIOW_OT_stand_on_base,
           TIOW_OT_next_adaptor, TIOW_OT_mirror_part, TIOW_PT_inbox)


def register():
    for c in classes:
        bpy.utils.register_class(c)
    if not bpy.app.timers.is_registered(_timer):
        bpy.app.timers.register(_timer, first_interval=1.0, persistent=True)


def unregister():
    if bpy.app.timers.is_registered(_timer):
        bpy.app.timers.unregister(_timer)
    for c in reversed(classes):
        bpy.utils.unregister_class(c)


# ---------------------------------------------------------------- built-in Pad references
# zlib + base64 of {"Pad": [{name, side, points, pivot, region}]}, file coordinates (mm)
_REFS_PACKED = (
    "eNpVfU2vrslt3F+5mE0S4MxFk2z2h3feZpPAW0EIxtLYkm3NCDPjOIGR/x6yiuxzpY2kc+55n/fp"
    "ZpPFYpH9n9/9rx/+8ed//+27v/vu73/5y69f/uNPP//645f/+cMfv/zw0x/+9PMvX/76859/+u3X"
    "Lz/88uOXf/3p5//46euX//Hbn378JX4Q//rnf/oS/+fLrz/85ccvf/nhX3/88s8//pY/+fMvv375"
    "x/8bP/rtD3/680//jH/0lx9//VP81c///tMf8f/5wV+/+/gunvbd3/3uP7/7KT4mvsde38dX+V6+"
    "/4fv/z5+++uf/5g//Yf4n//0y89/if/533/+9U//5dcvf/3h3//tj7/8/NOXH//PD3/567/9+OW/"
    "xu9/+u3LH37+5acff/n48o8//OFf3//57ee/5jfKB/9LPvi/xcfxG8Sjf/e9fhU5H/J1zWsfNr7K"
    "cf39x+++t6/z7PkR/z2O+Yfp1yNz52/867DjH/GHeu+H+dfrcn7/+/jUP//vn2M5f/f9/KrL18f3"
    "I/7lzT8V1/jQ73758Z///PNPeOz8etaReK5O3/lc9bXy0+fXO4Z8jK97Df0w+TrGnvGL8XWus+Pn"
    "a8RH52eOiS86vrrP/IWcfFj8/ZXFN1DTeIP4pyb7Q+9X2+fmb+KpsiweHn+Bh98lm7+wpTdebd6N"
    "zzLf9ZBlY3/EP9g2zofFZ9+h9Vnx/vEntja+77mrfn625xqIrZtP1+3G3/i4Hk83ORdP1/5FfIbk"
    "kp9z8qN838mnm81crLtzsfSrr2v17jI9v9YY62CT1t58+dgj+8hdG/iF66xfqMTCx6qMWMH8zdwu"
    "+RuNjXQspB3NL+ybfzJjp/EmZ4piVWzcWpUbfxH/PW14moKM1Qs5DyxgDq23vxvbOJbnq5jbwjrG"
    "KtW+b5nx9DkFNrPWqKebHcNHbZH8qFj5w4dM9TQVHzZzvaZhWeJfyl0wIbz6kjP56q7x83jR+HcO"
    "Yxeu/Pzqc8aX2jpX/tyvlqGY52LFT/aZH3q+bnfnZ915sSh7x39b7pk6/2ZZPvzkXsaSHLEylKFp"
    "JzPPW3yr+OplWjtPQhqMT7z5VZF6xo5Dia06sNMwx9qqIffgTY5iS3b8oJ4y493iN3p05/eK81Wb"
    "5ZY2f9fAYnlYTJnjGWkpQ+bJLxxPP2V1c8LmLV81HhLrXB91wmjS5s9UfGPBYYgFHWEhkpsu+Yw7"
    "uPLxL47HR8QZja8dnzRVy7JjlcLYvqoOnuq1je++z8BeLXOYaXgjPiN2/8CABp4xfZyykyNpDSZL"
    "c7GG7zKgObEjU/IZK1amjts6g5ubG3Nip3jcwjftLTRrgT3MbVJf94ShwGfeXNy9pP/kxk/iH9wj"
    "PNRn1KtvC7+UG3KNG29WHnbcPAPxzpPLu5x/cWbsVHrgTQcx1yoDjvXNxTqLbjVOHf8ijGnFmvgM"
    "K02PrHx4rE64aJjk4flc3os1NH3QzJMT3155CmNnh+M9BpY3rGFKbYhuC4OKh59NK9V6wYgL8WJh"
    "eGr5WUNnPSMco+XT3eKY5vdt12g7liK29l6YqMi8HXMmzDpCAJbkjF2Obkt60fgSQqelu5bkjrD3"
    "WO88EHlERGt3b/qm9Jn5fT3WZnVg0/TU8VGT3uz2OfSVhhWrC8NSno8Id4qDM3b+PA66H213PXA8"
    "Z/gVmDv+Ik7BvOnJIqIhIsT2njoFK85kvMTEPx9Yjvx38UUQxxYD7VLlAm6EyGsKVxl7KPx5eNl8"
    "wHLDN4ojXQt74vXzG52z6F1tlYO7E9HTLnfCtIPngheL8Ks02/b5d4TphD1sHuWIpZsvEcfIEO/C"
    "wVvupdKx+0X0GK54C9X1vO7GusrCDi3lt83DJLTOoYvuQmuh1k13G54bz17HpJ3CokNMswW8aFPb"
    "l2sYRxVrONvQV+zjBzbXYAZ26sTWZsSRwpK0n4wDexTBYEXMDXcxwsDKcO6FPe9YjHJJhCaea5Wh"
    "Xh3gII5ZLe8laJG0lPjCR29tYaIbyV2hc/NTD18TH7QuQl2csfXCOX5j+Qfhw5RnKb+E57cN1ERj"
    "G1NoCxInIfeJJ1wXA0S4mTxCsT9w9/EHq/59wq58uTjOOHpxquuDEucFgphcqL1nRYE9NqK/pX9N"
    "Vzye8aSbzO0on3fXbnS38jfxfQOuYdnvqT23nWc/vlCgnnTH7r1TEWLT7Q0i1DhOdZBPxOAPIli8"
    "Shi7MP5POh47x/knWv57nE0HYxs7NStCxVu65E6dwyg47VQUnPGascByeJrnPM8vrAvAsnkKp9Y7"
    "egYz+FAD7lybxpioMcwzfkEgEwe//J7lm2QkpmMfs75U4GgGc53wlAEDGxFGpPzAJzrePdazoIHc"
    "OE25wkZXGfZRNrcvD7vv8A7x/O3jdsBbGSEl1y32Xgr/WJzAawyRsQhhd1LOL8GAAHkGzsFGmrd5"
    "YbNibZw+sZ2Zuh5Yy07IEh+l/fS7F1z4LgOrkzsSnWNnLiDkMStPE8cFp4T/Xt8yLkm3R/cYqzUq"
    "FuR252rlWmwY97inPGYccqxwvI7h+95bfk6v4tXj6BIe7FUWsTOAZJByJAkSSKOev6cx7TnY+Dju"
    "tV2xSs5A7HAdQwupboHR2/JvTTjN7hygGYL0+Pd9tCYyFB2HJ2tL2VbgJcW+61DGTuczhiNYAALE"
    "q09fHVI3zVR4SsIc281GkoX0aHOnZPTp9YFzfW0Tgex2Hplt5LdWGIPOWvhjNLnINYi9Ag3VWt0J"
    "fBenBqY9zu0EJb4Y4q3jT0x6eW3mImXAxoHbDzZ4pqixePciLJwr2h+lm9iLSePep3x5bE064IA5"
    "fEg5lYTBmvEiHDO28BYqS2sKr59nZPEv7NaOBC7Knbp3EP/4N3adqCz8hNOuhe7JcocQa7FYkXZN"
    "ehTJSJ+/cCz7bYMzvYfLrjhUs1HnSK+fME9e4JH+E1tAPwp7s7mJnhPrwrEceDMdjQ8SOYQt3Ats"
    "Eut2Oo29cPIeJhHrEeC6Eo1wOHj23gvvHYv+gh62w+EZZua3tYQZkWJ7bG5SDaod9DaCQiCmjSxr"
    "ttOIBCO9ibsCxFll3TNzE+yfKT4rkFCnJocn7XSiPr1Cq12+Sebj8D9av4gPF6aFceQSiFeU1vwi"
    "h0a6AXrHvtzCyFcuHg+A4toARWzS+QJPZdD0cuXxEIAdJAqgKWx2UJAE1pF9OPPxIjwi4mBVIl9B"
    "xjbKm6THq6PuRPXSOXRnIeHpSWwcKWc6hzuyUt8EsauR01r4k5MUQ35j99r5lQhP0tCRhQSYr5c8"
    "zriPRUg3J6OT4pNMSywX4bvY8w82CZVzp5Ml2aPCfrgzWKSBKDgAtRWrHdhpb6KLCIV13MPfwmeP"
    "Y4QqlellOpO8U66lw0XMNbiWulQ+ymbzJU+/fiBKOGAc3vRXp+mItJ+0FlfmVE43FJ4UYX+lMcfP"
    "I9/usJ9+FDuspG8CxZVNGlkSGZeQq1cy/Gm6OktUgtTJyiRlD7ziqdQiUtXyNuGf0tsEzgWuG9I5"
    "4JXb2BjoYgTWKQNLQJv2JPRcPmvtA9lgh0EexYlYHcRHgsrwtIMLHPl/+/OV7xged6mSkbi9jweI"
    "Fhg5fzHbT2gc/8Ty4FZg5nXqmfeAG8ApssdIiADXXSPqWdK83UqqL9dNBUs8tb5wYEdk7JHHAr4F"
    "ZKinRNYGn1q5/x71JpY8zPfAPGC7AkNWWhdZN1g4x8p7h8tIToDRzJ3v0U745ipmiB4wiHuP9iMc"
    "3iOwuSFgjQ6LlWJIbn88Q8rf4Yzj/IrAEd4HLe5dWJOR1pdbUo4FBAm8194OBLPM6ouJ0Nlb2jgw"
    "7S2sEF8ef7PiKyHKBcTvlzGgXdidh/21eZ3AUOmJjb+Ig9yRdBBvBm6Hw42koM6WDM3P8nQTmWhv"
    "HuA4M/gTHIjJzHZ3GHIFtFqESSpa7x9g4MJUBbExAnrFs8eykufcneYAJeT2dRjYzLbjiDE3ELrI"
    "wKvFXREl0eTCBKT94+XrTWLzVdxKBt9FlujEI9INzsbGS/0SEeD19vXK4uKMYhfJJHxCnvhTvMXd"
    "+KT1ku2IXgzwaSmZFOk3cK8MYjBozV7DKXjzNQ0hXs6saOaZy6d1JQuXiPZohaBAXGRqjiCi2PsC"
    "loaQ/MCBoexLKOhIwZECwtHXPsWr+wXiGlcAVcKPdWhciEBmjne88skP0KHagudoJ5jLCOLg7I3j"
    "EyZfh2QpfPZJtjGPokt928hhF/0pvNNaq8n4CUiyAR0zDEqxRMkZJqeB7xoH9lUOkiIysij7NCO6"
    "MlQDMayqAvhzAk47nHTYnwyLZY7PQEL+wysmrc0stb7SbHJVFxOlOAo4N5GhNwRdN7/W2HTLezU/"
    "P0+uoGw+IT3Vi5RIodYlehvhyWttLyoKK4sBBjQ+mxACC7bxhpG1iZXthktIN27Tef5vA0Qn+WGb"
    "jKHv0UEs/F2WIKYCDSx5FZ6DcDQBBaTqNYla6BYG6gzpDHf95rKctHcmXicZshekCbeW4LO2jLKE"
    "pJ5x0tLTwis6sTeg9wSQTo/cNGK4NQc1t4CC4rQ3L1AJYubE8FX7xftcQrhXuWTaVyGEiMST/DHw"
    "0brtke/M0koShEAb8k6zJzTIKLoXXMbVTrmWkAcfQIlJdjxKL0mBtGkzVovcnw8HoT8QI8fpStU5"
    "eHo4MIDpspLkVzb5lb1poE3OBzbEszfqD5kcF8ESKSPWPfBVZaF2GoGCXYpHgDk/RQklcljJ+W4k"
    "Q3nuVjlwHP4xlWTF9DrkNsBrJeKHRzqfXuHCsXdQLXJ8ZGGL5qPHyUh4nf7Y5sNlJ2U5Gq/qTSvP"
    "MAPf7m25ARqcuN/g9obMzjsy786txWflGeyDM64B4M/BcDfuI5aTBcstzHVm9YOxiH+gpkWDV4ia"
    "mXen6Q0Y6Sjgm0wcCec1NsBfeN1OudyqRKfFF4z7nGXinwi5gDnhfaxrCUdRLiEZFQiqab2sqqUV"
    "OzdX5ZYLR1k3cb/DrvM4FvgLWJV7ckVZzG2EGXDx5gJPg79cnagsgWt34MysdJSTGRmdrUqj8fN2"
    "DYEakVHip4FwXs2QCMcPv+rapws1doouJc1YYHhmiEvv43tOrkczr2qsBq05GB3tdMEgT1g6OAf2"
    "sN3ccvjKfO3tm2h0NyYKV5AnaqcnR4Zv5RkiKwe2DMfMClljiaMHhbOtDHW7E+Bc2dz6mwcq/e6S"
    "Vz2i+wER7/G9my+NuDhpbySVYtnKzdxFmHyq+npMrO0ajnFnhYlkZoEGTTedRUojrvdGE6AQWHTF"
    "nsvsYlRg/48sEJHhjcVpwG8knAIoLiLlxkURT5EKOJhk1BLq/ecB7Iw8n2S8tJPzhdRpL2aHOm/X"
    "qgGtI9HDEQlPX8/oU3gHedFDIhchO0GDKAH/fDXsm1Qm6uIkRfy0xyzIMrPsllimFnEz1ZnMZ7zP"
    "vyaazVUHuZKBo+tBRiJTcQwC1VYtM4skFxGEy66AVfVhCdEqLMG7e5fJs1qoYAmwUlWfQ4YPGO4s"
    "h7tLJ00DriGcH0Hc7erywrFKvMGEdbyiminP1UzvnEY3ura1nPRGVhRRKO9azsWayODqmjWwFkbu"
    "Ktis0dYbECXXNtJtmIKO/laevuR7JPWbNN+jrw+gJUAyYN/u4J1uIKOQMQFat2uDJB8law55QG//"
    "RYQGKRxHLFXOF5EN3lpZytnFziVYxGFzxvRh7XmvH3xfEYLFeNMuoWWJg4Uv4JlF4AnphVTmCxM6"
    "hdcG1icJp8wHkvKQV+83JkBwmVBtFOWyJ9KAbcY8R05X1qeRVwdu8bBaKdsK/111Ezq0J2lIkoMS"
    "hYOFzGyraOqUvUhV0dK7euEWnaga7U1lyCyS01hyjl8frZBb23siaOTh2QrnEFljVxpIfupKV77A"
    "+jQ7Z9T3HFaez8scWtJwWNVc1pXnnZgJLijMLldeRz9eC82NAcuOFLzLvAe2chZJrUj7Gtk7s/WI"
    "fsDKez82lSS94F0U+S4DPqP0zHJPYpcmCpIbSU6ctdaA86sFLjiHkQdpmUMrX9K153HTBWcWsavc"
    "wFks4N8UGeH8dAKvqCZnwMMyrvbX50BtIArC208T3uugsr4BtDLsraaN4j9M0rG4u3P0IXCwkY5V"
    "ptwwMnkAVDWNLK6+wt5BrWiSUyhjm6S+NgtIcUIb0h8yNpYZeRZH5RNNkIKYhwDBTh9m+KQBgUJY"
    "7T3WzEgWaDIM7gJkBRt2ANbM3OeEEYaXayFFlily5w6DROVkwK8Qlyyi7XMWi1TCSu5xBUwNpNLc"
    "z1XQve16vPVt4NPzKzDRELeXF23lEcdeh4Nv/OFVdiZKXYUaEvBCpmKL9YLVxPEB4ZKsAqK8vWKx"
    "az48E6LiG8UbVS8y2qco1VsGNfNxFJId7nc4xqpJjyx8pNPyxWBwGluucJsfqOgfSt/6TajkSmQH"
    "KqW9yEivBokFwf4jLJbCUx1U/GKjpI3zzIU3GWLAtXY6XXP43AF5R7owq3e3yNCx506hyG5R2Lmr"
    "zjflV+GVu5aJgJJoFd44vrw8VhHiReX76ROYxflsZq+ygy6xoq6eZiHwO5G1tOTFHe94D8WIc50u"
    "Z+ZvMs4dQq+lrcw80L0drwLS7rCdNRrka6zHmzeJZXk2QGKxmHm8s3RPJhAUIRKwOEtN8t+BXyCi"
    "JwRoR7LFk6OLs+NVYHnKGuz6SRKGjNQqLeBl3GZR4JYEI1Eb6xgsusfDPzmFc+GtItmbxbN0pWgx"
    "Pg9uo87OPMMaFZnkpFx1LGnTZnGSOqxUIOxO4CEUzFMtp0CIN4bFcT84JzCN1Zw1Sw8VuJ9/WBWf"
    "16ZoxAtqZJquSPOG0S36q63PQWGMZdoD4vbFFYoO121h7cuEFPU7x6t4VhyeThHuxiDbSvpidZag"
    "LLptF9YOVVaz05tSEMCAXJdhnb4YC0+LrErAgdMiMB4vTc1XEpXWWHKS2bi6VlW4G7StPCrDWElY"
    "r1TlWZrNCuYqMrR9sF+GyVGCqDMaak1l+RmUDAqIDY8ChSyoho9Qc/Uq8oPyzXGxYDKfoCxVEsm4"
    "ClHxk/5d/gUhWBaA1kNaFz5tw1amtfJvQN2T+wvntcoiMxkHXxdpmZK1upVpOhQayWxaVfaaMef2"
    "rs067xm3TEWcDNhA0SmzgFYYhe8RJELG5IUYBLLHu6lxBp6JeFRvfvKLgi0UxJPzJNYyQQInP5eO"
    "qJNsSaNKApMMVJzSpnST/gGIVrrz0ZKdwp62iYD0dj53lrFItalDL5lN/pNTjPIlAXae/Gd1alw0"
    "exfooFvXQxYxjkqLUAcSvTAJZ1rc5G3WNKBaZW3BrTn2BLfUWH0bq9Oq0zjhhtxKolkgyDdR0DzY"
    "9PDddarWgqwhPouVs9tqvutQak+hTKDLYBnKWGfdc2yyUEee1+aajIJ/r0wjqWPJ00bR/q4yXPqU"
    "1SpDbOJ9pHYsFMgVUHb5jVvvtlMF31LQhQyjNZd6INo98M6nVXhzstQH7wStXb1hyu0h+GvN4COO"
    "0vcRyoP4SGFJGTah8hCq+u1VbMc9Ra46rVTb1cVZIAOns4qAWzo48Df3MgtVfSomNhs4GwHsdvYk"
    "Ts37vqRw5MGIQWwz00kiNLSnvxuaAGCrRCTzJboMi7JI7TTjcimwXPXv9ZPZMJDEqG6n+tofbz4L"
    "Q+C4yRNSMiffKX9JxDO6ZImSi1CEA+Vxc38sVScbzj/xSnYyKlBsb5eF1JQHPDU4BTvGzG10fhY/"
    "h75TmXBEdt765jzSiSUpOh1S4on0UZDakXWN83v7vC26LFbpAz72Nu2xoP6lEkBbenONBJwYC9jF"
    "U2Tpja+xQZPkadwke9aggmlsFvxdm+iyS4n6fDLfz8YEAnNV7NQulkaY0CCDYoUqnFp/YQW5ug5j"
    "2N3PrOEwUlZNDdPS9QIoxegQXSU51jwtZFoJ1lkcjGfsVgeS8GbvTti7aLuUC/I8/S68rHT9HgJ8"
    "sHhIoc6RWrBhrF8pxMkTfRtdWt9QjhQ83ndWHLkoPCcrTPjms0m7yMxAJi7C4yaJ8tBAjAvprTGg"
    "l0WAo1YKu5aNPrd7QhnosKw5mn+bDu7xdJnYuyZjl6rE8GGUhqzbbTqJAjVFGbtU+FXKSAIq0wIi"
    "Gi2910ypP3ocqrxiYv5yxDxVF6rTbE9pPDlMiEIylaayvOsJl91D2XRBbrldpiIozEEZUyCaRkcb"
    "GnL2dwzkR52UjIkgNrEmkUJbk3Ys1hxtrr3TRKjDoHG5i1JnfYLFna5JwPOl7fXCX+hPcjnYcbRm"
    "g0Oi3PCbTIn8RTFhjU4PEbCt19CVZY/c7M2QdO0xaqylXJQz0oFepsLjwHx9MIgFGP+Ug6EAkVLg"
    "hIbrkV2LjJo7QUJk3dpKGkQ3Bdaip2/lJxj3CuCm40URMM5bS6yzn+QMVpsJsVZZtmkgpvpjsF67"
    "j9TySipb8ttRwCpNcXqddVUSHyYNnM6kQABaZ+kmIcgbDFRtgVJdDzyQSTwUj6k3/IvIWuTuZQbV"
    "/ENK5chwliRThrSMci1KwIkqVim9M0cAqT6TQkLCuZv1zad8TzAMwUq3ebkQl85J01r+olimyCAH"
    "WFTsYhH0kof+jKR3hwVhg989lKNa9ZFky8mmnGLe8idWPULp5rDHqKDFKjb/sFgJhJ4vy96dPl7Z"
    "VLZerSpAUyNhPwCBK89wBnDrviKfm8CfXzdwdCv6Uu2WJB19ioynfk/skkbII6qnE06FS9l6qIdR"
    "67TKT1X8aBC32LA0XGFdWFjx02ENDtP34YuzJnY6R7QkTYRImwiwi98b6zuq26hLZeoo/URwPTT4"
    "6d+odHKxwOWyl+BBVnjyzUrZaE2KL8pR1Wc5hyb7/Fa72oJlh1U8R8cCIaoAYRlNAOilOIsf1L4k"
    "sA9eejgj3uiU2YRZwgXflizK7PavVPTQ7NkJ0ZUindSfbWitIH3tAk8p+TaqFp5W0np8SL8zCFKO"
    "M0u5hfKukG5nD1bs8e1OmkUV1mG1U9R3F1NQ2vdiGyO5W832D0pVhV420GkX3lNskALs5dQcuDe5"
    "LLvyVpz3cIhNy0AtmU13C8Z1HivkhnrunuQP/cgLyKRy2duUXGw3PVxVRy+mliS2k6uAGOgLuofF"
    "hlYKaXVJoJcQAqYj5etYGtqTbUHx7bRLSTDgCbjF9s+KvBT5nUmOIYzqvrNgPKIspVv7lD0QFgzP"
    "yJ7A1aXIkgKzqjlqsxw9G1lzovrPP2kUp/iPFPOqByTopkgpzifwXJemjQpOkLQlarb+rO1eirIi"
    "xKUV4MouH8kiVBrE7G0nRThy81Gt6k4wAFDKG7nup4GxlHb3eClmpFuJtQ6KsBr4FMKHAeMI3zHA"
    "eMujB8zkCstr53Y5+xpWJZn8zzJS9q0ZSlIod86M660oRvU7JQiw0Kp6oQkYxU40O6yk4R7wB+dy"
    "LqXR9GS5XcrtM4K2Y0e6YLKQlu+UMRp0HBXv3cj3sMZrTx+RBb7ccdQhw5etufrYzizu3Es0Ff7k"
    "PFk22hoHiUapnDE7Fi6w5xmXnfS7O/+8CvWT8avF4pp5ahJvRLFJzr6mNRD71kiugYMtcE0mbMC4"
    "ozUjnkVRyIO5GatwS2acCKs2WW84923TZhUScTf3aXqtSXGsNymwTBu15WRaiie45Qn+m2dZqWtw"
    "MolzDflGkEd7pOz8re7BWiUnkTFqtQ5KkAmEVTsrNtKVi6y7ZjJSgLRqv4nG2fqhpxTn34ggmNoL"
    "hdKnMtnMxZUqQVb61mjMNPO90ivQH9oTdA2HpGoN6iBN+lxGSK3wzEB1V5suAxIKxnRWp5XS+7LZ"
    "KnyqVA29zsHAuc++IlaS53xyK3YVRDbDgopPr7SmQQDFRaO7wCdKd6AQMkNvFXGkPzhpTu3C0GZj"
    "FWREmB03Vp7LZbN1toWkiWxt+CxoauZch0yN/ekv0A2jgLCpIG8Qp6WJLZo0Eu/Vgq6LQ76rVdDe"
    "np+LyD0ue9l3VRThWtLeRusW+miGC9OPagxM5VIz7aYZSrIYxFYV60z1GrOpxYpiePM3cQHAZBcD"
    "/slT7lLd7MsG2G3WibKzZFGgr3Y1Fw9q1VvV0tfBAjQ2UtiMlLBzW6boCXEm9cbjPsXvNh6mxb7Y"
    "0xEzvHydAsoG/Ckgko3ML6WsC2hnawMwMDWYpKV2l6MmW14i0JEEHs3pohBUXTTQIZW+1ajmPIdG"
    "6/tF/gmN+U0mDVq1W4hs257kUy5RXClcs+SMlu3qr9ViGpKqBp8hk0IcZ09Pglj8vNQzps3bTrQU"
    "Z5xw9qU2yyFzsBqyOKHglpYgC+bVY3WrjavzQXRPJGxuGcXrVyWpKJddHXK7jWuh3eIedg3tSguS"
    "/bw4M/CeiW1llfdk4MUhyya65nc8aQEW0hAX12fzJQSeY1U9rTs/FRX7ufgK4eBf3sHE7iiFzs15"
    "oV4CiY0SHk1/Si0o/dzZbrwe4+V0ODNLMGhV7Q4MmSgkinixwk9zZmzV8kNRC6sN3i14jg5l9KD2"
    "bk+IdBfZ+HjrLktlKokC+SP1ugSzYeXS0X20AiA8AWozzu32KqhknZOF2nEn3JE/z7mzpQ67taj0"
    "8e5kWcYPq1EV8WFltpI6Huj9SRWNntuyB0vLcbgpCl/WYwsGmkvdaoJGf1RkX7tyXaEMRZqNT1f1"
    "2SMX9voODacppDY07XA1bruXqHhvwKo48k1YzIMOSxcaomvnb+OU0NqLStZP/ItOuHQ0yXTe9yeK"
    "/vMxmQuGTbYyiFJrT6UVRpe8/D/5MygKteT4bGAVB1WjBSf3aHGkLqp55mIL4vj8Vofp/Dyc9LJf"
    "K/A0AkGhZueuTqivwhvLJFF01mN5s86EFsNTgyQa/UKNLw2YX0wuUbpmMwIlm693F8o2ZW+gPGmC"
    "Zo0dpA9bzU5XNPZgd1pWbeHfrKkPPBxmqlZVkC5mLa+nsM/QZovoL5jOyG7ZdHTnpw4QYymWMKmd"
    "1v2oF6EIjcLIHDvZOxDkZ7ilKvSUkCPrdwzNUiLI+8LaNhqwOsHu0a6EeDZ44LBSy1nyfgyemaWQ"
    "pgi8Bp4gvalWFiZXVTwZqPkQ97D51KuhLwGwQxgyD9lkG11FULY8GIpDoFR7OE2GciwMz7V9kmuM"
    "CedyiMJ4nxVWfSAmxffS3URZHA+Fuo2v+NmDd/boLs8KI/5EdxzeIodEjvjukqgbKxJo+UotV0N3"
    "zT5roGrOSrAnhTqsomK+C4ulFaVlc0IFM+Rd/eQKzQVFoHfREZ6nViMOyYCfGrrzqvCwb0yeSiLJ"
    "myGVZGXyYC88Y2mvigk7kk42xybiXS99Lj5lJweFAs4b9ZGlTYq9TpUdHhc6eCaqKiqrK1G3ujxT"
    "x0+x+5syRJ+eTByr/e2hrUjH6rPMGVPFnzryxQUyPfeg3S34YfiFxdbMMpckh6CkG2v3aJTTvGpV"
    "25xy2vMCMxSMmEdGENiZsq+ijg/lTT67/AiZCzg59pLu1s1SIpApwGEF0tsodiak6T45TqXkTQnV"
    "BlT4l4j1Viks1W0lOwTQzBT3deJw+kusCuGk+hvZQivmsfdvRGrLuV5Ercl9N6KsUW9hcU55df2F"
    "Z9P3900jGiyweUc9lIaQshvSOo9RDWzVCKBPFt3dmbIJAcZDV+dW7oTTPTBnpJNN0kPeaai1Dw3f"
    "wE6SxXlc2mIE8kyeG52x6zzw4+SHFutRu5D55HQ4UPrs55R53pSOqtHVQ8Ih9DCFBUd16xDPT3nu"
    "QJu8XMK1ODrvszDBayQSgAO1T5EEooRQQ6bWpfKbhZ2Ecaza5nCnhmsMRbrZVNAdOYr5PB+IXixi"
    "ST99p4AgkwwWLnscR4ps5yEuQqmzspLkBCEztsH2hLPtjaajiOqmOif3dzfDpxQmuxYV3QlcjSg7"
    "JUCZ3WN22G5uBaM698gyK+ffDIJL+Zxlw0bLm64qF/cxDFpjGTRsDIUf7d7xedjoMKskH/b6quib"
    "RwvDstCw/GosKIobp3R8zp24i6rX48SjHHSQecfdHzWSA/7xCeiVDfWDmNNe9wVZKB9lJOVSsncI"
    "1RIKP13ttb0UC3Sq9eJ172qRHpv02yrSIwmrheZBpaxJ1yM2nLI1tmdnk1u5DePkGxYfso70huIN"
    "ihqkpmtJc71J7nIGVOGxfkbKZxIqUC0ZSVHDLqcsRU71v7McA1ROdanWDD39LJOjl2Km/gYMdA+O"
    "PHOyZEn1emloMGANtLiwQhUubr65B+zwx/QVQzNrfVTlGcCRqBI1kYBJEenlMAMzy7ctEjjU8Oiu"
    "OVO7h1nlfAB82KTyZb9xhKzD5SZ5jaqQ2+NJFjmlkug2B305XGxACJ8NvZ3QD1IDy6kdkPvADTH1"
    "xeg0VHH2m9cFFgUaF6Cjbmc4KHS2uHTOboP0ydlFZERHFbeRHdboO1IDtYUcqxO/JO+/X5+ukyqx"
    "RTmmWTMAhoJawhfi+QCln56P1XvnMJ7ABD2vjrIiwVg1x7DNNyAROnIKVqbJ61Qhbl2ryvfampic"
    "z4YwSf2bV5FzcmyDUNGSQGT3+KvL8uNAtTRH2PSIiJMnIGuynOMZO9ika04dQzrKWQxzSIsbhbLa"
    "WPcqBdWAIhEq/Ni1WTIaYL1zmAEQ6Y7XYqFZHBzgy9mgJD1mZXKeUzY7JNbTT0Ex0mcd5Hz3/HQ0"
    "EBCdVkJ5Zz93M3iakbiItLRlNIoWxVSpcNjcfbGIDUqCIS+ZJneta5HbNSJzmTXLckp197LYFBvV"
    "NH/pXiLpZ4Aer9uI0jDIndN4paXyxy+DTvcUNQuBETnUg6JD+k0dmJuVkk3p1G3BHEpykK8s0t2r"
    "qKKBYS2zhvX6mVaHmfD+cCbJrVpaugivAa01LuSpd64CSM7qh1uc/pSPqBL5YafTeQM2bVHeErGU"
    "JeQ3Mu9ekt3MYRK59fC4c610dKvibbfk22Xr9h1UVelLh5N3R9GuqNHCE1DSgvhCb0v61vb9uYnp"
    "nKmxO2/OhlWDdkq7oBR8OuYkFDP+oNkzj/abNuf4rOmdQN03cYgNbou1kj4hAbfZx3JYMoxj3BJR"
    "A4jUnBWEIcONl47VlFQBMXrtcZBZGQC/RW3YqFmoqizNGcZWYJpezScCO++blHoAk96pgyYrRb9s"
    "Dq/p45HSyRS9cNjNuK9ZTGsKWvX8+iMHBkpzmMYKyNmzLG61spsxTNw3a+06wKiKlRC/+7Nv6kaJ"
    "+zul89eIzRwBYwztm3bOcxBBREkSnt3iatCNcGkcNDH9vImIDLlhJSTE/CF+io8hmYb4uB0NcjpA"
    "LKL0sey1mQDvK5kykfMGaVWz5+C7ZNW0tn1A3YgtwMCH7u0ToTcTzHXIjLsVAtUgdYUd7UqB3yCR"
    "OyADIhPZOMCKmNirUKx+zjExzA1yUgZPRb0uU5oxOArmrGalVauYqhORZ1czVFb7GPcoLEU3xH6N"
    "sZzMx4X8pPboAGVUa34lp2kdXQx3li6kNf2uyDd2zUuOk/rIJ4GGZzNrPa9IjkZLVrBZYvLXWyiA"
    "bWORSHcbDX0vm/tmFuXSWM/t9AEal9S7UUOZkftvZbh3EIGmWbWOJtOTHJs0a2J6i2onGMTq/ZHd"
    "HbhQu1OLxa6g8yDVRQeXZkEb8ueW+e3kJzH5mbWNU+OahdJvOAt3ljDa2x2nfx6FTtetGBf4npYH"
    "0h4dyl32e5NWVzeENwxk085oGdxusGdo6sr2vxopst8IViopB8/Qum/4Fa1o0XntpziYk1r1qeRY"
    "yr7BoCC6bzbbpb/4tDvhSIO04dsSlymcht1Fbj89deYkZsUwzFkzDqWFG2zbvTU/RxuInUQ0Wa6q"
    "IeGvncMFBPy4q+jL16e1uVeoK6eXmPbEpQflbNPqvC5XMLOXIcVdt1RE63P+0Qf6QkgjlPBxlFAz"
    "4Ranr5g3V6Gpt8y9Zzo5mwZWr96BQ+5yr1aA7PKcw0g6afvaOyBGjWBqdUbr9BogW8a+biVpV2to"
    "VzbKUnq2DYRF0AMk34dJNX87KVouTSFA2ptlghf3QT+793qN2uubzm7TN98hy3RF82ci9ikxoV5u"
    "OavJETA6tTDW0GUXG1G0Sm41kJBR2N4SSuPEr0RnrNfdzpxS+l4gntyg2eelBlja66dG27w8cEJm"
    "otVlq28qy3H2wNUFCePBewOBYdOEc3pbNHKVE6GqACefWiDCJlB06IwbTZYnEkEDJ6dOeCvLZaOQ"
    "iEGxWKvb6exGFJFBLfiaT+OLKtCWajs5Z38juATVyBHnTQlnjYwKTaq/Ptt9BI22RzhwtkgKzAwD"
    "wXhJcdnpYTsXSicBo830YbdSGRN9V63f7jkxPqjnH9jvxNo9E068u2r42tKT4lFsSX/DgYvD24tc"
    "5zzhzB0zQ9FX80Ru5jWHMbyL9ShAUOEY3oFP0haSYKqNSs/N6fXwicx+13yzCNOPpUSzp9dpvbt1"
    "jT6hvkfPBOLjfpNzkDtQfeoYtt5TV6BXFcTN9BXv9BWjLtVGIY/Q6XlXKYRMhuu1tSweAZdSHFhP"
    "cJcD7SsnR4D5eTvLkdBaHTLr8yaFYSWi2QWMuuZJKOVOfaR3hR2TwTCIxYoHfbpqDF5elxVPexOZ"
    "U6T1AYk5r5C4zYErFdfsZ8xZN624hugNZDlLT6fHmwSmYS2hWobU2k1u1qTG5cLvN/pTfCL/O8Ua"
    "vytCmIagyFH3anTlP10LGp+rvrV6lNDaJWoiUF6d0ehgFVhho8n89nUQ6BSTN9dudsfq4SRwjISF"
    "curdjpKYAyUQzhKeo08OxNyoLsExjNVBnluX1Qg4drvNBixnaZ5jA9HE8q0+K9O+muFpXbSmauSW"
    "WHV3I+koDdRcPDuxVoWITJCaeTWDRHSxl6lj2q0yt9+d4maLEjqWOFj604s5V/cMQuF7WxFn2T9A"
    "4roaJbpJLiXIRFCX/VK3E1w5mA5BpQ2ozY43g30zRiw839QpFOw5QYEp8RvJZMbxYOaFOfUlVaWz"
    "Fw5su6evedmLGil0BiwA3TcoBmHtsHzm87zhB5jYhikgmVGdLpLRCwjV/mlbhR/TsVFkp4OZ5n6y"
    "GVe7/M1kr7/I58jVCZUKs/jxhPYzrUeKw4QAs6a6Kg/DoHJdWu5i99aBY6r+um18s3SJTnXogbsV"
    "PK+X+P4bomt2ncYvisMJ3VFmn284gNaFQItuticmukCaiilahnmTb5QR1YWL1GYPDai7LRDpeQnK"
    "lPN6NS74AIrQLsNL2i3H6wcmMMoOn9+YmIq0tMLLbTXrGTX+AKjWU3Hb18K41wsyfDZnpcdZCOKc"
    "s/1EWoNdGnuSjGiQAyVsDbGjbzItNmIsBnsTlmzl9FjT04PknF9rTnmU2ai+eUL6+Y2aDlZyVb8Z"
    "JAeDYol713DY660TmUpvahg5CN9dL6MDNFuNndpX3iT59I1QeGFOxqesk6wVmiExHnzaU9OSilH5"
    "m7iAbh8ufY4txiUsjxacmFukl7c97E/5CjqjsnThNb7ssZUY5auZDmDix+vo5JRSpAF5RK37JdAJ"
    "h8nUWndmvPFWd2GaJCJ1vvKb41AXumwOeXe6NNSkcaymUdsxdby5phTbUkc53qTZRBCnBo5Vo3Jn"
    "WY4xVqtmgetpJGmnD0Pd9tQ3YGA+NuaICidG1Q07I2cJXegJSZu5d7eP0DvJrJteOr9Eg8co0X7q"
    "BVod7wKGKoW/nOvRh1pYk0UROa9I6mFG+P6YA47XmLNpFXSJ4aYuav1uS0cwQJeWR6f1Jv7vzXx4"
    "G+F44If9Rmzu0l1zhvKSz3GL7BcbXu2LnXT7BW683MP5hqdmDzvTQqFCRDvG1aVH21hJXfJqSJB1"
    "7MUe6bNf/yeU2tqtONcaDFxTDr7iSPGjXQ1DQTR3+8q3l/XMxwbr4VyN8/ketqhQZCqptwkaqb6s"
    "mVxTmvyc2gOEUML2U2F0+LvjA5OaORQwpc1v7OBgzj+FzfljtjTr0lTiDzkBc3cnrVHVGBGbFJif"
    "N2UX9Zqlpc0Z9+UKGLG3Vo3Yuz3wFcIjiusoY5vSkPKQsZxH2iBrSy4nQd4quTd2Q2MS6NxZXcxv"
    "gXk1hexVFcInuM/dSrkBR3uVgpzddfwTyCAWJs89boyZ5iX5Ok4PYDehPOVMFhUjVBeyMs4xvISn"
    "rRfPIKGcfkAG7Eon2YJxb4prHmjaPekOibrWTXEphm3MwTmNU0mFnPNmuGo9HNkV2rj05cxwKjrq"
    "jiUbn13fu448J8LunvEzrZThgzKf03r1Ozk1JtNIzJcobI7kgpdgcLj0eq2mLFsclqT2ah3mzCsg"
    "kESx32C024SECDNza3bum1uXyBXjZnzWbOe+t4uSnek9ZcaeULDGfRzCjnUagS9De7WDhQIn8c0d"
    "OVDwIdvNO5VaZoIy4RqlTe0Zkewww+BYeuYuK8zJjNpqwE8P5IcQBk2Hg/WGNV6wlKqQDqok5bTz"
    "6JsWV41Q6tuGBIP1Pj6bMMZ91xPq5LhLuuecdtC9L6wEHKpA5Y3bLpOfi9FStKWIi3p9XGsD7vHN"
    "b+LoSt7Qk+xKjyuUBXG1oAgDcqDTwZqVM7x7AprMs6K257h1R04r2pP1UFRyqeOpul8CQNCD1L8u"
    "73bWc1fdJVIEWV0mAvUQdSN0zuHWa7EaNfdAz8+ZjxcHcQvRptweDJM3QeHyGtI+gRtWC9ExGNVo"
    "vmNX31Z92+Vssb3adIkXR7wnGQCzjpaXudI8VIBaZcjog0eqj8FruO2vs8GL60cuurAcLbV9PwLB"
    "S2a3GUhqZEvNBhhscsbVnp31UUJTF19lMehN6GbnFOZXAYJ2+cVwn0zWYzivbPbkXsPAjYwsvJEq"
    "q6/dq8BezyOsQMQW9yoaal9zd83kDRQdGO0jWt1Au+fOGlXa8ZBumOn8kRAJ4mcUuF696A5eCMMt"
    "kVf257cdHK96ZwcYDB9JLoetrLu/0gAJt8F3DZSvy8dghgJS4BxW2sNSBu/G0cW0Qx5mw2DpJMit"
    "Sk6zqz6TWg91jknT3fdeVLuhS5W8tnwmKpwJdSlZ7xNryqY029Wz3p59LIZCHzUVlHPfEbp5pU2N"
    "PKzGvpEqYNzwUwOn+61ndvzlPlF9ssbnQDvWhKVuAKv2RJTSWH/VopTf6JzF+z5u+bB5PuNjzXRj"
    "W8UoETDei0n5YbNc6wR5eynjCieo1tnABSS4iQ/3o8Dlv5mVKMUE2uGwtzfib94WNLM1bH0WzpTR"
    "QGoMkN/1Wogo1/HqVeteDAXnO9DykCRetwMlsMS3plqlb1JUq3uEoA3DXZV1YGTWZIFDMq/Tk8SZ"
    "LGbVSeokvi7ISFjHduYOzZ3krs2kfL6emRwozKpV92c1zYcr4oC9y3u/iTdyMQTtHo43Nm1Uls35"
    "VfjmSEv9m0CUi+dFlj4enDTqqvuYjryxxBcTXNAJnPMeetyrac+onOXGuhdCFR1MQymXDufRV8mk"
    "hgdjtVfxqK84BonzqkRIHpu38Wqpo6Aw2DuTVYNKifOjswrT5YrtvOHm1kwme/zQxfSPIxSki/un"
    "+hduz0glHnksNW+GHhyJHCbb9+3h6GdxgpMrZ7cP3LMIuAenBXwDOlOTbEVUQIXYKSBOQJbTCAy6"
    "hbcmLHEkU5WCE6Pi5eKcEVqNVo/3+PFTGEa65f9eq4s+mE1Fit8M4+GdqLhTKdHVm94y2ThWzTpj"
    "yOu6ZcMMaERHJaQWShE0ZdaIDe2641E6JrnMTSJ1e0MjWC2RzetP3nWNgvy1Os/tpUzpw4zKTZKx"
    "XVMyA6FjSIgxTb011XVhF/MiT5TQ/IhRipR1iwSJp2XY51DYs0e5cH21Hcwxxe0A+m3BF93VC0T4"
    "qJ6NTg5kIMGdtqv/omuMM0cCo8dFv70eCUQT4oRODhEesxXanrotoMWqLVmpda2SA13Mpfyc/c3s"
    "Uxgn45q8Yht1GQMNpQKH+8aLoLik5f16BiNUx/Z5Pal2g0sqEbKWqIQFfdVp5lTsdz59f3tD17EJ"
    "9K0uQdKXf7DYXIXgR5zg1jzlpaMYxtfavha9eJ2bMVpUORIXQ0DE6ckizYOMEm8WySWjlWkL4ltU"
    "tkEJvvvxDtA876RFl7J2QIe9U1iTqL+tWmrm664W9+ReC/os3nfnpy68XF0dPIeT5bWYftV3mYow"
    "JJwaz8NpoYkjdnW/M/U6577SMib02uEljnlJSuOljXVkCjnfTtXVeUN4c8DeLSXImea8G5AWd/U8"
    "/RlldIOijy0taEfe8X1vIxo/uqqXtoYrunhfVFdYmr/F1aKZAtQKW91al6RBXawmr7WUpL1MjlNz"
    "ayEd7gHtDhvEvG4iobiRZadvcXjedstagnJWqHxzCZJWxw+B6l49wErUHypE603fqT5KC+TFsj2F"
    "wOa9BZjODv2OPlNFOiOLTvvYeeQU5TOn+/Kt70CsASqQcLOJ++mPMeHDpCYT3TfTF6nqzNl4vIG1"
    "O0gO9uQYbavCQlYi2KOy2Nl9Hi+2cxw5WK7Zg1W62z374sfXYr/cegBm0oYfnRoaBPw9pX+XLnDT"
    "N4t2Pf6weQbNEYb7lxs5UZkxBidit3oGN45htE1ddMoah3mhqVqPT4rLoX/gpQwT8wSeKBiKQGcv"
    "f5hqC5Mm78oFlwd8IO/yQ9Q+jKDb3+3MjvGkyBjqGvLXu5rBLulKjm4ZPYt+2apEilJweWn1mej8"
    "O2uWumS9WVSHt4dQaTqWe+vvBTMMpHxDkwAnL2rgXE6vZoKneVRKcyHKSmKug8i6CG4mFBLv+a6M"
    "527sQ97t3P5FquZAkjIclqSUjQLk+Hnxjox3xd5edSsW57rIfj6z0sVtDCT2yFD1XaNPONFsn7qt"
    "FhedUCBCek3XGx54aognR7hEwO5JJgOqlNM9S/J5jSKz0rrNzm+j6DWJ72XxXrO85e118THhQpDJ"
    "u6b245vrOmISJ0d77y2bWMB2VQrPlkCkQotcC2+IGu8ui0OiZ41Z82t6sP+dJcRPAQCYqZoFMLZU"
    "KNHqVGy63TZYOau+Wlt9NR7nmlsNmp8vx86iFcd31ajL2+VvZcmY4wizQb+6AAabWwoIdTdF0nds"
    "FTmjKYrGeqgujzc0oQUBaYm4apr1ctyl/K4pwR0/19ndv3oi6VjV1jMo1HtzjHvsBJWb+tqc9uFU"
    "uOt8PWM/Ly5CRvPOYr/h+JzkcAUj/3bdbfjGg9QFD+KkHHXv7g1g+HaOUdGuIwgpv8362H44RDA+"
    "JcfLUgB6+uqZSy2XMgFzXk+M/Ip0QAGzbvTB5J9SlTMJOp9jmjangV6I3Rl6OrIQbaRSlsbelR0F"
    "VZ2Iiyt1Hwur5N2sqvfjjTRUJIAj7zxGQ3rfzrBLsXLhTDMgtIpne405c3Y6tawh97qGV2/KRtad"
    "r96WNwHntCZa3NVHHKf/vbPu8BkdiYVtfWORUz3DnziTmGZfzhQx7Xr82JBi7UvNWpOU2a/IlqlD"
    "AWgXGpMso1h5Tg5V9NnLcloue6kJtrrwI/adR429Zx0lkyzYH0XEJCGxup9xIfHWwSHNgZ4/KQRA"
    "ION3mqM7JjUbOXGjlNQN4vszqOMOCAq3+sFecdWUbXKxbh0RcPEVpnCSpCiOa3DWCGF67EjP4jx9"
    "WQxrvr66D3s5WPcphMORC3UX52Axzdu9NFo7k9owzI/OWyZb7pRVv0zElFKV2ZOacCkxwcOkClne"
    "iD7wwugXw5/YK16Q+H63jfB63pR4cYKF8JbhpnIx8iINS2sIfpOBU9BiRPr+U+FmrI8P9rah/10/"
    "8/EaHV+TOE5PtcrGN7YMUbr0FId1XcTlJGR9Db2BD2GCp+bVujYpjNwTuIkSrP3uTkPJaFW35tQe"
    "jW9s1rS6TG6NrpqYYHTo8FK4fb4H7vbTrNjBxu31OCuzQgqHzu6+lQ3S++KabN500QQsSsrioy4u"
    "6UrdhooiJTuc7OSvg8A4AZ9pciZwZ/bEcxYC1imdp/WZpNbYtTt9O01WpfZAT9FI76IhyuStdjYD"
    "SUuEcY3duDU0pJpgBqU5CJyUt9krOW7ok+c8df3kfp7tHM43q6aKlqLg2sIsx9ZN1PPd6KMsaxan"
    "sI8+PD+cSI3PaKE6q9mpEpkULbWzV4gNd90EcXsIAqZoo+xUV8mORpwVn66yMzgnM3bViRdCrctR"
    "6+afdQPeinsWFdtqb5y9VymdfRvyVhdKxNzS4ulv987HyaLUqC5z2++Ku7t4/r1wbWQZHdIy+EK6"
    "fWtyQk+1AyBRFLFyiGxrnW9yGRiPwKlJc4++rKnKdJsqsvGutqrbcu9gQPuc7XZ5K65NwrpI3fqE"
    "OIdpyPBKYdv15eiQD14nRlj3eVUohqcb2+POO51zQn/qWqMgR7sf2RxoMIztTefo64xeFbdIKown"
    "I1CULzYoTHSyNWChemQa+RHfPfR7DAyzv8LhPREb3/Ae6ORmiRp7fE7+gnlRX0V0u9cNIo076JZ6"
    "PFCGLVYvcAU1yL32iTlvBFk4R4/uDlx5swrU23UN2Ccb6CWsqHLjaAm9CGtGuy5zW6dpqXlQTx3a"
    "A1y69q2CbO1Y3Yajr6t1nuL2eyRGi/cEQ+snRMo5K9ZfH+zlZYdErmM8FYxTgnPLlT11uC4MOTzF"
    "Y0V+9e5twpr4rA18rUiecyXwtYkw7E13RHtntS3mhryRWG5QBqE2O74Za74UDvagNIXp+33Nk3OK"
    "Q1H7216EvAArR2suQpfwzVoJR86/x51jri03fdRgXXu6OiHR4Iu3fKyXQh6Xula1b6DsYtricEI0"
    "rGN0Z5/PwR5OySIjqpHWFxHVXN/LAdfrjieCYQ1xSZlvC5sV2crY/KT1xmtPXCyaWs1Tg0DW73//"
    "8d2//Pznn3777u+YfuV3Y3n49//v9//v/wOO8/0y"
)


# The reference fist for the wrist rule: Mar Fil's assault-marine right hand
# (the surface its bolt pistol, knife and axe hands share), 1369 points.
_FIST_PACKED = (
    "eNpdncuOLjlWhV+lVCOQso58v/SQATMk1FPEoCVAKqnoRl3NCPHu/F7f2o5IJpWVPo6ww97XtS/5Pz//+U//+e8//+Hnf/rTX3/6"
    "x19/++lPv//+p//+7W8//cevv//tp78rOf/yD3/57W///PntL7/98sef/uOvn+l///PXz7//+m/nsT9+/ve//vLrn//2+89/+Jdf"
    "8o8+vs5/5/z6Jf1oqeq3Uc6PUfYZLOvrzhtDQ3k0xrJ+aCxN3jT6+dFaOYN1zdfE1vbXZ2IZr7Fa2pnYsydqsbqXnm7vscHK+f3w"
    "6ueF7dlgXryubsb0I089W9p7jZz4lPl+erfzvr7vKaQfe2ovPT0PfwZ31Ru3B3V6O+tHXvX1+Ow8XjyonczKydb9bWbXOe7GWX1+"
    "1M9hZZ1EHGDR4NDM3AuDQ4Of1c9ZVMY0lMrX+WxP+7yi/FhbLxx8cGv9DO6sF3Zu61zTGVwszdj5jM9YqxwaYzzcig5txMLn0XPR"
    "hdPX/sqPySXMxpeMqkG+ROT3GZyLmbrD4jdOzzyr5DTe36Lv8123pd3M1LgEyHBq4ljnXmtibDD2eW/iRGPb45yg6bdr1d71tgXl"
    "cC6dG21eYWtZ32Ft0LaGChS72fLWqn3psCZbniVe+Oykz3j4s5cMLUxtr0Fmk3WX5p19fpat65JH+VE1IflZLq5y0Dv7rBoTG1cC"
    "bSbdU80ZhtRbemZmXYgCZmZ9YOWok0lb31dhIERGqkzLhxgY87aLLqQnf/Lm0fMpM/dL/mfszFuZU036lIysGqWwrB7OQ4TZONhe"
    "dBA6+nMpcGnm8XFoM/f+org8i24e0uRLmLfe9JGWfsnIpTY0mGtGIrCdwnaSyCFVjqboIFI79FXKvCSSxTomLshdXPe5ve1b1m+7"
    "cntcfU+bmYgNk1xhcG+kFecAs+1uhmrfBguszF3BRLtm3V+7B8Y6RwLVe6dn3rk+5GRjq3uJe9K6VPwZExWvsa4c+KiQrTcUT9S8"
    "wWdm08PSP82GVOW3XrSn2WEBtICf3sh8HwT/NrbEYXydxuaQGDC5+4VTzGeq2553xsZelxw+Y/mMbaspv0LzfJ+wW19DJwMl8ali"
    "7+lvC/ms2cUnGBdjJcTdWVp1yAuV3KuFiWUplDN2XM3nsIslpP7J3xrMN9kDRMy2UZ4VtbmXV9HSFTk8v51hLSJZSINp+uRgHpao"
    "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"
)

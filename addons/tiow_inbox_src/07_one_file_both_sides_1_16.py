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
    if job.get("_side") in ("R", "L"):
        return sides[other] if job["_side"] == other else None
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


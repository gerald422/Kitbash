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
    sock["tiow_corrected"] = 1
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
                c["tiow_corrected"] = 1
                moved += 1
            elif CM is not None and t == other:
                c.matrix_world = c.matrix_world @ CM
                c["tiow_corrected"] = 1
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


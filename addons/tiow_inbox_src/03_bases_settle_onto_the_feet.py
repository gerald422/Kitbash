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
    # a socket moved by hand (Fix the Socket) is already at the tilt wanted: no rocking off it
    if spec and spec.get("rock") and not sock.get("tiow_corrected"):
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


def _library_root(path):
    """The Kitbash Library folder a part's file is in (the one holding _sources.csv), or None."""
    d = os.path.dirname(os.path.abspath(str(path)))
    for _ in range(12):
        if os.path.isfile(os.path.join(d, "_sources.csv")):
            return d
        up = os.path.dirname(d)
        if up == d:
            break
        d = up
    return None


def _adaptor_of(part):
    """The connector a part brings (its sockets file's "adaptor": a path in the library), or None for the
    body adaptor from Preferences."""
    src = part.get("tiow_src")
    rel = (read_sidecar(str(src)) or {}).get("adaptor") if src else None
    root = _library_root(src) if rel else None
    if not root:
        return None
    p = os.path.join(root, *str(rel).replace("/", "\\").split("\\"))
    return p if os.path.isfile(p) else None


def bring_adaptor(via_sock, prefs, unit, path=None):
    """Import an adaptor and snap it onto `via_sock`, replacing what was there:
    the chosen body adaptor onto a Mar Fil torso's Waist, or (path given) the
    connector a part brings - a wing's onto the pack's Wing Mount, as the
    connector's variant for that side. Returns (adaptor, note)."""
    named = path is not None
    files = adaptor_files(prefs)
    if path is None:
        if not files:
            return None, f" - no body adaptors in {prefs.adaptor_dir or '(Adaptors folder not set)'}"
        i = min(max(int(prefs.adaptor_default), 1), len(files)) - 1
        path = files[i]
    job = {"path": path, "category": "Adapters", "_unit": unit}
    variant = None
    if named:
        job["category"] = part_category(job) or "Adapters"
        data = read_sidecar(path) or {}
        want = str(via_sock.get("ws_type") or "")
        if want not in (data.get("fits") or {}):
            for vi, v in enumerate(part_variants(data)):
                if isinstance(v, dict) and want in ((v.get("sidecar") or {}).get("fits") or {}):
                    variant = (vi, v)
                    job["_rname"] = str(v.get("name") or "")
                    job["_folder"] = str(v.get("folder") or "")
                    break
    new, meshes, s, made, added = load_stl(path, job, prefs, variant=variant)
    if len(meshes) != 1:
        return None, " - the adaptor file is not one mesh"
    ad = meshes[0]
    note = auto_snap(ad, job, prefs, via_sock)
    if "snapped to" not in note:
        _remove_part(ad)
        return None, f" - adaptor not placed{note}"
    nm = os.path.splitext(os.path.basename(path))[0]
    if named:
        return ad, f", {nm} brought onto {via_sock.get('ws_type')}"
    return ad, f", adaptor {nm} added (Next Adaptor swaps it)"


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
    if spec.get("sided") and job.get("_side") in ("R", "L"):
        goes = job["_side"]
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
            ad, brought = bring_adaptor(vs, prefs, unit, path=_adaptor_of(part))
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


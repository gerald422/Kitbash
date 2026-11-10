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


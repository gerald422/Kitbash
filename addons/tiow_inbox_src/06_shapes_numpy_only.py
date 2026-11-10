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


"""Legs on waist adapter 3 (flat-topped legs: Marta, Turtle Ninja), inside Blender. Moved from the Nov 23 scripts
(legs_seat, legs_rest, legs_check2); behaviour unchanged, objects are arguments.

Start from Josh's known seat (the Marta May 2026 Legs 1 on adapter 3 under Torso 2). Per legs: map its waist-top flat
(the biggest up-facing flat near the top) onto the known one, sweep the turn +-45 deg with ICP of the waist block onto
the known legs' block, sit it flush on the adapter's underside, then the rest step (slide, turn, lift; the smallest
move) until the adapter overlaps no more than in Josh's seat (0.11-0.13 mm). The control row gave his seat back to
0.01 mm and 0.6 deg. The turn of a round waist is not fixed by this: take it from the buckle (buckle.py)."""
import math
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
import geom as G


def top_flat(o, V):
    """(score, area, centre, normal) of the waist-top flat, or None"""
    zmax = V[:, 2].max(); best = None
    for a, c, n, lo, hi, idx in G.flats(o, 4.0):
        if n[2] < 0.9 or c[2] < zmax - 4.0: continue
        s = a * (1.0 if c[2] > zmax - 2.0 else 0.5)
        if best is None or s > best[0]: best = (s, a, c, n)
    return best


def region(V, c, n, depth=5.0, rad=9.0):
    """the waist block under the flat: -depth..+0.6 mm along the normal, within rad of the axis"""
    h = (V - c) @ n; r = np.linalg.norm((V - c) - np.outer(h, n), axis=1)
    return V[(h < 0.6) & (h > -depth) & (r < rad)]


class Known:
    """Josh's known seat: the known legs and adapter 3, both placed (world)"""
    def __init__(self, legs, adapter):
        self.legs, self.adapter = legs, adapter
        self.V = G.verts_world(legs); f = top_flat(legs, self.V); self.c0, self.n0 = f[2], f[3]
        fa = max((f for f in G.flats(adapter, 4.0) if f[2][2] < -0.9), key=lambda f: f[0]); self.ca, self.na = fa[1], fa[2]
        self.gap0 = float((self.c0 - self.ca) @ self.n0); self.b = G.bvh(legs, self.V)

    def info(self): return dict(c0=self.c0.tolist(), n0=self.n0.tolist(), flat_to_adapter_mm=round(self.gap0, 3))


def seat(o, K, start=None, raw_z=(0, 0, 1.0)):
    """Seat legs object o (moved to `start` first, a world 4x4, if given) under K's adapter. Moves o; returns a log.
    raw_z: the file's own up axis (in its raw frame) for the turn-vs-file number."""
    import bpy
    if start is not None: o.matrix_world = G.mat(start)
    bpy.context.view_layer.update()
    M_before = np.array(o.matrix_world); V = G.verts_world(o); f = top_flat(o, V)
    if f is None: return dict(legs=o.name, note="no waist-top flat found")
    _s, a1, c1, n1 = f; c0, n0 = K.c0, K.n0
    Rb = G.rot_to(n1, n0); Pr = region(V, c1, n1); Pr = Pr[np.random.default_rng(2).choice(len(Pr), min(1500, len(Pr)), replace=False)]
    cands = []
    for th in range(-45, 46, 5):
        R = G.rot(n0, th) @ Rb; t = c0 - R @ c1
        R2, t2, med, seen = G.icp_median(K.b, Pr, R, t, iters=12)
        cands.append((med + 2 * (1 - seen), th, R2, t2, med, seen))
    cands.sort(key=lambda c: c[0]); _c, th, R, t, med, seen = cands[0]
    R, t, med, seen = G.icp_median(K.b, Pr, R, t, iters=30)
    n1w = R @ n1; c1w = R @ c1 + t; Rf = G.rot_to(n1w, n0); R = Rf @ R; t = Rf @ (t - c1w) + c1w     # flush: normals
    c1w = R @ c1 + t; t = t + n0 * float((c0 - c1w) @ n0)                                              # and planes
    c1w = R @ c1 + t; offv = c1w - c0; off_in = offv - n0 * (offv @ n0)
    fz = M_before[:3, :3] @ np.array(raw_z); fz2 = R @ fz
    def proj(v): v = v - n0 * (v @ n0); return v / np.linalg.norm(v)
    turn = math.degrees(math.atan2(np.cross(proj(fz), proj(fz2)) @ n0, proj(fz) @ proj(fz2)))
    D = np.eye(4); D[:3, :3] = R; D[:3, 3] = t; o.matrix_world = G.mat(D @ M_before)
    return dict(legs=o.name, flat_area=round(a1, 1), waist_median=round(med, 3), waist_seen=round(seen, 2), sweep_turn=th,
                turn_vs_file=round(turn, 1), flat_offset_mm=round(float(np.linalg.norm(off_in)), 2), next_turns=[round(c[1]) for c in cands[1:4]])


def rest(L, AD, K, frame=None):
    """Rest step: slide in the waist plane, turn about its normal, lift, so adapter AD's underside sits on legs L with no
    more overlap than Josh's seat (p99.5 <= 0.12 mm), smallest move. frame: the torso's world matrix (K's c0 / n0 are
    in that frame; identity when the torso is at the origin). Moves L; returns a log."""
    F = np.eye(4) if frame is None else G.M4(frame); Fi = np.linalg.inv(F); n0, c0 = K.n0, K.c0
    ML = Fi @ np.array(L.matrix_world); MA = Fi @ np.array(AD.matrix_world)
    VL = G.verts_local(L) @ ML[:3, :3].T + ML[:3, 3]; b = BVHTree.FromPolygons([tuple(v) for v in VL], [tuple(p.vertices) for p in L.data.polygons])
    VA = G.verts_local(AD) @ MA[:3, :3].T + MA[:3, 3]
    h = (VA - c0) @ n0; PA = VA[h < 1.5]; PA = PA[np.random.default_rng(0).choice(len(PA), min(2500, len(PA)), replace=False)]
    u = np.cross(n0, [1, 0, 0]); u /= np.linalg.norm(u); v = np.cross(n0, u)
    def pen(dx, dy, lift, th):
        R = G.rot(n0, th); t = dx * u + dy * v + lift * n0
        Q = (PA - c0 - t) @ R + c0; d = []
        for q in Q:
            loc, nor, _i, dist = b.find_nearest(Vector(q), 2.0)
            if loc is not None and (Vector(q) - loc).dot(nor) < 0: d.append(dist)
        d = np.array(d) if d else np.zeros(1)
        return float(np.percentile(d, 99.5)), float((d > 0.15).mean() if len(d) > 1 else 0), len(d)
    base = pen(0, 0, 0, 0)
    def cost(x): p99, share, _n = pen(*x); return max(0, p99 - 0.12) * 4 + share * 2 + 0.25 * math.hypot(x[0], x[1]) + 1.0 * x[2] + 0.03 * abs(x[3])
    x = [0.0, 0.0, 0.0, 0.0]; best = cost(x)
    if base[0] > 0.2:
        for step in ((0.5, 0.5, 0.2, 2.0), (0.25, 0.25, 0.1, 1.0), (0.1, 0.1, 0.05, 0.5)):
            improved = True
            while improved:
                improved = False
                for k in range(4):
                    for s in (1, -1):
                        y = list(x); y[k] += s * step[k]
                        if y[2] < 0: continue
                        c = cost(y)
                        if c < best - 1e-4: best, x, improved = c, y, True
    after = pen(*x)
    R = G.rot(n0, x[3]); t = x[0] * u + x[1] * v + x[2] * n0
    Dm = np.eye(4); Dm[:3, :3] = R; Dm[:3, 3] = c0 + t - R @ c0
    L.matrix_world = G.mat(F @ Dm @ ML)
    return dict(legs=L.name, before_p99=round(base[0], 2), after_p99=round(after[0], 2), slide_mm=round(math.hypot(x[0], x[1]), 2),
                lift_mm=round(x[2], 2), turn_deg=x[3])


def _ray_inside(b, p):
    votes = 0
    for dv in ((0.577, 0.577, 0.577), (-0.3, 0.8, -0.52), (0.1, -0.2, 0.97)):
        q = Vector(p); dvv = Vector(dv).normalized(); hits = 0
        for _ in range(80):
            loc, nor, _i, d = b.ray_cast(q, dvv, 200.0)
            if loc is None: break
            hits += 1; q = loc + dvv * 1e-4
        votes += hits % 2
    return votes >= 2


def clash(host, other, every=8000, lim=3.0):
    """points of `other` inside `host` (nearest face, confirmed by ray parity): (count, max depth mm, share)"""
    b = G.bvh(host); V = G.verts_world(other)[:: max(1, len(other.data.vertices) // every)]; hits = []
    for p in V:
        loc, nor, _i, d = b.find_nearest(Vector(p), lim)
        if loc is not None and (Vector(p) - loc).dot(nor) < 0 and _ray_inside(b, p): hits.append(d)
    return len(hits), round(max(hits), 2) if hits else 0.0, round(len(hits) / max(1, len(V)), 3)

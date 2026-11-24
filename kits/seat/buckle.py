"""The legs' turn from the belt buckle, inside Blender. Moved from the Nov 23 scripts (belt_sym, buckle_core,
tmpl_core, tn_tmpl, buckle_apply); behaviour unchanged, objects and axes are arguments.

A round waist (Turtle Ninja) or a disc can't fix the turn (45-97 deg off). Belt mirror symmetry gives the axis but not
front from back. The buckle template does: the belt-front outer skin of one legs whose front is confirmed, matched all
round a new legs about the adapter axis (through the adapter's underside centre). Two templates agree within 3 deg.
One template per buckle style (the Turtle Ninja Mk6 round slotted buckle needs its own). Leave out the Primus Medicae.

Axes: ax = waist up, e1 = front, e2 = side, cen = the waist centre on the adapter's underside plane (numpy, world)."""
import math
import numpy as np
from mathutils import Matrix, Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
import geom as G


def _kd(B):
    kd = KDTree(len(B))
    for i, p in enumerate(B): kd.insert(Vector(p), i)
    kd.balance(); return kd


def axes_from_adapter(adapter, front=(0, 1.0, 0)):
    """(ax, e1, e2, cen) from adapter 3's underside (its biggest down-facing flat), front = the torso's front"""
    fa = max((f for f in G.flats(adapter, 4.0) if f[2][2] < -0.9), key=lambda f: f[0])
    ax = -np.array(fa[2]); ax /= np.linalg.norm(ax); cen = np.array(fa[1])
    e1 = np.array(front, float); e1 = e1 - ax * (e1 @ ax); e1 /= np.linalg.norm(e1); e2 = np.cross(e1, ax)
    return ax, e1, e2, cen


# ---- template (use this)

def local(V, ax, e1, e2, cen): Q = V - cen; return np.c_[Q @ e2, Q @ e1, Q @ ax]


def belt(P, lo=0.2, hi=3.0, rmax=9.0):
    r = np.hypot(P[:, 0], P[:, 1]); return P[(P[:, 2] < -lo) & (P[:, 2] > -hi) & (r < rmax)]


def outer(B, step=2):
    """the outer skin: per 2 deg x 0.25 mm cell, the points within 0.3 mm of that cell's biggest radius"""
    th = np.degrees(np.arctan2(B[:, 0], B[:, 1])); r = np.hypot(B[:, 0], B[:, 1])
    key = ((th + 180) // step).astype(int) * 1000 + ((-B[:, 2]) // 0.25).astype(int)
    order = np.lexsort((-r, key)); ks = key[order]; first = np.r_[True, ks[1:] != ks[:-1]]
    rmaxk = np.repeat(r[order][first], np.diff(np.r_[np.where(first)[0], len(ks)]))
    keep = np.zeros(len(B), bool); keep[order[r[order] > rmaxk - 0.3]] = True; return B[keep]


def template(P, win=50):
    """belt-front outer skin of a legs whose front is confirmed (P: its points in local())"""
    B = outer(belt(P)); th = np.degrees(np.arctan2(B[:, 0], B[:, 1])); T = B[np.abs(th) < win]
    if len(T) > 3000: T = T[np.random.default_rng(0).choice(len(T), 3000, replace=False)]
    return T


def match(P, T, angs):
    kd = _kd(outer(belt(P))); out = []
    for a in angs:
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        Tr = np.c_[c * T[:, 0] + s * T[:, 1], -s * T[:, 0] + c * T[:, 1], T[:, 2]]   # template turned to a (+ toward +X)
        out.append(float(np.mean(np.minimum([kd.find(Vector(q))[2] for q in Tr], 0.8))))
    return np.array(out)


def find_buckle(P, T):
    """(direction of the buckle in deg, + toward +X; its score; the best score more than 40 deg away)"""
    angs = np.arange(-180, 180, 4); s = match(P, T, angs); a0 = angs[int(np.argmin(s))]
    fine = np.arange(a0 - 4, a0 + 4.1, 1); sf = match(P, T, fine); j = int(np.argmin(sf))
    far = s[np.abs(((angs - a0 + 180) % 360) - 180) > 40]
    return float(fine[j]), float(sf[j]), float(far.min()) if len(far) else 9.0


# ---- belt symmetry (axis only: can't tell front from back; kept for the record)

def sym_frame(V, ax, e1, e2):
    h = V @ ax; zt = np.percentile(h, 99.5); top = V[h > zt - 0.25]; x, y = top @ e2, top @ e1
    A = np.c_[2 * x, 2 * y, np.ones(len(x))]; s = np.linalg.lstsq(A, x * x + y * y, rcond=None)[0]
    R0 = math.sqrt(max(1e-6, s[2] + s[0] ** 2 + s[1] ** 2))
    return np.c_[V @ e2 - s[0], V @ e1 - s[1], h - zt], R0, s[0] * e2 + s[1] * e1 + zt * ax


def sym_scan(P, R0, phis):
    r = np.hypot(P[:, 0], P[:, 1]); B = P[(P[:, 2] < -0.2) & (P[:, 2] > -2.5) & (r > R0 - 1.5) & (r < R0 + 2.5)]
    if len(B) > 20000: B = B[np.random.default_rng(0).choice(len(B), 20000, replace=False)]
    kd = _kd(B); th = np.degrees(np.arctan2(B[:, 0], B[:, 1])); out = []
    for phi in phis:
        m = np.abs(((th - phi + 180) % 360) - 180) < 75; Q = B[m]
        if len(Q) > 2500: Q = Q[np.random.default_rng(1).choice(len(Q), 2500, replace=False)]
        a = math.radians(phi); n = np.array([math.cos(a), -math.sin(a), 0.0]); Qm = Q - 2 * np.outer(Q @ n, n)
        out.append(float(np.mean(np.minimum([kd.find(Vector(q))[2] for q in Qm], 0.6))))
    return np.array(out)


def sym_minima(phis, s, k=6):
    idx = [i for i in range(len(s)) if s[i] <= s[i - 1] and s[i] <= s[(i + 1) % len(s)]]
    idx.sort(key=lambda i: s[i]); return [(int(phis[i]), float(s[i])) for i in idx[:k]]


# ---- apply a turn

def turn_legs(L, AD, n0, th, frame=None, c0=None):
    """Turn legs L by th deg about the waist normal n0 (torso frame) through the waist-disc centre, then slide / drop a
    little if adapter AD now overlaps more (p99.5 of its points inside the legs). c0: the known seat's flat centre
    (legs.Known.c0; the adapter points within 1.5 mm above it are tested), default the disc centre. Moves L; returns a log."""
    F = np.eye(4) if frame is None else G.M4(frame); Fi = np.linalg.inv(F); n0 = np.asarray(n0, float)
    u = np.cross(n0, [1, 0, 0]); u /= np.linalg.norm(u); v = np.cross(n0, u)
    ML = Fi @ np.array(L.matrix_world); MA = Fi @ np.array(AD.matrix_world)
    VL = G.verts_local(L) @ ML[:3, :3].T + ML[:3, 3]
    zt = np.percentile(VL @ n0, 99.5); top = VL[VL @ n0 > zt - 0.25]; x2, y2 = top @ u, top @ v
    A = np.c_[2 * x2, 2 * y2, np.ones(len(x2))]; sol = np.linalg.lstsq(A, x2 * x2 + y2 * y2, rcond=None)[0]; pc = sol[0] * u + sol[1] * v + zt * n0
    b = BVHTree.FromPolygons([tuple(p) for p in VL], [tuple(p.vertices) for p in L.data.polygons])
    VA = G.verts_local(AD) @ MA[:3, :3].T + MA[:3, 3]; c0 = pc if c0 is None else np.asarray(c0, float); h = (VA - c0) @ n0; PA = VA[h < 1.5]
    PA = PA[np.random.default_rng(0).choice(len(PA), min(2500, len(PA)), replace=False)]
    def pen(th, dx=0, dy=0, lift=0):
        R = G.rot(n0, th); t = dx * u + dy * v + lift * n0; Q = (PA - pc - t) @ R + pc; d = []
        for q in Q:
            loc, nor, _i, dist = b.find_nearest(Vector(q), 2.0)
            if loc is not None and (Vector(q) - loc).dot(nor) < 0: d.append(dist)
        return float(np.percentile(d, 99.5)) if d else 0.0
    p0 = pen(0); p1 = pen(th); x = [0.0, 0.0, 0.0]
    if p1 > max(0.15, p0 + 0.03):
        best = max(0, p1 - max(0.12, p0)) * 4
        for st in ((0.2, 0.1), (0.1, 0.05), (0.05, 0.02)):
            imp = True
            while imp:
                imp = False
                for kk in range(3):
                    for s in (1, -1):
                        y = list(x); y[kk] += s * (st[0] if kk < 2 else st[1])
                        if y[2] > 0: continue
                        c = max(0, pen(th, *y) - max(0.12, p0)) * 4 + 0.25 * math.hypot(y[0], y[1]) + abs(y[2])
                        if c < best - 1e-4: best, x, imp = c, y, True
    p2 = pen(th, *x)
    R = G.rot(n0, th); t = x[0] * u + x[1] * v + x[2] * n0
    Dm = np.eye(4); Dm[:3, :3] = R; Dm[:3, 3] = pc + t - R @ pc; L.matrix_world = G.mat(F @ Dm @ ML)
    return dict(legs=L.name, turn=th, clash_before=round(p0, 3), clash_turned=round(p1, 3), clash_after=round(p2, 3),
                slide_mm=round(math.hypot(x[0], x[1]), 2), drop_mm=round(-x[2], 2))

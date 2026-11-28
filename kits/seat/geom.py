"""Shared geometry for the seat-by-shape method (skill `kitbash-seat-by-shape`), inside Blender (bpy, mathutils, numpy).
Moved from the Nov 23 method scripts (seat_shape2, seat_live6, flats, legs_core); behaviour unchanged, object names
and file paths are arguments now. Matrices are numpy 4x4 (world) unless a name says otherwise."""
import math
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


def M4(a): return np.array(a, float).reshape(4, 4)
def flat16(M): return [float(x) for x in np.asarray(M, float).reshape(-1)]
def mat(M): return Matrix(np.asarray(M, float).tolist())
def rot(axis, deg): return np.array(Matrix.Rotation(math.radians(deg), 3, Vector(axis)))


def rot_to(a, b):
    """the turn taking unit vector a onto unit vector b"""
    v = np.cross(a, b); c = float(a @ b)
    if np.linalg.norm(v) < 1e-9: return np.eye(3)
    return np.array(Matrix.Rotation(math.acos(max(-1, min(1, c))), 3, Vector(v / np.linalg.norm(v))))


def ang(A, B):
    """degrees between the turns of two 4x4 (or 3x3) matrices"""
    R = np.asarray(A, float)[:3, :3].T @ np.asarray(B, float)[:3, :3]     # atan2 form: exact near 0 (acos isn't)
    s = np.linalg.norm([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]]) / 2
    return math.degrees(math.atan2(s, (np.trace(R) - 1) / 2))


def off(A, B): return [round(float(np.linalg.norm(np.asarray(A)[:3, 3] - np.asarray(B)[:3, 3])), 2), round(ang(A, B), 1)]


def verts_local(o):
    n = len(o.data.vertices); co = np.empty(n * 3); o.data.vertices.foreach_get("co", co); return co.reshape(-1, 3)


def verts_world(o, M=None):
    M = np.array(o.matrix_world if M is None else M); return verts_local(o) @ M[:3, :3].T + M[:3, 3]


def world_vn(o):
    """world vertices and unit normals"""
    mw = o.matrix_world; n3 = mw.to_3x3().inverted().transposed(); n = len(o.data.vertices)
    nr = np.empty(n * 3); o.data.vertices.foreach_get("normal", nr); nr = nr.reshape(-1, 3)
    N = nr @ np.array(n3).T; N /= np.maximum(np.linalg.norm(N, axis=1), 1e-9)[:, None]
    return verts_world(o), N


def bvh(o, V=None):
    """BVH of the object's faces in world space (or on the vertices V given, same faces)"""
    V = verts_world(o) if V is None else V
    return BVHTree.FromPolygons([tuple(v) for v in V], [tuple(p.vertices) for p in o.data.polygons])


def tris(o):
    """the object's triangles in its mesh coordinates, (n, 3, 3)"""
    me = o.data; me.calc_loop_triangles(); n = len(me.loop_triangles)
    i = np.empty(n * 3, np.int64); me.loop_triangles.foreach_get("vertices", i)
    return verts_local(o)[i.reshape(-1, 3)]


def near_d(b, q, lim, miss):
    """distance from q to the BVH's surface; miss when nothing within lim (Nov 28: a point exactly ON the surface is
    0.0, which `[3] or miss` counted as a miss)"""
    r = b.find_nearest(Vector(q), lim); return miss if r[0] is None else r[3]


def kabsch(A, B):
    ca, cb = A.mean(0), B.mean(0); H = (A - ca).T @ (B - cb); U, s, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T)); R = Vt.T @ np.diag([1, 1, d]) @ U.T; return R, cb - R @ ca


def probe(b, Q, lim=4.0):
    """nearest host points, distances (9 = none within lim) and which points are inside the host"""
    N = np.empty_like(Q); d = np.full(len(Q), 9.0); ins = np.zeros(len(Q), bool)
    for k, q in enumerate(Q):
        loc, nor, _i, dist = b.find_nearest(Vector(q), lim)
        if loc is not None:
            N[k] = loc; d[k] = dist; ins[k] = (Vector(q) - loc).dot(nor) < 0
        else: N[k] = q
    return N, d, ins


def icp(b, P, R, t, iters=30, keep=0.8, lim=3.0):
    """trimmed ICP of points P onto the BVH: (R, t, trimmed rms) - 9.0 when too few points land (seat_live6)"""
    for _ in range(iters):
        Q = P @ R.T + t; N = np.empty_like(Q); d = np.full(len(Q), 9.0)
        for k, q in enumerate(Q):
            loc, _n, _i, dist = b.find_nearest(Vector(q), lim)
            if loc is not None: N[k] = loc; d[k] = dist
            else: N[k] = q
        ok = d < 9
        if ok.sum() < 60: return R, t, 9.0
        kp = ok & (d <= np.quantile(d[ok], keep))
        dR, dt = kabsch(Q[kp], N[kp]); R, t = dR @ R, dR @ t + dt
    Q = P @ R.T + t
    d = np.array([near_d(b, q, lim, 9.0) for q in Q])
    return R, t, float(np.sqrt(np.mean(np.sort(d)[: int(len(d) * keep)] ** 2)))


def icp_median(b, P, R, t, iters=25, keep=0.8, lim=2.5):
    """trimmed ICP: (R, t, median distance, share of points that land) (legs_core)"""
    for _ in range(iters):
        Q = P @ R.T + t; N = np.empty_like(Q); d = np.full(len(Q), 9.0)
        for k, q in enumerate(Q):
            loc, _n, _i, dist = b.find_nearest(Vector(q), lim)
            if loc is not None: N[k] = loc; d[k] = dist
        ok = d < 9
        if ok.sum() < 0.3 * len(P): return R, t, 9.0, 0.0
        kp = ok & (d <= np.quantile(d[ok], keep)); dR, dt = kabsch(Q[kp], N[kp]); R, t = dR @ R, dR @ t + dt
    Q = P @ R.T + t; d = np.array([near_d(b, q, lim, 9.0) for q in Q]); ok = d < 9
    return R, t, float(np.median(d[ok])) if ok.any() else 9.0, float(ok.mean())


def flush(b, P, R, t, iters=30, keep=0.6):
    """pull points flat onto the host (trimmed ICP, no score)"""
    for _ in range(iters):
        Q = P @ R.T + t; N, d, _ins = probe(b, Q, 3.0); ok = d < 9
        if ok.sum() < 40: break
        kp = ok & (d <= np.quantile(d[ok], keep))
        dR, dt = kabsch(Q[kp], N[kp]); R, t = dR @ R, dR @ t + dt
    return R, t


def sphere_fit(P):
    A = np.c_[2 * P, np.ones(len(P))]; x = np.linalg.lstsq(A, (P ** 2).sum(1), rcond=None)[0]
    return x[:3], math.sqrt(max(x[3] + x[:3] @ x[:3], 1e-9))


def part_inside(o):
    """world vertices of the part's inside: those whose normal looks at the fitted sphere's centre (a pad's dome)"""
    V, N = world_vn(o); c, R = sphere_fit(V); m = np.ones(len(V), bool)
    for _ in range(8):
        d = c - V; m2 = (N * d).sum(1) / np.maximum(np.linalg.norm(d, axis=1), 1e-9) > 0.6
        if m2.sum() < 30: break
        m = m2; c, R = sphere_fit(V[m])
    return V[m]


def flat_patches(o, top=3):
    """the host's biggest flat patches, world: [(centre, normal, area)], biggest first (seat_shape2)"""
    mw = o.matrix_world; n3 = mw.to_3x3(); bins = {}
    for p in o.data.polygons:
        nv = n3 @ p.normal
        if nv.length < 1e-9: continue
        nv = np.array(nv.normalized()); c = np.array(mw @ p.center)
        key = tuple(np.round(nv * 8).astype(int)) + (int(round(float(c @ nv) / 0.3)),)
        b = bins.setdefault(key, [0.0, np.zeros(3), np.zeros(3)]); b[0] += p.area; b[1] += c * p.area; b[2] += nv * p.area
    out = sorted(((a, cs / a, ns / np.linalg.norm(ns)) for a, cs, ns in bins.values() if a > 1.0), key=lambda f: -f[0])
    return [(c, n, a) for a, c, n in out[:top]]


def flats(o, min_area=3.0, nbin=10, dbin=0.25):
    """big flat patches, world: [(area, centroid, normal, bbox min, bbox max, face indices)], biggest first (flats.py)"""
    me = o.data; n = len(me.polygons)
    nr = np.empty(n * 3); me.polygons.foreach_get("normal", nr); nr = nr.reshape(-1, 3)
    ce = np.empty(n * 3); me.polygons.foreach_get("center", ce); ce = ce.reshape(-1, 3)
    ar = np.empty(n); me.polygons.foreach_get("area", ar)
    M = np.array(o.matrix_world); R = M[:3, :3]; s = abs(np.linalg.det(R)) ** (1 / 3)
    N = nr @ np.linalg.inv(R); N /= np.maximum(np.linalg.norm(N, axis=1), 1e-12)[:, None]
    Cw = ce @ R.T + M[:3, 3]; A = ar * s * s
    key = np.c_[np.round(N * nbin).astype(int), np.round((Cw * N).sum(1) / dbin).astype(int)]
    groups = {}
    for i, k in enumerate(map(tuple, key)): groups.setdefault(k, []).append(i)
    res = []
    for idx in groups.values():
        idx = np.array(idx); a = A[idx].sum()
        if a < min_area: continue
        c = (Cw[idx] * A[idx, None]).sum(0) / a; nn = (N[idx] * A[idx, None]).sum(0); nn /= np.linalg.norm(nn)
        res.append((float(a), c, nn, Cw[idx].min(0), Cw[idx].max(0), idx))
    res.sort(key=lambda r: -r[0]); return res


def fib(n):
    i = np.arange(n) + 0.5; phi = np.arccos(1 - 2 * i / n); th = math.pi * (1 + 5 ** 0.5) * i
    return np.c_[np.cos(th) * np.sin(phi), np.sin(th) * np.sin(phi), np.cos(phi)]


def inside_share(host_bvh, P, lim=3.0, depth=0.05):
    """share of points P that sit inside the host by more than depth (clash checks)"""
    n = 0
    for q in P:
        l, nor, _i, _d = host_bvh.find_nearest(Vector(q), lim)
        if l is not None and (Vector(q) - l).dot(nor) < -depth: n += 1
    return n / max(1, len(P))

"""Shared numpy geometry for kit scripts: STL reading, frames, Kabsch / ICP, flat faces, spheres.
One copy of the helpers that kits/lib/fitlib.py, kits/lib/stl_io.py and kits/nc/geo.py each carried (moved here
unchanged). New scripts import from here:   from kb.geo import read_stl, stl, icp, best_fit, flats, spheres
No fixed paths; nothing here reads the add-on. scipy is only needed by the ICP functions."""
import numpy as np
try:
    from scipy.spatial import cKDTree
except ImportError:                      # the PC may not have scipy: STL reading and frames still work
    cKDTree = None

def read_stl(p):
    with open(p, 'rb') as f:
        f.read(80); n = np.frombuffer(f.read(4), np.uint32)[0]
        rec = np.frombuffer(f.read(n * 50), dtype=[("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")])
    tri = rec["v"].reshape(-1, 3, 3).astype(float)
    V, inv = np.unique(tri.reshape(-1, 3).round(5), axis=0, return_inverse=True)
    T = inv.reshape(-1, 3)
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    N = np.zeros_like(V)
    for i in range(3): np.add.at(N, T[:, i], fn)
    N /= np.linalg.norm(N, axis=1)[:, None] + 1e-12
    return V, N, T


MX3 = np.diag([-1.0, 1, 1]); MX = np.diag([-1.0, 1, 1, 1])
def stl(path):
    v, n, t = read_stl(path); V = np.asarray(v, float); T = np.asarray(t, np.int64)
    q = np.round(V, 5); u, inv = np.unique(q, axis=0, return_inverse=True)
    return u, inv.reshape(-1)[T]
def M4(x, y, z, o):
    M = np.eye(4); M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = x, y, z, o; return M
def shin_frame(a, b, c, n):
    """tiow_inbox._three_point_frame('Shin', ...)"""
    a, b, c, n = map(np.asarray, (a, b, c, n)); line = (b - a) / np.linalg.norm(b - a); mid = (a + b) / 2
    off = (c - mid) - line * ((c - mid) @ line); x, y = line, off / np.linalg.norm(off); z = np.cross(x, y)
    if z @ n < 0: x, z = -x, -z
    return M4(x, y, z, c)
def pad_frame(a, b, c, forward=None):
    """tiow_inbox._three_point_frame('Pad', ...): Y along the corners (forward if given), Z to the top point."""
    a, b, c = map(np.asarray, (a, b, c)); line = (b - a) / np.linalg.norm(b - a); mid = (a + b) / 2
    off = (c - mid) - line * ((c - mid) @ line); y = line
    if forward is not None and y @ forward < 0: y = -y
    z = off / np.linalg.norm(off); x = np.cross(y, z)
    return M4(x, y, z, c)
def ang(R): return float(np.degrees(np.arccos(np.clip((np.trace(np.asarray(R)[:3, :3]) - 1) / 2, -1, 1))))
def surf(V, T, n, seed=0):
    tri = V[T]; a = np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1)
    rng = np.random.default_rng(seed); i = rng.choice(len(T), n, p=a / a.sum()); u, w = rng.random(n), rng.random(n)
    m = u + w > 1; u[m], w[m] = 1 - u[m], 1 - w[m]; t = tri[i]
    return t[:, 0] + u[:, None] * (t[:, 1] - t[:, 0]) + w[:, None] * (t[:, 2] - t[:, 0])
def kabsch(P, Q):
    cp, cq = P.mean(0), Q.mean(0); U, S, Vt = np.linalg.svd((P - cp).T @ (Q - cq))
    D = np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U.T))]); R = Vt.T @ D @ U.T; return R, cq - R @ cp
def icp(src, tree, R, t, iters=40, keep=0.85):
    for _ in range(iters):
        P = src @ R.T + t; d, i = tree.query(P); m = d <= np.quantile(d, keep)
        R, t = kabsch(src[m], tree.data[i[m]])
    d, _ = tree.query(src @ R.T + t); return R, t, d
def rots24():
    out = []
    for perm in ((0, 1, 2), (1, 2, 0), (2, 0, 1), (1, 0, 2), (0, 2, 1), (2, 1, 0)):
        for s in ((1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1), (-1, 1, 1), (1, -1, 1), (1, 1, -1), (-1, -1, -1)):
            R = np.zeros((3, 3)); R[range(3), perm] = s
            if np.linalg.det(R) > 0: out.append(R)
    return out
def best_fit(src, tgt_pts, inits=None, iters=30):
    tree = cKDTree(tgt_pts); best = None
    for R0 in (inits or rots24()):
        t0 = tgt_pts.mean(0) - R0 @ src.mean(0)
        R, t, d = icp(src, tree, R0, t0, iters)
        if best is None or np.median(d) < best[0]: best = (np.median(d), R, t)
    R, t, d = icp(src, tree, best[1], best[2], 80)
    return R, t, d
def pose(R, t):
    M = np.eye(4); M[:3, :3], M[:3, 3] = R, t; return M


# ---- flat faces, circles and spheres (from the BBoosty / CyberBrush survey)
def tri(V, F):
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    n = np.cross(b - a, c - a); ar = np.linalg.norm(n, axis=1) / 2
    n = n / np.maximum(2 * ar, 1e-12)[:, None]
    return n, ar, (a + b + c) / 3
def components(F, sel):
    """connected components (shared vertex) among the selected faces -> list of face index arrays"""
    idx = np.nonzero(sel)[0]
    if len(idx) == 0: return []
    parent = {}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    vf = {}
    for i in idx:
        parent[i] = i
        for v in F[i]:
            vf.setdefault(v, []).append(i)
    for fs in vf.values():
        r = find(fs[0])
        for g in fs[1:]:
            rg = find(g)
            if rg != r: parent[rg] = r
    groups = {}
    for i in idx: groups.setdefault(find(i), []).append(i)
    return [np.array(g) for g in sorted(groups.values(), key=len, reverse=True)]
def flats(V, F, n_ref, cos=0.995, min_area=1.0):
    """planar patches facing n_ref: [(area, centroid, normal, faces)] largest first"""
    n, ar, c = tri(V, F)
    sel = n @ np.asarray(n_ref, float) > cos
    out = []
    for g in components(F, sel):
        A = ar[g].sum()
        if A < min_area: continue
        cen = (c[g] * ar[g, None]).sum(0) / A
        nn = (n[g] * ar[g, None]).sum(0); nn /= np.linalg.norm(nn)
        out.append((A, cen, nn, g))
    return sorted(out, key=lambda t: -t[0])
def outline(V, F, faces):
    """boundary vertices of a face set (edges used once)"""
    E = np.sort(np.concatenate([F[faces][:, [0, 1]], F[faces][:, [1, 2]], F[faces][:, [2, 0]]]), 1)
    u, cnt = np.unique(E, axis=0, return_counts=True)
    return V[np.unique(u[cnt == 1])]
def circle_fit(P, n):
    """least-squares circle of points P in the plane normal n: centre, radius, rms"""
    n = np.asarray(n, float); n /= np.linalg.norm(n)
    a = np.cross(n, [1, 0, 0]) if abs(n[0]) < 0.9 else np.cross(n, [0, 1, 0]); a /= np.linalg.norm(a); b = np.cross(n, a)
    o = P.mean(0); x = (P - o) @ a; y = (P - o) @ b
    A = np.c_[2 * x, 2 * y, np.ones(len(x))]; s = np.linalg.lstsq(A, x * x + y * y, rcond=None)[0]
    r = np.sqrt(s[2] + s[0] ** 2 + s[1] ** 2); cen = o + s[0] * a + s[1] * b
    rms = np.sqrt(np.mean((np.hypot(x - s[0], y - s[1]) - r) ** 2))
    return cen, r, rms
def vnormals(V, F):
    n, ar, c = tri(V, F)
    N = np.zeros_like(V)
    for k in range(3): np.add.at(N, F[:, k], n * ar[:, None])
    return N / np.maximum(np.linalg.norm(N, axis=1), 1e-12)[:, None]
def spheres(V, F, radii, cell=0.08, top=5, convex=True):
    """ball / dome finder: every vertex votes for the centre one radius inside; returns
    [(score, r, centre, n_support)] best first (score = support / expected count for a full ball)"""
    N = vnormals(V, F)
    sgn = 1.0 if convex else -1.0
    out = []
    for r in radii:
        C = V - sgn * r * N
        q = np.floor(C / cell).astype(np.int64)
        key, inv, cnt = np.unique(q, axis=0, return_inverse=True, return_counts=True)
        inv = inv.ravel()
        for k in np.argsort(-cnt)[:top]:
            # gather votes in the 3x3x3 neighbourhood
            cen0 = (key[k] + 0.5) * cell
            d = np.linalg.norm(C - cen0, axis=1); m = d < 1.5 * cell
            cen = C[m].mean(0)
            # refine: points within r +- tol of the centre with normals pointing out
            dv = np.linalg.norm(V - cen, axis=1)
            sup = (np.abs(dv - r) < 0.06) & (np.einsum('ij,ij->i', N, (V - cen) / np.maximum(dv, 1e-9)[:, None]) * sgn > 0.9)
            out.append((m.sum(), r, cen, int(sup.sum())))
    return sorted(out, key=lambda t: -t[0])
def refine_sphere(V, cen, r, tol=0.12, it=20):
    """least squares sphere on the vertices near the given one"""
    for _ in range(it):
        dv = np.linalg.norm(V - cen, axis=1); P = V[np.abs(dv - r) < tol]
        if len(P) < 20: break
        A = np.c_[2 * P, np.ones(len(P))]; s = np.linalg.lstsq(A, (P ** 2).sum(1), rcond=None)[0]
        cen = s[:3]; r = float(np.sqrt(s[3] + cen @ cen))
    return cen, r, len(P)
_FIB = None
def fib(n=200):
    i = np.arange(n) + 0.5; phi = np.arccos(1 - 2 * i / n); th = np.pi * (1 + 5 ** 0.5) * i
    return np.c_[np.cos(th) * np.sin(phi), np.sin(th) * np.sin(phi), np.cos(phi)]
def coverage(V, N, cen, r, tol=0.08, convex=True):
    """fraction of the sphere's directions with surface on it (normals agreeing); and the mean free direction"""
    global _FIB
    if _FIB is None: _FIB = fib(200)
    dv = V - cen; d = np.linalg.norm(dv, axis=1); u = dv / np.maximum(d, 1e-9)[:, None]
    s = 1 if convex else -1
    m = (np.abs(d - r) < tol) & (np.einsum('ij,ij->i', N, u) * s > 0.85)
    if m.sum() < 10: return 0.0, None
    hit = np.zeros(len(_FIB), bool)
    hit[np.unique(np.argmax(u[m] @ _FIB.T, axis=1))] = True
    mean = u[m].mean(0)
    return hit.mean(), mean / np.linalg.norm(mean)
def balls(V, F, rmin, rmax, minc=0.4, k=4):
    N = vnormals(V, F); out = []
    for votes, r, c, sup in spheres(V, F, np.arange(rmin, rmax + 1e-9, 0.05), top=8):
        c2, r2, n2 = refine_sphere(V, c, r)
        if not (rmin - 0.05 < r2 < rmax + 0.05): continue
        if any(np.linalg.norm(c2 - o['c']) < 0.8 * r2 for o in out): continue
        cov, free = coverage(V, N, c2, r2)
        if cov >= minc: out.append(dict(c=c2, r=r2, cov=cov, free=free, votes=votes))
    return sorted(out, key=lambda o: -o['cov'] * o['votes'])[:k]

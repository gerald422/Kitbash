"""Geometry helpers for the BBoosty / CyberBrush survey (decimated npz meshes)."""
import numpy as np, glob, os
NPZ = "/home/claude/kits/nc/npz"
def key_files(pat):
    return sorted(glob.glob(os.path.join(NPZ, f"*{pat}*.npz")))
def load(f):
    d = np.load(f); return d['V'].astype(float), d['F'].astype(np.int64)
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

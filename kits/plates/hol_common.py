"""Shared bits for fitting library holsters, pouches and grenades onto the hip plate's Plate Hang L socket."""
import json, os, numpy as np
from scipy.spatial import cKDTree
U = "/mnt/user-data/uploads/d/Kitbash Library/"; LIB = os.path.join(os.path.dirname(__file__), "..", "..", "library") + "/"
AM = "Mar Fil - Tacticus/AssaultMarines-V2/"
M16 = lambda a: np.array(a, float).reshape(4, 4)
def stl(p):
    b = open(p, "rb").read(); n = np.frombuffer(b[80:84], np.uint32)[0]
    v = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))["v"].reshape(-1, 3).astype(float)
    V, inv = np.unique(v, axis=0, return_inverse=True); return V, inv.reshape(-1, 3)
def tf(M, V): return V @ M[:3, :3].T + M[:3, 3]
def surf(V, T, n=150000, seed=0):
    r = np.random.default_rng(seed); a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]; cr = np.cross(b - a, c - a); ar = np.linalg.norm(cr, axis=1); k = ar > 0
    a, b, c, cr, ar = a[k], b[k], c[k], cr[k], ar[k]; i = r.choice(len(a), n, p=ar / ar.sum()); u, w = r.random(n), r.random(n); m = u + w > 1; u[m], w[m] = 1 - u[m], 1 - w[m]
    return a[i] + u[:, None] * (b[i] - a[i]) + w[:, None] * (c[i] - a[i]), cr[i] / ar[i, None]
_trees = {}
def side(P, S, N, bound=1.5):        # signed distance of points P to the closed surface sampled as (S, N): < 0 inside
    k = id(S)
    if k not in _trees: _trees[k] = cKDTree(S)
    d, j = _trees[k].query(P, distance_upper_bound=bound); far = ~np.isfinite(d); j[far] = 0   # beyond `bound`: outside
    s = np.sign(np.einsum("ij,ij->i", P - S[j], N[j])); s[far] = 1; d[far] = bound; return d * s
plate = json.load(open(LIB + AM + "Hip Plates/MarFil Assault - Hip Plate L.sockets.json"))
SPH = M16([s for s in plate["sockets"] if s["type"] == "Plate Hang L"][0]["matrix"])      # plate file -> hang socket frame
PV, PT = stl(U + AM + "Hip Plates/MarFil Assault - Hip Plate L.stl")
PVs = tf(np.linalg.inv(SPH), PV)                       # the plate in the hang socket's frame

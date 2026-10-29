"""Mesh loading with an npz cache, plus small geometry helpers."""
import numpy as np, os, hashlib, sys
sys.path.insert(0, "/home/claude/real")
import fitlib as F
from scipy.spatial import cKDTree
RAW = "/home/claude/raw/"
CACHE = "/home/claude/kits/cache/"
U = "/mnt/user-data/uploads/new cults/All Mar All the time/"

def path_of(rel):
    for base in (RAW, U):
        if os.path.exists(base + rel): return base + rel
    raise FileNotFoundError(rel)

def load(rel):
    """(V, T) unique vertices and triangles of a raw kit file (path relative to 'All Mar All the time')."""
    key = hashlib.md5(rel.encode()).hexdigest()
    c = CACHE + key + ".npz"
    if os.path.exists(c):
        z = np.load(c); return z["V"], z["T"]
    V, T = F.stl(path_of(rel))
    np.savez(c, V=V.astype(np.float32), T=T.astype(np.int32))
    return V.astype(np.float32), T.astype(np.int32)

def surf(V, T, n=20000, seed=0): return F.surf(np.asarray(V, float), T, n, seed)
def ang(R): return F.ang(R)
MX = np.diag([-1.0, 1, 1, 1])

def icp(src, tgt_tree, tgt_pts, R=np.eye(3), t=np.zeros(3), iters=40, trim=0.85):
    for _ in range(iters):
        P = src @ R.T + t
        d, i = tgt_tree.query(P)
        k = d <= np.quantile(d, trim)
        R, t = F.kabsch(src[k], tgt_pts[i[k]])
    d, _ = tgt_tree.query(src @ R.T + t)
    return R, t, d

def region(V, T, centre, radius, n=3000, seed=0):
    S = surf(V, T, max(n * 20, 60000), seed)
    S = S[np.linalg.norm(S - centre, axis=1) < radius]
    if len(S) > n: S = S[np.random.default_rng(seed).choice(len(S), n, replace=False)]
    return S

def M4(R=np.eye(3), t=np.zeros(3)):
    M = np.eye(4); M[:3, :3] = R; M[:3, 3] = t; return M

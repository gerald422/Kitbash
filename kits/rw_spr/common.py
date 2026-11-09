"""Shared bits for the Nov 9 batch: Redwarden Techmarine Conversion Kit (Prime torso, helmets, pads) and the new
Springles helmets / pads / accessories (heresy scale x1.1, as Josh's Springles arms)."""
import sys, os, json, numpy as np
sys.path.insert(0, "/home/claude/kits"); sys.path.insert(0, "/home/claude/kits/cr"); sys.path.insert(0, "/home/claude/real")
import fitlib as F, geo
from scipy.spatial import cKDTree
U = "/mnt/user-data/uploads/d/new cults/"
RW = "Warhammer Techmarine Conversion Kit (1)/Warhammer Techmarine Conversion Kit @STL_Printer/"
LIBU = "/mnt/user-data/uploads/d/Kitbash Library/"
SPR_SCALE = 1.1
def load(rel, scale=1.0):
    V, T = F.stl(U + rel); return np.asarray(V, float) * scale, np.asarray(T, int)
def rz(a):
    c, s = np.cos(a), np.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])
def M4(R, t): M = np.eye(4); M[:3, :3] = R; M[:3, 3] = t; return M
def flat(M): return [round(float(x), 6) for x in np.asarray(M).reshape(-1)]
def lib_sidecar(rel): return json.load(open(LIBU + rel, encoding="utf-8-sig"))
def icp_starts(src_full, src_reg, Q, starts, iters=(40, 30)):
    """best rigid map src -> Q over rotation starts about Z (each start also centres src on Q): a coarse pass on 400
    points from every start, then the best three refined on all points."""
    tree = cKDTree(Q); coarse = []
    sub = src_full[np.random.default_rng(3).choice(len(src_full), min(400, len(src_full)), replace=False)]
    for R0 in starts:
        t0 = Q.mean(0) - R0 @ src_full.mean(0)
        R, t, d = geo.icp(sub, tree, Q, R0, t0, 25); coarse.append((float(np.median(d)), R, t))
    best = None
    for _, R, t in sorted(coarse, key=lambda c: c[0])[:3]:
        R, t, d = geo.icp(src_full, tree, Q, R, t, iters[0])
        if src_reg is not None: R, t, d = geo.icp(src_reg, tree, Q, R, t, iters[1])
        m = float(np.median(d))
        if best is None or m < best[0]: best = (m, R, t)
    return best

"""Find a known hand (template) inside a with-hand part: ICP of the template onto the part from
starts at every ball candidate x a spread of rotations; best = lowest median distance."""
import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation as Rot
from geo import *
from align import kabsch
def icp_into(src, tree, dstV, M0, it=40, trim=0.8):
    M = M0.copy()
    for _ in range(it):
        P = src @ M[:3, :3].T + M[:3, 3]; d, j = tree.query(P)
        keep = d <= np.quantile(d, trim)
        dM = kabsch(P[keep], dstV[j[keep]]); M = dM @ M
        if np.abs(dM - np.eye(4)).max() < 1e-6: break
    P = src @ M[:3, :3].T + M[:3, 3]; d = tree.query(P)[0]
    return M, float(np.median(d)), float(np.quantile(d, 0.9))
def find_hand(tV, tball, V, F, starts=None, nrot=60, ns=1500, seed=0):
    rs = np.random.default_rng(seed)
    src = tV[rs.choice(len(tV), min(ns, len(tV)), replace=False)]
    tree = cKDTree(V)
    if starts is None:
        starts = [b['c'] for b in balls(V, F, 0.95, 1.45, minc=0.3, k=8)]
    R = Rot.random(nrot, random_state=seed).as_matrix()
    best = None
    for s in starts:
        for Rk in R:
            M0 = np.eye(4); M0[:3, :3] = Rk; M0[:3, 3] = s - Rk @ tball
            M, med, q9 = icp_into(src, tree, V, M0, it=15)
            if best is None or q9 < best[2]: best = (M, med, q9)
    M, med, q9 = icp_into(src, tree, V, best[0], it=60, trim=0.9)
    return M, med, q9

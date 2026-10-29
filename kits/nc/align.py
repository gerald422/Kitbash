"""Rigid alignment of an STL mesh (npz) onto a sampled copy of it (Josh's object local coords)."""
import numpy as np
from scipy.spatial import cKDTree
def kabsch(P, Q, w=None):
    w = np.ones(len(P)) if w is None else w
    pc = (P * w[:, None]).sum(0) / w.sum(); qc = (Q * w[:, None]).sum(0) / w.sum()
    H = ((P - pc) * w[:, None]).T @ (Q - qc)
    U, S, Vt = np.linalg.svd(H); D = np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U.T))])
    R = Vt.T @ D @ U.T; M = np.eye(4); M[:3, :3] = R; M[:3, 3] = qc - R @ pc; return M
def icp(src, dst, M0, it=60, trim=0.9):
    tree = cKDTree(dst); M = M0.copy()
    for _ in range(it):
        P = src @ M[:3, :3].T + M[:3, 3]; d, j = tree.query(P)
        keep = d <= np.quantile(d, trim)
        dM = kabsch(P[keep], dst[j[keep]]); M = dM @ M
        if np.abs(dM - np.eye(4)).max() < 1e-7: break
    P = src @ M[:3, :3].T + M[:3, 3]; d = tree.query(P)[0]
    return M, float(np.median(d)), float(np.quantile(d, 0.95))
def rots():
    """24 axis-aligned rotations"""
    import itertools
    out = []
    for p in itertools.permutations(range(3)):
        for s in itertools.product([1, -1], repeat=3):
            R = np.zeros((3, 3))
            for i in range(3): R[i, p[i]] = s[i]
            if np.linalg.det(R) > 0: out.append(R)
    return out
def align(src, dst, n=4000):
    """best of PCA + axis-aligned starts"""
    rs = np.random.default_rng(0)
    s = src[rs.choice(len(src), min(n, len(src)), replace=False)]
    best = None
    for R in rots():
        M0 = np.eye(4); M0[:3, :3] = R; M0[:3, 3] = dst.mean(0) - R @ s.mean(0)
        M, med, q95 = icp(s, dst, M0, it=25)
        if best is None or med < best[1]: best = (M, med, q95)
    M, med, q95 = icp(s, dst, best[0], it=80)
    return M, med, q95

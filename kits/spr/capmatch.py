"""Swing of each Springles arm's shoulder (rotation about the shoulder disc axis) relative to a reference arm:
1-DOF search of the shoulder region, then a short ICP. Right-arm space (lefts mirrored)."""
import sys, json, numpy as np
sys.path.insert(0, '/home/claude/kits'); sys.path.insert(0, '/home/claude/kits/cr'); sys.path.insert(0, '/home/claude/real')
import stlcache, fitlib as F
from scipy.spatial import cKDTree
from spr_arms import S_R, S_L, S_H
U = "/mnt/user-data/uploads/new cults/Springles/"; ST = "/home/claude/kits/out113/stage_spr/Springles/"
D0 = S_H[:3, 3]; AX = S_H[:3, 1] / np.linalg.norm(S_H[:3, 1])         # out of the body
def torso_pts(rel, n=150000):
    s = json.load(open(ST + rel[:-4] + ".sockets.json")); side = list(s["fits"])[0][-1]
    W = (S_R if side == "R" else S_L) @ np.array(s["fits"]["Shoulder " + side]).reshape(4, 4)
    V, T = stlcache.load(U + rel); P = F.surf(np.asarray(V, float) * s["scale"], T, n, 0) @ W[:3, :3].T + W[:3, 3]
    if side == "L": P = P * [-1, 1, 1]
    return side, W, P
def shoulder(P, r=5.5):
    L = P - D0; return P[(np.linalg.norm(L, axis=1) < r) & (L @ AX > 0.4)]
def rot(th):
    k = AX; K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(th) * K + (1 - np.cos(th)) * K @ K
def match(ref, tgt):
    tree = cKDTree(tgt); best = None
    sub = ref[np.random.default_rng(0).choice(len(ref), min(3000, len(ref)), replace=False)]
    for th in np.radians(np.arange(-180, 180, 3)):
        R = rot(th); d, _ = tree.query((sub - D0) @ R.T + D0)
        m = np.median(d)
        if best is None or m < best[0]: best = (m, th)
    th0 = best[1]
    for step in (1.0, 0.25):
        cands = [th0 + np.radians(step * k) for k in range(-3, 4)]
        sc = [np.median(tree.query((sub - D0) @ rot(t).T + D0)[0]) for t in cands]; th0 = cands[int(np.argmin(sc))]
    R = rot(th0); d, _ = tree.query((sub - D0) @ R.T + D0)
    return float(np.degrees(th0)), float(np.median(d))
if __name__ == "__main__":
    ref = sys.argv[1]; _, _, Pr = torso_pts(ref); SR = shoulder(Pr)
    for rel in sys.argv[2:]:
        side, W, P = torso_pts(rel); th, m = match(SR, shoulder(P))
        print("%-55s %s swing %7.1f  median %.3f" % (rel[-55:], side, th, m))
def match3(ref, tgt, th0):
    """rotation about the shoulder disc centre (3 DOF), starting from the 1-DOF swing"""
    tree = cKDTree(tgt); sub = ref[np.random.default_rng(1).choice(len(ref), min(4000, len(ref)), replace=False)] - D0
    R = rot(np.radians(th0))
    for _ in range(30):
        Q = sub @ R.T; d, i = tree.query(Q + D0); k = d <= np.quantile(d, 0.85)
        A = sub[k]; B = tgt[i[k]] - D0
        Uu, _, Vt = np.linalg.svd(A.T @ B); Dd = np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ Uu.T))]); R = Vt.T @ Dd @ Uu.T
    d, _ = tree.query(sub @ R.T + D0)
    return R, float(np.median(d))
def _rotations(maxdeg=150, n=4000, seed=2):
    rng = np.random.default_rng(seed); out = [np.eye(3)]
    while len(out) < n:
        q = rng.normal(size=4); q /= np.linalg.norm(q)
        w, x, y, z = q
        R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
        if np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))) <= maxdeg: out.append(R)
    return out
_ROTS = None
def match_any(ref, tgt):
    """rotation about the disc centre from a global search (any swing / raise), then ICP"""
    global _ROTS
    if _ROTS is None: _ROTS = _rotations()
    tree = cKDTree(tgt); rng = np.random.default_rng(3)
    small = ref[rng.choice(len(ref), min(500, len(ref)), replace=False)] - D0
    sc = []
    for R in _ROTS:
        d, _ = tree.query(small @ R.T + D0); sc.append(np.median(d))
    best = None
    for j in np.argsort(sc)[:15]:
        R0 = _ROTS[j]
        th0 = 0.0
        sub = ref[rng.choice(len(ref), min(4000, len(ref)), replace=False)] - D0; R = R0
        for _ in range(25):
            Q = sub @ R.T; d, i = tree.query(Q + D0); k = d <= np.quantile(d, 0.85)
            A = sub[k]; B = tgt[i[k]] - D0
            Uu, _, Vt = np.linalg.svd(A.T @ B); Dd = np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ Uu.T))]); R = Vt.T @ Dd @ Uu.T
        d, _ = tree.query(sub @ R.T + D0); m = float(np.median(d))
        if best is None or m < best[0]: best = (m, R)
    return best[1], best[0]

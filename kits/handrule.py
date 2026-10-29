"""Rule: a hand-held part's wrist frame.
Find round stub caps (flat oval faces capping a short neck), fit the reference fist behind each (roll searched), keep the best.
Frame: Y = the cap's normal (out of the hand, into the arm), origin = cap centre pushed SEAT into the hand,
Z = the fist's 'top' (Josh's blade side) laid into the cap plane, X = Y x Z."""
import sys; sys.path.insert(0, '/home/claude/kits')
import numpy as np, wristrule as W
from scipy.spatial import cKDTree
import geo
FIST = np.load('/home/claude/kits/fistref.npy')
SEAT = 0.19
MXv = np.array([-1.0, 1, 1])
def rot_y(d):
    a = np.radians(d); c, s = np.cos(a), np.sin(a); return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
def basis(nn):
    X0 = np.cross(nn, [0, 0, 1.0]) if abs(nn[2]) < 0.9 else np.cross(nn, [1.0, 0, 0]); X0 /= np.linalg.norm(X0)
    return np.c_[X0, nn, np.cross(X0, nn)]
def hand_frame(V, T, side, fist=FIST):
    V = np.asarray(V, float)
    ref = fist * (MXv if side == 'L' else 1)
    caps = W.stub_caps(V, T)
    if not caps: return None, None
    S = geo.surf(V, T, 150000); tree = cKDTree(S)
    rng = np.random.default_rng(0)
    tiny = ref[rng.choice(len(ref), 150, replace=False)]; mid = ref[rng.choice(len(ref), 600, replace=False)]
    seeds = []
    for ci, (score, c, nn, r, ring) in enumerate(caps):
        B = basis(nn)
        if side == 'L': B = B @ np.diag([-1.0, 1, 1])   # the mirrored fist's frame, kept proper below
        for roll in range(0, 360, 15):
            R0 = basis(nn) @ rot_y(roll)
            d, _ = tree.query(tiny @ R0.T + c)
            seeds.append((np.median(d), ci, roll, R0, c))
    seeds.sort(key=lambda x: x[0])
    tried = []
    for m, ci, roll, R, t in seeds[:10] + [s for s in seeds if True][:0]:
        R, t, d = geo.icp(mid, tree, S, R, t, 20); tried.append((float(np.median(d)), ci, R, t))
    tried.sort(key=lambda x: x[0])
    md, ci, R, t = tried[0]
    # the other way up (a fist rolled half a turn can look nearly as good)
    c, nn = caps[ci][1], caps[ci][2]
    Rf = np.linalg.inv(basis(nn)).T  # noop placeholder to keep shapes clear
    flip = R.copy(); A = np.eye(3) - 2 * np.outer(nn, nn)   # half turn about the cap normal: v -> 2(v.n)n - v
    Rh = 2 * np.outer(nn, nn) - np.eye(3)
    R2, t2, d2 = geo.icp(mid, tree, S, Rh @ R, Rh @ (t - c) + c, 20)
    if np.median(d2) < md: R, t, md = R2, t2, float(np.median(d2))
    R, t, d = geo.icp(ref, tree, S, R, t, 25)
    md = float(np.median(d))
    # frame
    Y = nn
    Z = R[:, 2] - (R[:, 2] @ Y) * Y; Z /= np.linalg.norm(Z)
    X = np.cross(Y, Z)
    M = np.eye(4); M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = X, Y, Z, c - SEAT * Y
    return M, dict(med=md, cap=c.tolist(), r=float(caps[ci][3]), ncaps=len(caps))

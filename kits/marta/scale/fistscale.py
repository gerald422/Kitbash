import sys; sys.path.insert(0, '/home/claude/real')
import fitlib as F, numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation as Rot
U = "/mnt/user-data/uploads/new cults/"
M = U + "Marta/51 May 2026-20260612T074408Z-3-001/51 May 2026/amrs and weapons/"
tgt = np.load('/home/claude/kits/fistref.npy'); tree = cKDTree(tgt)
def umeyama(A, B):
    ma, mb = A.mean(0), B.mean(0); a, b = A - ma, B - mb
    U_, S, Vt = np.linalg.svd(b.T @ a / len(A))
    d = np.sign(np.linalg.det(U_ @ Vt)); D = np.diag([1, 1, d])
    R = U_ @ D @ Vt; s = (S * np.diag(D)).sum() / (a ** 2).sum() * len(A)
    return s, R, mb - s * R @ ma
def sicp(src, s, R, t, it=60, trim=0.8):
    for _ in range(it):
        P = s * src @ R.T + t; d, i = tree.query(P); k = d <= np.quantile(d, trim)
        s, R, t = umeyama(src[k], tgt[i[k]])
    d, _ = tree.query(s * src @ R.T + t)
    # two-way: how much of the reference is covered
    d2, _ = cKDTree(s * src @ R.T + t).query(tgt)
    return s, R, t, np.median(d), np.median(d2)
for name in sys.argv[1:]:
    V, T = F.stl(M + name); S = F.surf(V, T, 6000, 0)
    res = []
    for q in Rot.random(150, random_state=1).as_matrix():
        for s0 in (0.8, 0.9, 1.0):
            t0 = tgt.mean(0) - s0 * S.mean(0) @ q.T
            s, R, t, m1, m2 = sicp(S, s0, q, t0, 25)
            res.append((m1 + m2, s, m1, m2))
    res.sort()
    print(name, 'best scale %.3f  (fit %.3f/%.3f mm)' % (res[0][1], res[0][2], res[0][3]), ' next:', [(round(r[1], 3), round(r[0], 3)) for r in res[1:6]])

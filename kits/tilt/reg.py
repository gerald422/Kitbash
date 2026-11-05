import numpy as np
from scipy.spatial import cKDTree
Matrix = lambda a: np.array(a)

def rots24():
    out = []
    for perm in ([0, 1, 2], [1, 2, 0], [2, 0, 1], [0, 2, 1], [2, 1, 0], [1, 0, 2]):
        for sg in np.array(np.meshgrid([1, -1], [1, -1], [1, -1])).T.reshape(-1, 3):
            R = np.zeros((3, 3)); R[range(3), perm] = sg
            if np.linalg.det(R) > 0: out.append(R)
    return out


def sicp(S, D, R, t, s, it=60, scale=True):
    """Similarity (or rigid, scale=False) ICP S -> D. Returns R, t, s, median and 95% residual."""
    tree = cKDTree(D)
    sub = S[np.random.default_rng(0).choice(len(S), min(len(S), 8000), replace=False)]
    for _ in range(it):
        d, i = tree.query(s * sub @ R.T + t)
        k = d <= max(np.percentile(d, 90), 1e-9)
        A, B = sub[k], D[i[k]]; ca, cb = A.mean(0), B.mean(0); A0, B0 = A - ca, B - cb
        U, sv, Vt = np.linalg.svd(A0.T @ B0); Dm = np.diag([1, 1, np.sign(np.linalg.det(U @ Vt))])
        R = (U @ Dm @ Vt).T
        if scale:
            s = (sv * np.diag(Dm)).sum() / (A0 ** 2).sum()
        t = cb - s * R @ ca
    d, _ = tree.query(s * S @ R.T + t)
    return R, t, s, float(np.median(d)), float(np.percentile(d, 95))


def register(S, D, scale=False):
    """Source points S onto mesh points D: the best of 24 axis turns (centroids and sizes matched), refined by
    ICP (similarity when `scale`: Josh's wings are the OBJs enlarged). Returns A (source -> mesh), s, median, p95."""
    best = None
    s0 = np.sqrt(((D - D.mean(0)) ** 2).sum(1).mean() / ((S - S.mean(0)) ** 2).sum(1).mean()) if scale else 1.0
    for R0 in rots24():
        t0 = D.mean(0) - s0 * R0 @ S.mean(0)
        r = sicp(S, D, R0, t0, s0, it=15, scale=scale)
        if best is None or r[3] < best[3]:
            best = r
    R, t, s, med, p95 = sicp(S, D, best[0], best[1], best[2], it=100, scale=scale)
    A = np.eye(4); A[:3, :3] = s * R; A[:3, 3] = t
    return Matrix(A.tolist()), s, med, p95


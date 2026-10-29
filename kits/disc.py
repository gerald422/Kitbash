import numpy as np
def tri_info(V, T):
    A, B, C = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    n = np.cross(B - A, C - A); a = np.linalg.norm(n, axis=1)
    return (A + B + C) / 3, n / np.maximum(a[:, None], 1e-12), a / 2
def shoulder_discs(V, T, direction, min_area=1.5, tol=0.995, near=None, radius=None):
    """Flat faces whose outward normal is `direction` (unit), grouped by plane offset.
    Returns list of (centre, area, offset) sorted by area, biggest first."""
    cen, n, a = tri_info(np.asarray(V, float), T)
    k = (n @ direction) > tol
    if near is not None: k &= np.linalg.norm(cen - near, axis=1) < radius
    if not k.any(): return []
    off = cen[k] @ direction; c, aa = cen[k], a[k]
    out = []
    order = np.argsort(-off)
    used = np.zeros(len(off), bool)
    for i in order:
        if used[i]: continue
        g = (~used) & (np.abs(off - off[i]) < 0.02)
        # connected-ish: within 4 mm of the seed
        g &= np.linalg.norm(c - c[i], axis=1) < 4.0
        used |= g
        A = aa[g].sum()
        if A >= min_area: out.append(((c[g] * aa[g, None]).sum(0) / A, A, off[i]))
    out.sort(key=lambda x: -x[1])
    return out

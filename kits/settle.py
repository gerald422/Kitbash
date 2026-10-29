import numpy as np, geo
def axis_gap(top_pts, bot_pts, frame, cell=0.25, reach=3.0):
    """Gap along frame Z between `top_pts` (torso, above) and `bot_pts` (legs, below): how far the top can
    slide down -Z before touching. Negative = already overlapping by that much."""
    Fi = np.linalg.inv(frame)
    A = top_pts @ Fi[:3, :3].T + Fi[:3, 3]; B = bot_pts @ Fi[:3, :3].T + Fi[:3, 3]
    ka = np.floor(A[:, :2] / cell).astype(np.int64); kb = np.floor(B[:, :2] / cell).astype(np.int64)
    key = lambda k: k[:, 0] * 100003 + k[:, 1]
    ia, ib = key(ka), key(kb)
    # lowest torso point per cell
    order = np.argsort(ia); ia_s = ia[order]; za = A[order, 2]
    u, start = np.unique(ia_s, return_index=True)
    lo = np.minimum.reduceat(za, start)
    low = dict(zip(u.tolist(), lo.tolist()))
    best = np.inf
    zb = B[:, 2]
    tl = np.array([low.get(k, np.nan) for k in ib.tolist()])
    m = ~np.isnan(tl) & (zb < tl + reach)
    if not m.any(): return np.inf
    return float(np.min(tl[m] - zb[m]))

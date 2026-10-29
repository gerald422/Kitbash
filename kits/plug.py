import numpy as np, disc
def plug_frame(V, T, verbose=False):
    """Frame of the legs' waist plug: origin = centre of its flat top, Z = top normal,
    X = across the plug's flat sides (towards +X of a kit-position legs), Y = Z x X."""
    V = np.asarray(V, float)
    cen, n, a = disc.tri_info(V, T)
    # 1. biggest flat face with an upward-ish normal: the plug top
    up = n[:, 2] > 0.5
    key = np.round(n[up] * 25).astype(int)
    best = None
    import collections
    groups = collections.defaultdict(list)
    for i, kk in zip(np.where(up)[0], map(tuple, key)): groups[kk].append(i)
    for kk, idx in groups.items():
        idx = np.array(idx); nn = n[idx].mean(0); nn /= np.linalg.norm(nn)
        off = cen[idx] @ nn
        # split by plane offset
        for o in np.unique(np.round(off / 0.05)):
            sel = idx[np.abs(off / 0.05 - o) < 0.6]
            # largest connected-ish cluster within 5 mm of its seed
            A = a[sel].sum()
            if best is None or A > best[0]: best = (A, sel)
    A, sel = best
    Z = (n[sel] * a[sel, None]).sum(0); Z /= np.linalg.norm(Z)
    c = (cen[sel] * a[sel, None]).sum(0) / A
    # refine: all faces coplanar with the top within 5 mm of its centre
    k = (np.abs((cen - c) @ Z) < 0.05) & ((n @ Z) > 0.99) & (np.linalg.norm(cen - c, axis=1) < 5)
    c = (cen[k] * a[k, None]).sum(0) / a[k].sum(); A = a[k].sum()
    # 2. side faces just below the top, within the plug radius
    d = (cen - c) @ Z
    r = np.linalg.norm((cen - c) - d[:, None] * Z, axis=1)
    side = (d < -0.2) & (d > -2.5) & (r < 4.5) & (np.abs(n @ Z) < 0.3)
    N = n[side]; W = a[side]
    M = (N * W[:, None]).T @ N
    ev, evec = np.linalg.eigh(M)
    axis = evec[:, 0] * np.sign(evec[:, 0] @ Z)
    # flat sides: faces whose normal is close to +-X'
    flat = side & (np.abs(n @ Z) < 0.05)
    Nf = n[flat]; Wf = a[flat]
    # dominant direction of flat side normals (sign-free): principal axis of n n^T
    Mf = (Nf * Wf[:, None]).T @ Nf
    ev2, ev2v = np.linalg.eigh(Mf)
    X = ev2v[:, -1]; X = X - (X @ Z) * Z; X /= np.linalg.norm(X)
    # sign: the top leans towards the front, so Y = Z x X should agree with the tilt of the top against the plug axis
    tilt = Z - (Z @ axis) * axis
    Y = np.cross(Z, X)
    if Y @ tilt < 0: X, Y = -X, -Y
    F = np.eye(4); F[:3, 0], F[:3, 1], F[:3, 2], F[:3, 3] = X, Y, Z, c
    if verbose: print('top area %.1f  axis-vs-top %.1f deg  flats %.2f' % (A, np.degrees(np.arccos(np.clip(axis @ Z, -1, 1))), ev2[-1] / max(ev2.sum(), 1e-9)))
    return F

def front_sign(V, T, F):
    """+1 if the legs' front (belt buckle side) is +Y of frame F, else -1."""
    S = np.asarray(V, float)
    L = (S - F[:3, 3]) @ F[:3, :3]
    r = np.hypot(L[:, 0], L[:, 1])
    band = (L[:, 2] < -1.0) & (L[:, 2] > -4.5) & (np.abs(L[:, 0]) < 2.0)
    yp = L[band & (L[:, 1] > 0), 1]; yn = -L[band & (L[:, 1] < 0), 1]
    # the buckle reaches further out at the front than the back of the belt
    fp = np.quantile(yp, 0.98) if len(yp) else 0; fn = np.quantile(yn, 0.98) if len(yn) else 0
    return (1 if fp >= fn else -1), fp, fn

def shin_front(V, T):
    """mean outward direction of the two shin holes (the legs' front), or None"""
    import sys; sys.path.insert(0, '/home/claude/real'); import fitlib as F
    V = np.asarray(V, float)
    res = F.find_shin_points(V, T)
    if not res: return None
    zs = []
    for side in res:
        try:
            a, b, c, n = side[:4]
            zs.append(F.shin_frame(a, b, c, n)[:3, 2])
        except Exception:
            pass
    if not zs: return None
    f = np.sum(zs, axis=0); return f / np.linalg.norm(f)

def waist_frame(V, T):
    F = plug_frame(V, T)
    f = shin_front(V, T)
    if f is not None and F[:3, 1] @ f < 0:
        F[:3, 0] *= -1; F[:3, 1] *= -1
    return F, f

def plug_axis_origin(V, T, F):
    """Centre of the plug's round wall (flats excluded), on the top plane of frame F."""
    V = np.asarray(V, float)
    cen, n, a = disc.tri_info(V, T)
    Z, X, c0 = F[:3, 2], F[:3, 0], F[:3, 3]
    d = (cen - c0) @ Z
    P = (cen - c0) - d[:, None] * Z
    r = np.linalg.norm(P, axis=1)
    nz = n @ Z
    k = (d < -0.3) & (d > -2.5) & (r < 4.8) & (r > 1.5) & (np.abs(nz) < 0.3) & (np.abs(n @ X) < 0.9)
    if k.sum() < 20: return c0
    Np = n[k] - nz[k, None] * Z; Np /= np.linalg.norm(Np, axis=1)[:, None]
    # p = c + R*np  ->  solve for c (3, in plane) and R
    A = np.hstack([np.tile(np.eye(3), (k.sum(), 1)), Np.reshape(-1, 1)])
    b = P[k].reshape(-1)
    w = np.repeat(a[k], 3)
    sol, *_ = np.linalg.lstsq(A * np.sqrt(w)[:, None], b * np.sqrt(w), rcond=None)
    c = sol[:3] - (sol[:3] @ Z) * Z
    return c0 + c, sol[3]

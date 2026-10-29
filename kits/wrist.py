"""Carry a known Hand socket from reference arms onto another arm by matching the wrist/forearm cuff."""
import geo, numpy as np, json, disc
from scipy.spatial import cKDTree
def wrist_plane(V, T, joint):
    """biggest flat disc on the arm that faces away from the shoulder joint: (centre, normal out of the arm)"""
    cen, n, a = disc.tri_info(np.asarray(V, float), T)
    far = np.linalg.norm(cen - joint, axis=1)
    k = far > np.quantile(far, 0.6)
    key = np.round(n[k] * 20).astype(int); idx = np.where(k)[0]
    import collections
    g = collections.defaultdict(list)
    for i, kk in zip(idx, map(tuple, key)): g[kk].append(i)
    best = None
    for kk, ii in g.items():
        ii = np.array(ii); nn = (n[ii] * a[ii, None]).sum(0); nn /= np.linalg.norm(nn)
        off = cen[ii] @ nn
        for o in np.unique(np.round(off / 0.05)):
            sel = ii[np.abs(off / 0.05 - o) < 0.6]
            c = (cen[sel] * a[sel, None]).sum(0) / a[sel].sum()
            if (c - joint) @ nn < 0: continue          # must face away from the shoulder
            A = a[sel].sum()
            if best is None or A > best[0]: best = (A, c, nn)
    return best
def rot_about(ax, deg):
    a = np.radians(deg); ax = ax / np.linalg.norm(ax); K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K
def transfer(ref_V, ref_T, ref_hand, ref_joint, V, T, joint, radius=4.0):
    """returns (hand socket on V, median, ref plane, tgt plane)"""
    pr = wrist_plane(ref_V, ref_T, ref_joint); pt = wrist_plane(V, T, joint)
    if pr is None or pt is None: return None
    reg = geo.region(ref_V, ref_T, pr[1], radius, 2500)
    S = geo.surf(V, T, 300000); S = S[np.linalg.norm(S - pt[1], axis=1) < radius + 3]; tree = cKDTree(S)
    # rotation taking ref normal to tgt normal, then roll about it
    a, b = pr[2], pt[2]; v = np.cross(a, b); c = a @ b
    R0 = np.eye(3) if np.linalg.norm(v) < 1e-9 else rot_about(v, np.degrees(np.arctan2(np.linalg.norm(v), c)))
    best = None
    for roll in range(0, 360, 30):
        R1 = rot_about(b, roll) @ R0
        t1 = pt[1] - R1 @ pr[1]
        R, t, d = geo.icp(reg, tree, S, R1, t1, 30)
        m = np.median(d)
        if best is None or m < best[0]: best = (m, R, t)
    m, R, t = best
    R, t, d = geo.icp(reg, tree, S, R, t, 60)
    M = geo.M4(R, t)
    return M @ ref_hand, float(np.median(d)), pr, pt

"""Base settle: how far a base must rise along the legs' Base socket Z until the
lowest foot touches it. Heightfields on a 0.5 mm grid in the socket frame: the
legs' lowest surface (min z) and the base's top (max z), from points on the
triangles (barycentric grid, step 0.25 mm). Same maths as the page and add-on."""
import numpy as np
CELL = 0.5
STEP = 0.25
LOW_BAND = 1000.0

_bary = {}
def bary(k):
    if k not in _bary:
        w = [(i / k, j / k) for i in range(k + 1) for j in range(k + 1 - i)]
        _bary[k] = np.array(w)
    return _bary[k]

def surface_points(P):
    """P: (n,3,3) triangles -> points covering them at about STEP spacing."""
    if not len(P):
        return np.zeros((0, 3))
    e = np.max(np.stack([np.linalg.norm(P[:, 1] - P[:, 0], axis=1), np.linalg.norm(P[:, 2] - P[:, 1], axis=1),
                         np.linalg.norm(P[:, 0] - P[:, 2], axis=1)]), axis=0)
    k = np.clip(np.ceil(e / STEP), 1, 60).astype(int)
    out = []
    for kk in np.unique(k):
        sel = P[k == kk]
        w = bary(kk)
        u, v = w[:, 0][None, :, None], w[:, 1][None, :, None]
        pts = sel[:, None, 0] + u * (sel[:, None, 1] - sel[:, None, 0]) + v * (sel[:, None, 2] - sel[:, None, 0])
        out.append(pts.reshape(-1, 3))
    return np.concatenate(out)

def field(pts, mode):
    c = np.floor(pts[:, :2] / CELL).astype(np.int64)
    key = c[:, 0] * 100003 + c[:, 1]
    order = np.argsort(key, kind="stable")
    key, z = key[order], pts[order, 2]
    uk, start = np.unique(key, return_index=True)
    red = np.minimum.reduceat(z, start) if mode == "min" else np.maximum.reduceat(z, start)
    return dict(zip(uk.tolist(), red.tolist()))

def settle(legs_tris, base_tris):
    """Both (n,3,3) in the Base socket frame. Returns the gap (>0: the base must
    rise by it to touch the lowest foot), or None if the feet aren't over it."""
    if not len(legs_tris) or not len(base_tris):
        return None
    zl = legs_tris[:, :, 2].min()
    low = legs_tris[legs_tris[:, :, 2].min(axis=1) < zl + LOW_BAND]
    sole = field(surface_points(low), "min")
    top = field(surface_points(base_tris), "max")
    common = sole.keys() & top.keys()
    if not common:
        return None
    return float(min(sole[k] - top[k] for k in common))

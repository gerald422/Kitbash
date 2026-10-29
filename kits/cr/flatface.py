"""Frames of flat joint faces."""
import sys; sys.path.insert(0,'/home/claude/kits'); sys.path.insert(0,'/home/claude/kits/cr')
import numpy as np, flats, disc
def frame(o, z, yhint):
    z = np.asarray(z, float); z = z / np.linalg.norm(z)
    y = np.asarray(yhint, float); y = y - (y @ z) * z; y /= np.linalg.norm(y)
    x = np.cross(y, z); M = np.eye(4); M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = x, y, z, o; return M
def top_face(V, T, up=(0, 1, 0), min_area=5, cos=0.85, highest=True):
    """the flat face whose outward normal is closest to `up` and that is furthest along it (legs top)."""
    F = flats.flats(V, T, min_area=min_area)
    up = np.asarray(up, float)
    cand = [f for f in F if f[1] @ up > cos]
    if highest: cand.sort(key=lambda f: -(f[2] @ up) - 0.002 * f[0])
    else: cand.sort(key=lambda f: -f[0])
    A, nn, c, o, sel = cand[0]
    return A, nn, c, sel

"""Round base rule (as Marta's): origin = centre of the disc at the rim top, Z up from the bottom face."""
import numpy as np
from geo import *
def base_frame(V, F):
    lo, hi = V.min(0), V.max(0)
    # bottom face: the big flat facing -Z
    fl = flats(V, F, [0, 0, -1], cos=0.99, min_area=50)
    up = np.array([0, 0, 1.0])
    if fl:
        P = outline(V, F, fl[0][3]); cc, r, rms = circle_fit(P, fl[0][2]); up = -fl[0][2]
    else:
        cc = (lo + hi) / 2; r = (hi - lo)[:2].max() / 2
    h = (V - cc) @ up; rad = np.linalg.norm((V - cc) - np.outer(h, up), axis=1)
    rim = h[(rad > 0.75 * rad.max()) & (rad < 0.95 * rad.max())]
    top = np.quantile(rim, 0.9)
    o = cc + up * top
    Z = up / np.linalg.norm(up); X = np.array([-1.0, 0, 0]); X -= (X @ Z) * Z; X /= np.linalg.norm(X); Y = np.cross(Z, X)
    M = np.eye(4); M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = X, Y, Z, o
    return M, float(rad.max()), float(top)

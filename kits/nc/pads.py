"""Pauldrons for creators with round shoulder domes (BBoosty, CyberBrush).
Anchor: Josh's 62 on the Springles heresy arm (actual.blend), moved so 62's inner shell centres on this arm's
shoulder dome -> Mar Fil pads sit on these arms as on the heresy arms. A creator's own pad: its inner shell on the
dome, turned about the vertical so its opening faces the torso."""
import numpy as np, json
from geo import *; from bbrules import *
J = json.load(open('/home/claude/kits/spr/w/josh_pad_h4.json')); A_JOSH = np.array(J['A_josh_torso'])
P62 = json.load(open('/home/claude/kits/nc/pad62.json'))
INNER62 = (A_JOSH @ np.array(P62['F62']) @ np.r_[P62['inner'][0], 1])[:3]
def dome_world(V, F, W, side, near=None):
    """the shoulder dome (convex ball r 2.3-3.4) nearest the 62 seat, in torso coords; None if hidden"""
    Vw = V @ W[:3, :3].T + W[:3, 3]
    ref = INNER62 * ([1, 1, 1] if side == 'R' else [-1, 1, 1]) if near is None else near
    b = [o for o in balls(Vw, F, 2.2, 3.4, minc=0.25, k=6) if np.linalg.norm(o['c'] - ref) < 2.5]
    if not b: return None
    return min(b, key=lambda o: np.linalg.norm(o['c'] - ref))
def anchor_world(dome_c, side):
    if side == 'R':
        return T(dome_c - INNER62) @ A_JOSH
    return MX @ (T(MX[:3, :3] @ dome_c - INNER62) @ A_JOSH) @ MX
def pad_inner(V, F):
    N = vnormals(V, F); res = []
    for votes, r, c, sup in spheres(V, F, np.arange(2.3, 4.2, 0.1), top=3, convex=False)[:8]:
        c2, r2, n2 = refine_sphere(V, c, r); cov, fr = coverage(V, N, c2, r2, convex=False)
        if 2.3 < r2 < 4.3 and cov > 0.18: res.append((cov * votes, r2, c2, -fr))
    if not res: return None
    s, r, c, o = max(res, key=lambda x: x[0]); return dict(r=r, c=c, open=o)
def pad_fit_R(inner):
    """Pad R fit: the inner shell centre on 62's seat, opening turned (about the vertical) to face the torso (-X)"""
    h = inner['open'][:2]; ang = np.arctan2(h[1], h[0]); target = np.pi      # -> -X
    a = target - ang; c, s = np.cos(a), np.sin(a)
    Rz = np.array([[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1.0]])
    return np.linalg.inv(A_JOSH) @ T(INNER62) @ Rz @ T(-inner['c'])
from align import rots
OPEN_T = np.array([-0.6, 0.0, -0.8])
def pad_fit_R2(inner):
    """the axis turn that brings the pad's opening nearest inward-and-down (prints are square to the axes), inner shell on 62's seat"""
    best = max(rots(), key=lambda Rk: (Rk @ inner['open']) @ OPEN_T)
    M = np.eye(4); M[:3, :3] = best
    return np.linalg.inv(A_JOSH) @ T(INNER62) @ M @ T(-inner['c']), float((best @ inner['open']) @ OPEN_T)

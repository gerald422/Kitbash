"""BBoosty rules. BBoosty export their parts in the model's own axes, only moved for printing:
file -Y = front, -X = the model's right (Mar Fil: +Y front, +X right) -> Rz(180) between the two
(Josh's Backpack2 on 23-Torso-2 confirms it). Arms: the round flat shoulder face (r ~2-2.6, facing
+X on right arms, -X on left) goes on the heresy shoulder point Josh set for Springles (S_H)."""
import numpy as np, json, os
from geo import *
from bbarm import all_flats
S_H = np.array([[-0.0288, 0.9996, 0, 5.3108], [-0.9996, -0.0288, 0, 0.2019], [0, 0, 1, 31.2218], [0, 0, 0, 1.0]])
S_R = np.eye(4); S_R[:3, 3] = [5.4838, 0.2019, 31.9493]
S_L = np.eye(4); S_L[:3, 3] = [-5.4838, 0.2019, 31.9493]
S_BACK = np.array([[1.0, 0.0, 0.0, 0.0], [0.0, 0.998, 0.0627, -5.6453], [0.0, -0.0627, 0.998, 33.3381], [0, 0, 0, 1]])
S_NECK = np.array([[-1.0, 0.0042, -0.0017, 0.0034], [-0.0046, -0.9298, 0.3681, 0.176], [-0.0, 0.3681, 0.9298, 32.7399], [0, 0, 0, 1]])
MX = np.diag([-1.0, 1, 1, 1])
RZ180 = np.diag([-1.0, -1, 1, 1])
RZm90 = np.array([[0, 1, 0, 0], [-1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1.0]])
def T(c): M = np.eye(4); M[:3, 3] = c; return M
def rot_between(a, b):
    a = np.asarray(a, float) / np.linalg.norm(a); b = np.asarray(b, float) / np.linalg.norm(b)
    v = np.cross(a, b); s = np.linalg.norm(v); c = a @ b
    if s < 1e-9: return np.eye(4) if c > 0 else np.diag([1.0, -1, -1, 1])
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]]) / s
    R = np.eye(3) + s * K + (1 - c) * K @ K; M = np.eye(4); M[:3, :3] = R; return M
def side_of(name):
    n = os.path.basename(name).lower()
    if 'rightversion' in n: return 'R'
    if n.startswith('larm') or '_larm' in n or 'larm' in n.split('__')[-1][:5]: return 'L'
    return 'R'
def shoulder_disc(V, F, side):
    want = np.array([1.0, 0, 0]) * (1 if side == 'R' else -1)
    best = None
    for d in all_flats(V, F, min_area=5):
        if not (1.5 < d['r'] < 3.2 and d['rms'] < 1.0 and 6 < d['A'] < 30): continue
        s = d['n'] @ want
        if s < 0.3: continue
        key = s * min(d['A'], 20)
        if best is None or key > best[0]: best = (key, d)
    return best[1] if best else None
def arm_world(d, side):
    """file -> torso (Mar Fil 23-Torso-2 frame)"""
    want = np.array([1.0, 0, 0]) * (1 if side == 'R' else -1)
    R1 = rot_between(d['n'], want)
    A = T(d['cc']) @ R1 @ T(-d['cc'])            # disc square to the side, spin kept
    if side == 'R':
        return S_H @ RZm90 @ T(-d['cc']) @ A
    return MX @ S_H @ RZm90 @ MX @ T(-d['cc']) @ A
def cup_of(V, F, disc_c=None):
    """the wrist cup: concave ball r 1.0-1.8 far from the shoulder. -> dict(c, r, out (opening dir), sup) or None"""
    best = None
    for votes, r, c, sup in spheres(V, F, np.arange(0.9, 1.8, 0.1), top=4, convex=False):
        c2, r2, n2 = refine_sphere(V, c, r)
        if not (0.9 < r2 < 1.9): continue
        far = np.linalg.norm(c2 - disc_c) if disc_c is not None else 10
        if far < 6: continue
        key = votes * (1 + 0.02 * far)
        if best is None or key > best[0]: best = (key, dict(c=c2, r=r2, votes=votes, far=far))
    if best is None: return None
    d = best[1]
    N = vnormals(V, F); dv = np.linalg.norm(V - d['c'], axis=1)
    m = (np.abs(dv - d['r']) < 0.12) & (np.einsum('ij,ij->i', N, (V - d['c']) / np.maximum(dv, 1e-9)[:, None]) < -0.8)
    inward = (V[m] - d['c']).mean(0)
    d['out'] = -inward / np.linalg.norm(inward); d['nsup'] = int(m.sum())
    # how closed is the cup: support spread
    return d
def ball_of(V, F, rmin=0.8, rmax=1.7, near=None):
    """a convex ball (wrist / neck): best sphere; axis a = from the ball centre away from the free side"""
    best = None
    for votes, r, c, sup in spheres(V, F, np.arange(rmin, rmax, 0.1), top=3):
        c2, r2, n2 = refine_sphere(V, c, r)
        if not (rmin - 0.1 < r2 < rmax + 0.1): continue
        key = votes if near is None else votes / (1 + np.linalg.norm(c2 - near))
        if best is None or key > best[0]: best = (key, dict(c=c2, r=r2, votes=votes))
    if best is None: return None
    d = best[1]
    N = vnormals(V, F); dv = np.linalg.norm(V - d['c'], axis=1)
    m = (np.abs(dv - d['r']) < 0.1) & (np.einsum('ij,ij->i', N, (V - d['c']) / np.maximum(dv, 1e-9)[:, None]) > 0.85)
    free = (V[m] - d['c']).mean(0)
    d['free'] = free / np.linalg.norm(free); d['nsup'] = int(m.sum())
    # body direction: from the ball to the rest of the part
    body = V.mean(0) - d['c']; d['body'] = body / np.linalg.norm(body)
    return d
Z_SOCK = np.array([0, 1.0, 0.3]) / np.linalg.norm([0, 1.0, 0.3])     # forward, a little up: a hanging forearm holds its weapon forward, a raised one up
def frame_YZ(o, Y, Zhint):
    Y = Y / np.linalg.norm(Y); Z = Zhint - (Zhint @ Y) * Y; Z /= np.linalg.norm(Z); X = np.cross(Y, Z)
    M = np.eye(4); M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = X, Y, Z, o; return M
def hand_socket(cup, W):
    """Hand socket in the arm's file coords (Springles convention: origin where the hand's origin goes,
    Y into the arm, Z = torso up+forward)."""
    Yin = -cup['out']
    o = cup['c'] + 0.55 * Yin
    Zf = W[:3, :3].T @ Z_SOCK
    return frame_YZ(o, Yin, Zf)

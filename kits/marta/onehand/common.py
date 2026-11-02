"""Marta one-handed parts: shared helpers (loader, shoulder face, the Mar Fil shoulder convention Q)."""
import sys, json, struct, os, numpy as np
sys.path[:0] = ['/home/claude/kits', '/home/claude/kits/cr', '/home/claude/kits/cr/dev']
import flats
from topface import merge_flats
from flatface import frame
LIB = '/mnt/user-data/uploads/d/Kitbash Library/'
NC = '/mnt/user-data/uploads/d/new cults/'
SCALE = 0.9                       # Marta arms (Josh, 30 Oct); hand-held parts stay 1.0
def load(f):
    d = open(f, 'rb').read(); n = struct.unpack('<I', d[80:84])[0]
    a = np.frombuffer(d[84:84 + n * 50], dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]))
    P = a['v'].reshape(-1, 3).astype(float); V, inv = np.unique(P.round(5), axis=0, return_inverse=True)
    return V, inv.reshape(-1, 3)
def M16(a): return np.array(a, float).reshape(4, 4)
def faces(V, T, min_area=2.0):
    M = merge_flats([(a, n, c) for a, n, c, o, s in flats.flats(V, T, min_area=min_area)]); M.sort(key=lambda m: -m[0]); return M
# Q: Mar Fil AM torso (22-Torso-1 = MarFil Assault - Torso 1): face frame -> socket, per shoulder (same origin, rotation only)
_AMT = LIB + 'Mar Fil - Tacticus/AssaultMarines-V2/Chests/MarFil Assault - Torso 1'
def _q():
    S = {s['type']: M16(s['matrix']) for s in json.load(open(_AMT + '.sockets.json'))['sockets']}
    V, T = load(_AMT + '.stl'); F = flats.flats(V, T, min_area=3.0); Q = {}
    for side, sx in (('R', 1), ('L', -1)):
        f = max([f for f in F if f[1][0] * sx > 0.95], key=lambda f: f[0])
        Q['Shoulder ' + side] = np.linalg.inv(frame(S['Shoulder ' + side][:3, 3], f[1], [0, 0, 1.0])) @ S['Shoulder ' + side]
    return Q, S
Q, S_AM = _q()
def roundness(V, T, sel, c, n):
    P = V[T[sel].ravel()] - c; P = P - np.outer(P @ n, n); r = np.linalg.norm(P, axis=1).max()
    return r
def shoulder_face(V, T):
    """The arm's shoulder face: the biggest flat face (merged patches, 8-45 mm2) whose normal is within 11 deg of +-X
    (Marta: right arms' face points +X). Bigger flats are a gun's or shield's side."""
    c = [m for m in faces(V, T) if abs(m[1][0]) > 0.98 and 8 < m[0] < 45]
    return c[0] if c else None
def arm_fit(V, T, scale=SCALE):
    f = shoulder_face(V, T)
    if f is None: return None
    a, n, c = f; side = 'R' if n[0] > 0 else 'L'
    F = np.linalg.inv(Q['Shoulder ' + side]) @ np.linalg.inv(frame(c * scale, -n, [0, 1.0, 0]))
    return side, F, f
def wrist_socket(V, T, side, joint, F, scale=SCALE):
    """Hand R/L socket in scaled file coords: TIOW's wrist face (origin, Y into the forearm), roll = the torso's
    up+forward laid across the wrist (as Springles), since TIOW's armour roll is tuned on Mar Fil forearms."""
    import tiow_inbox as TI
    Vs = V * scale; j = joint * scale
    M = None
    for tol in (0.12, 0.2, 0.3):
        M = TI.arm_wrist_frame(Vs, T, j, side, round_tol=tol)
        if M is not None: break
    if M is None: return None, None
    R = (S_AM['Shoulder ' + side] @ F)[:3, :3]          # arm file -> torso frame (Z up, Y front)
    d = R.T @ np.array([0, 1.0, 1.0]) / np.sqrt(2)     # torso up+forward in arm file coords
    Y = M[:3, 1]; Z = d - (d @ Y) * Y; Z /= np.linalg.norm(Z); X = np.cross(Y, Z)
    N = np.eye(4); N[:3, 0], N[:3, 1], N[:3, 2], N[:3, 3] = X, Y, Z, M[:3, 3]
    ang = np.degrees(np.arctan2(np.cross(M[:3, 2], Z) @ Y, M[:3, 2] @ Z))
    return N, dict(tol=tol, armour_vs_rule_deg=float(ang))

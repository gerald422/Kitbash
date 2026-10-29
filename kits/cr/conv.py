"""Shared joint conventions for flat-joint creators, derived from Mar Fil's AM torso (22-Torso-1) so every kit fits every kit.
Face frames: frame(origin, z, y-hint).  Torso sockets for a flat-joint torso = its face frame @ Q, Q = inv(AM face frame) @ AM socket."""
import sys; sys.path.insert(0,'/home/claude/kits'); sys.path.insert(0,'/home/claude/kits/cr')
import numpy as np, json, geo, flats
from flatface import frame
P = json.load(open('/home/claude/kits/amv2_partial.json'))['side']
AMT = 'AssaultMarines-V2/AssaultMarines-V2/RawSTL/Chest/22-Torso-1.stl'
def M16(s): return np.array([v for k, v in s.items() if 'mat' in k][0], float).reshape(4, 4)
S_AM = {s['type']: M16(s) for s in P[AMT]['sockets']}
UP, FRONT = np.array([0, 0, 1.0]), np.array([0, 1.0, 0])
BELT_TOP = 24.8                     # Mar Fil legs: top of the belt at the front, torso coordinates (AM legs 24.0-25.3)
KB = frame([0, S_AM['Waist'][1, 3], BELT_TOP], UP, FRONT)   # where a flat-bottomed torso's bottom sits on Mar Fil legs
def _am_faces():
    V, T = geo.load(AMT); V = np.asarray(V, float)
    F = flats.flats(V, T, min_area=3.0)
    out = {}
    for side, sx in (('R', 1), ('L', -1)):
        f = max([f for f in F if f[1][0] * sx > 0.95], key=lambda f: f[0])
        o = S_AM['Shoulder ' + side][:3, 3]
        out['Shoulder ' + side] = frame(o, f[1], UP)
    # neck: where the socket's Z line meets the torso's top surface; floor normal of the terraces there
    S = geo.surf(V, T, 400000); s = S_AM['Neck']; o, z = s[:3, 3], s[:3, 2]
    d = S - o; t = d @ z; r = np.linalg.norm(d - t[:, None] * z, axis=1)
    k = r < 0.3; hit = o + z * np.max(t[k])
    fn = max([f for f in F if f[1][2] > 0.9 and np.linalg.norm(f[2][:2] - hit[:2]) < 3.5], key=lambda f: f[0])[1]
    out['Neck'] = frame(hit, fn, FRONT)
    fb = max([f for f in F if f[1][1] < -0.95 and f[2][2] > 32], key=lambda f: f[0])
    out['Back'] = frame(fb[2], fb[1], UP)
    return out
AM_FACE = _am_faces()
Q = {j: np.linalg.inv(AM_FACE[j]) @ S_AM[j] for j in AM_FACE}
def shoulder_frame(SR, SL):
    """Frame between the two shoulder joints: origin midway, X towards the right one, Z up (both sockets' Z), Y front."""
    o = 0.5 * (SR[:3, 3] + SL[:3, 3]); x = SR[:3, 3] - SL[:3, 3]; up = SR[:3, 2] + SL[:3, 2]
    z = up - (up @ x) / (x @ x) * x
    return frame(o, z, np.cross(z, x))
# Neck (Josh, 20 Oct: "similar position to the Mar Fil reference"): the head keeps exactly where it sits relative to
# the shoulder joints on the Mar Fil torso - height (0.79 above), front-back, tilt - whatever the mark's collar.
NECK_IN_SH = np.linalg.inv(shoulder_frame(S_AM['Shoulder R'], S_AM['Shoulder L'])) @ S_AM['Neck']
def torso_sockets(face):
    """face: dict joint -> face frame of a flat-joint torso (in its own file coords), incl. 'Bottom' (z up into the torso, y front)."""
    out = {j: face[j] @ Q[j] for j in Q if j in face}
    if 'Shoulder R' in out and 'Shoulder L' in out:
        out['Neck'] = shoulder_frame(out['Shoulder R'], out['Shoulder L']) @ NECK_IN_SH
    out['Flat Waist'] = face['Bottom']
    out['Waist'] = face['Bottom'] @ np.linalg.inv(KB) @ S_AM['Waist']
    return out
if __name__ == '__main__':
    for j, M in AM_FACE.items(): print(j, 'face o', M[:3, 3].round(3), 'z', M[:3, 2].round(3), '| Q t', Q[j][:3, 3].round(3), 'rot %.1f' % geo.ang(Q[j][:3, :3]))

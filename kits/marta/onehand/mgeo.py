"""Marta one-handed rules, plain numpy/scipy (runs on the PC): shoulder face, arm fit at 90%, wrist socket.
The Mar Fil shoulder convention Q comes from MarFil Assault - Torso 1 (conv_marfil.json, made by common.py)."""
import os, json, struct, collections, numpy as np
import tiow_geom as G
HERE = os.path.dirname(os.path.abspath(__file__))
_C = json.load(open(os.path.join(HERE, 'conv_marfil.json')))
Q = {k: np.array(v).reshape(4, 4) for k, v in _C['Q'].items()}; S_AM = {k: np.array(v).reshape(4, 4) for k, v in _C['S_AM'].items()}
SCALE = 0.9
def load(f, maxtris=600000, grid=0.06):
    """V, T of a binary STL. Meshes over maxtris (Marta's 1.5-1.9M-triangle sculpts) are thinned for the analysis only:
    vertices merged on a `grid` mm lattice, degenerate triangles dropped (flat faces stay flat to ~grid/2)."""
    d = open(f, 'rb').read(); n = struct.unpack('<I', d[80:84])[0]
    a = np.frombuffer(d[84:84 + n * 50], dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]))
    P = a['v'].reshape(-1, 3); del d, a
    if n > maxtris:
        key = np.floor(P / grid).astype(np.int32); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
        cnt = np.bincount(inv); V = np.zeros((len(cnt), 3)); np.add.at(V, inv, P.astype(float)); V /= cnt[:, None]
        T = inv.reshape(-1, 3); T = T[(T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 0] != T[:, 2])]
        return V, T
    V, inv = np.unique(P.astype(float).round(5), axis=0, return_inverse=True)
    return V, inv.reshape(-1, 3)
def tri_info(V, T):
    A, B, C = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]; n = np.cross(B - A, C - A); a = np.linalg.norm(n, axis=1)
    return (A + B + C) / 3, n / np.maximum(a[:, None], 1e-12), a / 2
def flats(V, T, min_area=3.0, tol=0.02):
    cen, n, a = tri_info(V, T); key = np.round(n / tol).astype(int); g = collections.defaultdict(list); out = []
    for i, k in enumerate(map(tuple, key)): g[k].append(i)
    for k, idx in g.items():
        idx = np.array(idx)
        if a[idx].sum() < min_area: continue
        nn = (n[idx] * a[idx, None]).sum(0); nn /= np.linalg.norm(nn); off = cen[idx] @ nn
        for o in np.unique(np.round(off / 0.05)):
            sel = idx[np.abs(off / 0.05 - o) < 0.6]; A = a[sel].sum()
            if A >= min_area: out.append((A, nn, (cen[sel] * a[sel, None]).sum(0) / A))
    return out
def merge_flats(FL, ang_deg=3.0, dz=0.12, reach=8.0):
    FL = sorted(FL, key=lambda f: -f[0]); used = [False] * len(FL); out = []; ca = np.cos(np.radians(ang_deg))
    for i, (A, n, c) in enumerate(FL):
        if used[i]: continue
        used[i] = True; grp = [(A, n, c)]
        for j in range(i + 1, len(FL)):
            if used[j]: continue
            Aj, nj, cj = FL[j]
            if nj @ n > ca and abs((cj - c) @ n) < dz and np.linalg.norm(cj - c) < reach: used[j] = True; grp.append((Aj, nj, cj))
        At = sum(g[0] for g in grp); nn = sum(g[0] * g[1] for g in grp); nn = nn / np.linalg.norm(nn)
        out.append((At, nn, sum(g[0] * g[2] for g in grp) / At))
    out.sort(key=lambda m: -m[0]); return out
def frame(o, z, yhint):
    z = np.asarray(z, float); z = z / np.linalg.norm(z); y = np.asarray(yhint, float); y = y - (y @ z) * z; y /= np.linalg.norm(y)
    x = np.cross(y, z); M = np.eye(4); M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = x, y, z, o; return M
def compact(V, T, n, c, info):
    """share of the disc (radius = farthest point of the face from its centre) that the flat face fills"""
    cen, nn, a = info
    k = (nn @ n > 0.995) & (np.abs((cen - c) @ n) < 0.06) & (np.linalg.norm(cen - c, axis=1) < 6.0)
    if not k.any(): return 0.0
    P = V[T[k].ravel()] - c; P = P - np.outer(P @ n, n); r = np.linalg.norm(P, axis=1).max()
    return a[k].sum() / (np.pi * r * r)
def shoulder_faces(V, T):
    """Flat faces (8-45 mm2) whose normal is within 11 deg of +-X and that fill at least 17% of their disc, roundest first
    (Marta: a right arm's face points +X, the model's right is -X). Shoulder faces fill 19-86% (bionic ones least, round
    their tubes); the flat sides of a shield or gun built onto an arm 7-16%."""
    info = tri_info(V, T); out = []
    for a, n, c in merge_flats(flats(V, T)):
        if abs(n[0]) > 0.98 and 8 < a < 45:
            k = compact(V, T, n, c, info)
            if k >= 0.17: out.append((a, n, c, k))
    out.sort(key=lambda f: -f[3]); return [f[:3] for f in out]
def shield_pad(V, T):
    """The round pad on a strapped shield's back where the handle's 9.5 mm plate goes: a flat 55-85 mm2 face along +-Z
    filling 60%+ of its disc. None if there's none (a shield with its hand and handle built in)."""
    info = tri_info(V, T)
    for a, n, c in merge_flats(flats(V, T)):
        if abs(n[2]) > 0.95 and 55 < a < 85 and compact(V, T, n, c, info) >= 0.6: return a, n, c
    return None
def arm_fit(face, scale=SCALE):
    a, n, c = face; side = 'R' if n[0] > 0 else 'L'
    return side, np.linalg.inv(Q['Shoulder ' + side]) @ np.linalg.inv(frame(c * scale, -n, [0, 1.0, 0]))
def wrist_socket(V, T, side, joint, F, scale=SCALE):
    """Hand R/L socket (scaled file coords): TIOW's wrist face (origin, Y into the forearm), roll = the torso's up+forward
    laid across the wrist (as Springles); TIOW's armour roll is tuned on Mar Fil forearms and scatters +-120 deg on Marta's."""
    Vs = V * scale; j = joint * scale; M = None
    for tol in (0.12, 0.2, 0.3):
        M = G.arm_wrist_frame(Vs, T, j, side, round_tol=tol)
        if M is not None: break
    if M is None: return None, None
    R = (S_AM['Shoulder ' + side] @ F)[:3, :3]; d = R.T @ np.array([0, 1.0, 1.0]) / np.sqrt(2)
    Y = M[:3, 1]; Z = d - (d @ Y) * Y; Z /= np.linalg.norm(Z)
    N = np.eye(4); N[:3, 0], N[:3, 1], N[:3, 2], N[:3, 3] = np.cross(Y, Z), Y, Z, M[:3, 3]
    return N, tol

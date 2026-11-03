import sys, json, struct, numpy as np, pickle
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
LD = '/mnt/user-data/uploads/d/Kitbash Library/Mar Fil - Tacticus/AssaultMarines-V2/Legs(JumpPack)/Legs/MarFil Assault - Legs %s'
TOR = json.load(open('/mnt/user-data/uploads/d/Kitbash Library/Mar Fil - Tacticus/AssaultMarines-V2/Chests/MarFil Assault - Torso 1.sockets.json'))
M16 = lambda a: np.array(a, float).reshape(4, 4)
S_WAIST = M16([s['matrix'] for s in TOR['sockets'] if s['type'] == 'Waist'][0])
def load(f):
    d = open(f, 'rb').read(); n = struct.unpack('<I', d[80:84])[0]
    v = np.ascontiguousarray(np.frombuffer(d[84:84 + n * 50], dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]))['v'].reshape(-1, 3))
    _, first, inv = np.unique(v.view(np.dtype((np.void, 12))).ravel(), return_index=True, return_inverse=True)
    return v[first].astype(float), inv.reshape(-1, 3)
def samples(V, T, n=400000, seed=0):
    A = V[T]; a = np.linalg.norm(np.cross(A[:, 1] - A[:, 0], A[:, 2] - A[:, 0]), axis=1); rng = np.random.default_rng(seed)
    i = rng.choice(len(T), n, p=a / a.sum()); u, w = rng.random(n), rng.random(n); f = u + w > 1; u[f], w[f] = 1 - u[f], 1 - w[f]
    return A[i, 0] + (A[i, 1] - A[i, 0]) * u[:, None] + (A[i, 2] - A[i, 0]) * w[:, None]
def frame(o, z, y):
    z = z / np.linalg.norm(z); y = y - (y @ z) * z; y /= np.linalg.norm(y); F = np.eye(4); F[:3, 0], F[:3, 1], F[:3, 2], F[:3, 3] = np.cross(y, z), y, z, o; return F
out = {}
for n in range(1, 9):
    a, b = '%dA' % n, '%dB' % n
    VA, TA = load(LD % a + '.stl'); VB, TB = load(LD % b + '.stl'); sc = json.load(open(LD % a + '.sockets.json'))
    M = S_WAIST @ M16(sc['fits']['Waist'])                          # legs file -> torso coords (+X model right, +Y front, Z up)
    hips = {s['type']: M16(s['matrix']) for s in sc['sockets'] if s['type'] in ('Hip R', 'Hip L')}
    SA = samples(VA, TA); tA = cKDTree(SA)
    cB = VB[TB].mean(1); far = tA.query(cB)[0] > 0.12; idx = np.where(far)[0]; Tf = TB[idx]
    G = coo_matrix((np.ones(Tf.size), (np.repeat(np.arange(len(idx)), 3), Tf.ravel() + len(idx))), shape=(len(idx) + len(VB),) * 2)
    lab = connected_components(G, directed=False)[1][:len(idx)]
    up_legs = np.linalg.inv(M)[:3, :3] @ np.array([0, 0, 1.0]); found = {}
    for k in np.unique(lab):
        sel = idx[lab == k]; P = VB[TB[sel]].reshape(-1, 3)
        area = np.linalg.norm(np.cross(VB[TB[sel, 1]] - VB[TB[sel, 0]], VB[TB[sel, 2]] - VB[TB[sel, 0]]), axis=1).sum() / 2
        Pt = P @ M[:3, :3].T + M[:3, 3]; cx = Pt.mean(0)
        if not (35 < area < 120) or abs(cx[0]) < 3.5: continue           # plates: mid-size, at the side of the waist
        side = 'R' if cx[0] > 0 else 'L'
        c = P.mean(0); _, _, E = np.linalg.svd(P - c, full_matrices=False); nrm = E[2]
        outw = (np.linalg.inv(M)[:3, :3] @ np.array([np.sign(cx[0]), 0, 0]))
        if nrm @ outw < 0: nrm = -nrm
        seam = P[tA.query(P)[0] < 0.3]; o = seam.mean(0) if len(seam) > 20 else c
        F = frame(o, nrm, up_legs)
        if side in found and found[side][1] > area: continue
        found[side] = (F, area, sel, np.linalg.inv(hips['Hip ' + side]) @ F)
    out[a] = {s: dict(F=v[0], area=v[1], sel=v[2], rel=v[3]) for s, v in found.items()}
    print('%s: plates found %s' % (a, ', '.join('%s %.0f mm2' % (s, v[1]) for s, v in sorted(found.items()))))
pickle.dump(out, open('plates.pkl', 'wb'))
for side in 'RL':
    rels = [(k, v[side]['rel']) for k, v in out.items() if side in v]
    T = np.array([r[:3, 3] for _, r in rels]); Z = np.array([r[:3, 2] for _, r in rels]); Y = np.array([r[:3, 1] for _, r in rels])
    zm = Z.mean(0); zm /= np.linalg.norm(zm); ym = Y.mean(0); ym /= np.linalg.norm(ym)
    print('Plate %s vs Hip %s anchor over %d legs: offset mean %s mm, spread (sd) %s mm; normal within %.1f deg (max), up within %.1f deg (max)' % (
        side, side, len(rels), T.mean(0).round(2), T.std(0).round(2), np.degrees(np.arccos(np.clip(Z @ zm, -1, 1))).max(), np.degrees(np.arccos(np.clip(Y @ ym, -1, 1))).max()))

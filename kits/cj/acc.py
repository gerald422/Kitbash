"""Chaplain belt bits: exported on the belt in torso coordinates. Each gets a belt-anchor frame K (origin where it
touches the belt, Z out of the belt, Y up - the frame a clicked belt/hip anchor has), fit = inv(K) for every belt
anchor; the Chaplain legs get anchors at Mar Fil's spots (P_X @ K in each legs file)."""
import sys; sys.path.insert(0, '/home/claude/kits')
import geo, json, numpy as np, os
from scipy.spatial import cKDTree
inv = np.linalg.inv
O = "ChaplainWithJumpPack (1)/ChaplainWithJumpPack/"
PO = json.load(open('/home/claude/kits/cj/pose.json'))
def surf_n(V, T, n, seed=0):
    V = np.asarray(V, float); A = V[T]; cr = np.cross(A[:, 1] - A[:, 0], A[:, 2] - A[:, 0]); ar = np.linalg.norm(cr, axis=1)
    rng = np.random.default_rng(seed); i = rng.choice(len(T), n, p=ar / ar.sum()); u, v = rng.random(n), rng.random(n); f = u + v > 1; u[f], v[f] = 1 - u[f], 1 - v[f]
    P = A[i, 0] + u[:, None] * (A[i, 1] - A[i, 0]) + v[:, None] * (A[i, 2] - A[i, 0])
    return P, cr[i] / ar[i, None]
LEGS = {}
for X, p in PO.items():
    V, T = geo.load(p['legs']); P, N = surf_n(V, T, 300000); M = np.array(p['M_marfil'])
    LEGS[X] = (P @ M[:3, :3].T + M[:3, 3], N @ M[:3, :3].T)
ACC = {'23-Book': 'Belt Back', '24-Badge': 'Belt Front', '25-Holster': 'Hip L', '26-Grenade': 'Belt Back'}
out = {'K': {}, 'anchors': {X: {} for X in PO}}
for a, anchor in ACC.items():
    V, T = geo.load(O + 'Accesories/Accesories-Raw-STL/' + a + '.stl'); Q = geo.surf(V, T, 40000); cq = Q.mean(0)
    pts, nrm = [], []
    for X, (P, N) in LEGS.items():
        tr = cKDTree(P); d, i = tr.query(Q); k = d < np.percentile(d, 3) + 0.15
        pts.append(Q[k]); n = N[i[k]]; n *= np.sign((cq - P[i[k]]) @ n.T).reshape(-1, 1) if False else 1
        # legs normals point out of the legs surface already (outward winding); keep the ones facing the bit
        n = n[((cq - P[i[k]]) * n).sum(1) > 0]; nrm.append(n)
    c = np.concatenate(pts).mean(0); z = np.concatenate(nrm).mean(0)
    y = np.array([0, 0, 1.0]); z = z - y * (z @ y); z /= np.linalg.norm(z); x = np.cross(y, z)
    K = np.eye(4); K[:3, 0], K[:3, 1], K[:3, 2], K[:3, 3] = x, y, z, c
    out['K'][a] = K.tolist()
    print('%-11s contact %s  out %s  -> %s' % (a, np.round(c, 2), np.round(z, 2), anchor))
    if anchor:
        for X, p in PO.items(): out['anchors'][X][a] = [anchor, (np.array(p['P']) @ K).tolist()]
json.dump(out, open('/home/claude/kits/cj/acc.json', 'w'), indent=1)

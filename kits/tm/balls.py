import sys; sys.path.insert(0, '/home/claude/kits')
import geo, json, numpy as np, os, glob
from scipy.spatial import cKDTree
O = "Techmarine (2)/Techmarine/"
def surf_n(V, T, n, seed=0):
    V = np.asarray(V, float); A = V[T]; cr = np.cross(A[:, 1] - A[:, 0], A[:, 2] - A[:, 0]); ar = np.linalg.norm(cr, axis=1); ok = ar > 0; A, cr, ar = A[ok], cr[ok], ar[ok]
    rng = np.random.default_rng(seed); i = rng.choice(len(A), n, p=ar / ar.sum()); u, v = rng.random(n), rng.random(n); f = u + v > 1; u[f], v[f] = 1 - u[f], 1 - v[f]
    return A[i, 0] + u[:, None] * (A[i, 1] - A[i, 0]) + v[:, None] * (A[i, 2] - A[i, 0]), cr[i] / ar[i, None]
def sphere_fit(P):
    A = np.c_[2 * P, np.ones(len(P))]; b = (P ** 2).sum(1); x = np.linalg.lstsq(A, b, rcond=None)[0]; c = x[:3]; r = np.sqrt(x[3] + c @ c)
    return c, r, np.abs(np.linalg.norm(P - c, axis=1) - r)
def vote(P, N, r, sign=+1, cell=0.15):
    C = P - sign * r * N                     # convex ball: centre is inside along -normal
    q = np.round(C / cell).astype(int); u, inv_, cnt = np.unique(q, axis=0, return_inverse=True, return_counts=True)
    best = np.argsort(-cnt)[:5]; out = []
    for b in best:
        m = inv_ == b; c0 = C[m].mean(0)
        k = np.abs(np.linalg.norm(P - c0, axis=1) - r) < 0.08
        if k.sum() > 30: c, rr, res = sphere_fit(P[k]); out.append((int(k.sum()), c, rr, float(np.median(res))))
    return sorted(out, key=lambda x: -x[0])
BP, BN = surf_n(*geo.load(O + 'Backpack/Backpack-Raw-STL/11-Techmarine-Backpack.stl'), 400000); tb = cKDTree(BP)
res = {}
for f in sorted(glob.glob(geo.U + O + 'MechanicArms/MechanicArm-Raw-STL/*.stl')):
    P, N = surf_n(*geo.load(f[len(geo.U):]), 300000)
    # the ball: sphere votes for radii 2.0-4.0
    best = None
    for r in np.arange(2.0, 4.01, 0.1):
        v = vote(P, N, r)
        if v and (best is None or v[0][0] > best[0]): best = (v[0][0], v[0][1], v[0][2], v[0][3], r)
    n, c, rr, md, r0 = best
    d, _ = tb.query(c[None]); 
    res[os.path.basename(f)] = {'c': c.tolist(), 'r': rr}
    print('%-22s ball r %.2f (votes %d, fit %.3f) centre %s' % (os.path.basename(f), rr, n, md, np.round(c, 2)), flush=True)
# the cup on the backpack: concave sphere (centre outside along +normal)
best = None
for r in np.arange(2.0, 4.01, 0.1):
    v = vote(BP, BN, r, sign=-1)
    if v and (best is None or v[0][0] > best[0]): best = (v[0][0], v[0][1], v[0][2], v[0][3], r)
print('backpack cup r %.2f (votes %d, fit %.3f) centre %s' % (best[2], best[0], best[3], np.round(best[1], 2)))
best2 = None
for r in np.arange(2.0, 4.01, 0.1):
    v = vote(BP, BN, r, sign=+1)
    if v and (best2 is None or v[0][0] > best2[0]): best2 = (v[0][0], v[0][1], v[0][2], v[0][3], r)
print('backpack ball r %.2f (votes %d, fit %.3f) centre %s' % (best2[2], best2[0], best2[3], np.round(best2[1], 2)))
res['cup'] = {'c': best[1].tolist(), 'r': best[2]}; res['pack_ball'] = {'c': best2[1].tolist(), 'r': best2[2]}
json.dump(res, open('/home/claude/kits/tm/balls.json', 'w'), indent=1)

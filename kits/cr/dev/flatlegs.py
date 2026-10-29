"""Device-side: flat-topped legs -> Flat Waist fit, belt anchors, Base socket. usage: flatlegs.py jobs.json out.json
jobs: [[path, [front x,y,z]], ...]  (file Y is up for these creators)"""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.expanduser('~/ctools'))
from stllib import stl, flats
from topface import top_face
def frame(o, z, y):
    z = np.asarray(z, float); z /= np.linalg.norm(z); y = np.asarray(y, float); y = y - (y @ z) * z; y /= np.linalg.norm(y)
    M = np.eye(4); M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = np.cross(y, z), y, z, o; return M
def surf(F, n, seed=0):
    e1 = F[:, 1] - F[:, 0]; e2 = F[:, 2] - F[:, 0]; cr = np.cross(e1, e2); ar = np.linalg.norm(cr, axis=1); ok = ar > 0
    F, cr, ar = F[ok], cr[ok], ar[ok]
    rng = np.random.default_rng(seed); i = rng.choice(len(F), n, p=ar / ar.sum()); u, v = rng.random(n), rng.random(n); f = u + v > 1; u[f], v[f] = 1 - u[f], 1 - v[f]
    return F[i, 0] + u[:, None] * (F[i, 1] - F[i, 0]) + v[:, None] * (F[i, 2] - F[i, 0]), cr[i] / ar[i, None]
DIRS = {'Hip R': (1, 0, 0), 'Hip L': (-1, 0, 0), 'Belt Front': (0, 1, 0), 'Belt Back': (0, -1, 0)}
def legs(path, front, belt_depth=1.0):
    F = stl(path)
    A, nn, c = top_face(flats(F, min_area=1.0), ytop=float(F[:, :, 1].max()))
    L = frame(c, nn, front)
    P, N = surf(F, 300000)
    Q = (P - c) @ L[:3, :3]; NQ = N @ L[:3, :3]                       # in the top-face frame
    axis = np.array([0, 0, -belt_depth]); out = {}
    for name, d in DIRS.items():
        d = np.array(d, float); D = Q - axis; t = D @ d; lat = np.linalg.norm(D - t[:, None] * d, axis=1)
        k = (t > 0) & (lat < 0.35)
        if k.sum() < 3: continue
        hit = Q[k][np.argmax(t[k])]
        near = (np.linalg.norm(Q - hit, axis=1) < 0.6) & (NQ @ d > 0)
        z = NQ[near].mean(0) if near.any() else d
        y = np.array([0, 0, 1.0]); z = z - y * (z @ y); z /= np.linalg.norm(z)
        K = np.eye(4); K[:3, 0], K[:3, 1], K[:3, 2], K[:3, 3] = np.cross(y, z), y, z, hit
        out[name] = (L @ K).tolist()
    V = F.reshape(-1, 3); ymin = V[:, 1].min(); foot = V[V[:, 1] < ymin + 0.6]
    base = frame([foot[:, 0].mean(), ymin, foot[:, 2].mean()], [0, 1, 0], front)
    return dict(area=round(float(A), 2), tilt=round(float(np.degrees(np.arccos(min(1, nn[1])))), 1), top=L.tolist(), fit=np.linalg.inv(L).tolist(), belt=out, base=base.tolist())
if __name__ == '__main__':
    jobs = json.load(open(sys.argv[1])); res = {}
    if os.path.exists(sys.argv[2]): res = json.load(open(sys.argv[2]))
    for p, front in jobs:
        if p in res: continue
        try: res[p] = legs(p, front)
        except Exception as e: res[p] = dict(err=repr(e))
        json.dump(res, open(sys.argv[2], 'w'))
    print(len(res), sum('err' in v for v in res.values()))

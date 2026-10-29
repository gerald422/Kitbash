import sys, os, json, numpy as np
sys.path.insert(0, os.path.expanduser('~/ctools'))
from poses import stl, flats
def top(F):
    e1 = F[:, 1] - F[:, 0]; e2 = F[:, 2] - F[:, 0]; c = np.cross(e1, e2); a = np.linalg.norm(c, axis=1) / 2
    FL = flats(F, min_area=4.0)
    up = [f for f in FL if f[1][1] > 0.7]
    up.sort(key=lambda f: -(f[2][1]) - 0.01 * f[0])
    t = up[0]
    # feet: lowest 1.5 mm of the mesh
    V = F.reshape(-1, 3); ymin = V[:, 1].min(); foot = V[V[:, 1] < ymin + 1.5]
    return dict(area=round(t[0], 1), n=t[1].round(3).tolist(), c=t[2].round(2).tolist(), ymin=round(float(ymin), 2),
                foot_c=foot.mean(0).round(2).tolist(), bb=[V.min(0).round(1).tolist(), V.max(0).round(1).tolist()])
res = {}
for d in sys.argv[1:]:
    for f in sorted(os.listdir(d)):
        if f.lower().endswith('.stl'):
            p = os.path.join(d, f)
            try: res[p] = top(stl(p))
            except Exception as e: res[p] = dict(err=str(e))
json.dump(res, open(os.path.expanduser('~/legs_scan.json'), 'w'), indent=0)
print(len(res))

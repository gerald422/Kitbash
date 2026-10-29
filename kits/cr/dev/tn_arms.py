"""Device: Turtle Ninja arms -> Shoulder R/L fit (shoulder disc on the socket, as the Mar Fil arms). usage: tn_arms.py list.txt root out.json"""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.expanduser('~/ctools'))
from stllib import stl, flats
from topface import merge_flats
QI = {'R': np.array([[7.3e-05, -0.04237, 0.999102, 0.0], [1.0, 3e-06, -7.3e-05, -0.0], [-0.0, 0.999102, 0.04237, 0.0], [0.0, 0.0, 0.0, 1.0]]),
      'L': np.array([[0.000148, 0.042006, -0.999117, 0.0], [-1.0, 6e-06, -0.000148, -0.0], [0.0, 0.999117, 0.042006, -0.0], [0.0, 0.0, 0.0, 1.0]])}
def frame(o, z, y):
    z = np.asarray(z, float); z /= np.linalg.norm(z); y = np.asarray(y, float); y = y - (y @ z) * z; y /= np.linalg.norm(y)
    M = np.eye(4); M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = np.cross(y, z), y, z, o; return M
def name_side(p):
    import re
    w = set(re.split(r'[^a-z]+', re.sub(r'([a-z])([A-Z])', r'\1 \2', p).lower()))
    r, l = bool(w & {'r', 'right'}), bool(w & {'l', 'left'})
    return 'R' if r and not l else 'L' if l and not r else None
def arm(p):
    F = stl(p)
    cand = [f for f in merge_flats(flats(F, min_area=1.0)) if abs(f[1][0]) > 0.98 and f[0] > 6]
    if not cand: return dict(err='no shoulder disc')
    A, n, c = max(cand, key=lambda f: f[0])
    side = 'R' if n[0] < 0 else 'L'
    Af = frame(c, -n, [0, 1, 0])
    fit = QI[side] @ np.linalg.inv(Af)
    return dict(area=round(float(A), 2), n=n.round(4).tolist(), c=c.round(3).tolist(), side=side, name_side=name_side(os.path.basename(p)), fit=fit.tolist())
if __name__ == '__main__':
    L = [l for l in open(sys.argv[1]).read().split('\n') if l]; root = sys.argv[2]; res = {}
    for rel in L:
        try: res[rel] = arm(os.path.join(root, rel))
        except Exception as e: res[rel] = dict(err=repr(e))
    json.dump(res, open(sys.argv[3], 'w'))
    print(len(res), 'errors', sum('err' in v for v in res.values()))

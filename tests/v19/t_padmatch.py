"""Pad anchor matching on every AM-V2 arm / power fist (+ VS arms): the add-on's current match vs a full swing about the joint."""
import bpy, sys, json, time, os, glob
import numpy as np
import importlib.util
spec = importlib.util.spec_from_file_location('ti', '/home/claude/tiow_blender/tiow_inbox.py'); T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
from mathutils.bvhtree import BVHTree
RAW = '/home/claude/raw/'
P = json.load(open('/home/claude/kits/amv2_partial.json'))['side']
ref = T.builtin_refs('Pad')[0]
REG = np.array(ref['region'], float).reshape(-1, 3); PTS = np.array(ref['points'], float).reshape(3, 3)
PIV = np.array(ref['pivot'], float); RJ = np.array(ref['joint'], float)
MXv = np.array([-1.0, 1, 1])
def rand_rots(n, seed=2, maxdeg=120):
    rng = np.random.default_rng(seed); q = rng.normal(size=(n, 4)); q /= np.linalg.norm(q, axis=1)[:, None]
    w, x, y, z = q.T
    R = np.stack([1 - 2*(y*y + z*z), 2*(x*y - z*w), 2*(x*z + y*w), 2*(x*y + z*w), 1 - 2*(x*x + z*z), 2*(y*z - x*w), 2*(x*z - y*w), 2*(y*z + x*w), 1 - 2*(x*x + y*y)], 1).reshape(-1, 3, 3)
    ang = np.degrees(np.arccos(np.clip((np.trace(R, axis1=1, axis2=2) - 1) / 2, -1, 1)))
    return R[ang < maxdeg]
ROTS = rand_rots(4000)
def full_swing(region, rj, joint, tree, nrot=3000):
    near = T._nearest_with(tree, 1.0)
    rng = np.random.default_rng(1); tiny = region[rng.choice(len(region), 80, replace=False)]
    small = region[rng.choice(len(region), 250, replace=False)]
    mid = region[rng.choice(len(region), min(700, len(region)), replace=False)]
    sc = []
    for R in ROTS[:nrot]:
        t = joint - R @ rj; _q, d = near(tiny @ R.T + t); sc.append((float(np.median(d)), R, t))
    sc.sort(key=lambda x: x[0])
    st2 = []
    for _m, R, t in sc[:40]:
        R, t, d = T._icp_np(small, near, R, t, 6); st2.append((float(np.median(d)), R, t))
    st2.sort(key=lambda x: x[0]); best = None
    for _m, R, t in st2[:6]:
        R, t, d = T._icp_np(mid, near, R, t, 15)
        if best is None or np.median(d) < best[0]: best = (float(np.median(d)), R, t)
    R, t, d = T._icp_np(region, near, best[1], best[2], 30)
    return float(np.median(d)), R, t
ROTS = rand_rots(8000)
rels = sorted(r for r, d in P.items() if d.get('category') == 'Arms')
rels += [f[len(RAW):] for f in sorted(glob.glob(RAW + 'VeteranSquad/VeteranSquad/Arms/*/*.stl'))]
only = [a for a in sys.argv if a.startswith('--only=')]
if only: rels = [r for r in rels if any(k in r for k in only[0][7:].split(','))]
res = {}
for rel in rels:
    V, Tr = T.read_stl_np(RAW + rel)
    d = P.get(rel, {}); sh = [k for k in d.get('fits', {}) if k.startswith('Shoulder')]
    sd = sh[0][-1] if sh else ('L' if 'Mirrored' in rel else 'R')
    joint = np.linalg.inv(np.array(d['fits'][sh[0]]).reshape(4, 4))[:3, 3] if sh else np.array([5.484 * (1 if sd == 'R' else -1), 0.202, 31.949])
    reg, piv, rj = (REG * MXv, PIV * MXv, RJ * MXv) if sd == 'L' else (REG, PIV, RJ)
    tree = BVHTree.FromPolygons(V.tolist(), Tr.tolist())
    got, t1 = (None, 0.0) if '--nocur' in sys.argv else (lambda t0: (T.match_shoulder(reg, piv, V, Tr, tree, [(joint, rj)]), time.time() - t0))(time.time())
    t0 = time.time(); fm, R, t = full_swing(reg, rj, joint, tree); t2 = time.time() - t0
    res[rel] = dict(cur=got[0] if got else None, full=fm, R=R.tolist(), t=t.tolist(), side=sd)
    print('%-34s %s  current %.3f (%.1fs)   full swing %.3f (%.1fs)' % (os.path.basename(rel), sd, got[0] if got else -1, t1, fm, t2), flush=True)
json.dump(res, open('/home/claude/test/v19/padmatch2.json' if '--nocur' in sys.argv else '/home/claude/test/v19/padmatch.json', 'w'))
c = np.array([v['cur'] or 9 for v in res.values()]); f = np.array([v['full'] for v in res.values()])
print('current > 0.2:', int((c > 0.2).sum()), ' full > 0.2:', int((f > 0.2).sum()), ' full > 0.25:', int((f > 0.25).sum()))

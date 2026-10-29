import geo, json, numpy as np, glob, os, re, sys
from scipy.spatial import cKDTree
sys.path.insert(0,'/home/claude/real'); import fitlib as F
base = 'AssaultMarines-V2/AssaultMarines-V2/RawSTL/Arms/'
files = sorted(os.path.basename(f)[:-4] for f in glob.glob(geo.RAW + base + '*.stl'))
def parse(f):
    g = re.match(r'(\d+)-A[Rr]m-(\d+)-([RL])-([ABC])', f).groups(); return int(g[1]), g[2], g[3]
res = {}
for f in files:
    d, s, v = parse(f)
    if s != 'L': continue
    V, T = geo.load(base + f + '.stl'); S = geo.surf(V, T, 60000); tree = cKDTree(S)
    best = None
    for g in files:
        d2, s2, v2 = parse(g)
        if s2 != 'R' or d2 != d: continue
        W, U = geo.load(base + g + '.stl'); W = W * [-1, 1, 1]; U = U[:, ::-1]
        src = geo.surf(W, U, 3000)
        # start: centroid alignment, then ICP
        R, t, dd = geo.icp(src, tree, S, np.eye(3), S.mean(0) - src.mean(0), 60)
        med = np.median(dd)
        if best is None or med < best[0]: best = (med, g, R, t)
    med, g, R, t = best
    res[f] = dict(src=g, med=float(med), R=R.tolist(), t=t.tolist())
    print('%-16s = mirror(%-16s) med %.4f rot %.2f t %s' % (f, g, med, geo.ang(R), np.round(t, 3)))
json.dump(res, open('b_arms2.json', 'w'), indent=1)

import geo, json, numpy as np, glob, os, re
from scipy.spatial import cKDTree
base = 'AssaultMarines-V2/AssaultMarines-V2/RawSTL/Arms/'
files = sorted(os.path.basename(f)[:-4] for f in glob.glob(geo.RAW + base + '*.stl'))
info = {}
for f in files:
    m = re.match(r'(\d+)-ARm-(\d+)-([RL])-([ABC])|(\d+)-Arm-(\d+)-([RL])-([ABC])', f)
    g = [x for x in m.groups() if x is not None]
    info[f] = dict(num=int(g[0]), design=int(g[1]), side=g[2], var=g[3])
# is each L arm the X-mirror of some R arm of the same design?
for f, i in info.items():
    if i['side'] != 'L': continue
    V, T = geo.load(base + f + '.stl'); P = geo.surf(V, T, 4000)
    best = None
    for g, j in info.items():
        if j['side'] != 'R' or j['design'] != i['design']: continue
        W, U = geo.load(base + g + '.stl'); W = W * [-1, 1, 1]
        d = cKDTree(W).query(P)[0]
        if best is None or np.median(d) < best[0]: best = (np.median(d), g, d.max())
    print('%-16s mirror-of %-16s med %.4f max %.3f' % (f, best[1], best[0], best[2]))

import geo, numpy as np, glob, os, json, sys
from scipy.spatial import cKDTree
A = 'AssaultMarines-V2/AssaultMarines-V2/RawSTL/'
V0, T0 = geo.load(A + 'Legs/29-Legs-2.stl')
S0 = geo.surf(V0, T0, 400000)
zmin = float(sys.argv[1]) if len(sys.argv) > 1 else 22.5; rmax = float(sys.argv[2]) if len(sys.argv) > 2 else 6.0
reg = S0[(S0[:, 2] > zmin) & (np.hypot(S0[:, 0], S0[:, 1] - 0.5) < rmax)]
reg = reg[np.random.default_rng(0).choice(len(reg), min(4000, len(reg)), replace=False)]
c0 = reg.mean(0)
def rot(ax, deg):
    a = np.radians(deg); ax = np.asarray(ax, float); K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K
out = {}
for f in sorted(glob.glob(geo.RAW + A + 'Legs*/*.stl')) + sorted(glob.glob(geo.RAW + A + 'Legs*/Mirrored/*.stl')):
    rel = f.split(geo.RAW)[1]; V, T = geo.load(rel); S = geo.surf(V, T, 400000)
    top = S[:, 2].max(); C = S[S[:, 2] > top - 10]; tree = cKDTree(C)
    tgt = C[C[:, 2] > top - 1.0].mean(0); src_top = reg[reg[:, 2] > reg[:, 2].max() - 1.0].mean(0)
    best = None
    for a in range(-45, 46, 15):
        for b in range(-45, 46, 15):
            R0 = rot([1, 0, 0], a) @ rot([0, 1, 0], b)
            t0 = tgt - R0 @ src_top
            R, t, d = geo.icp(reg, tree, C, R0, t0, 25)
            m = np.median(d)
            if best is None or m < best[0]: best = (m, R, t)
    m, R, t = best
    R, t, d = geo.icp(reg, tree, C, R, t, 80); m = np.median(d)
    out[rel] = {'R': R.tolist(), 't': t.tolist(), 'med': float(m), 'p90': float(np.quantile(d, 0.9))}
    print('%-28s med %.3f p90 %.3f rot %5.2f  t %s' % (os.path.basename(f)[:-4], m, np.quantile(d, 0.9), geo.ang(R), np.round(t, 2)))
json.dump(out, open('f_legs3.json', 'w'), indent=1)

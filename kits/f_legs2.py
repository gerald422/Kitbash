import geo, numpy as np, glob, os, json
from scipy.spatial import cKDTree
A = 'AssaultMarines-V2/AssaultMarines-V2/RawSTL/'
def plug(V, T, M=np.eye(4)):
    S = geo.surf(V, T, 400000); S = S @ M[:3, :3].T + M[:3, 3]
    return S
V0, T0 = geo.load(A + 'Legs/29-Legs-2.stl')
S0 = plug(V0, T0); reg = S0[(S0[:, 2] > 25.9) & (np.hypot(S0[:, 0], S0[:, 1] - 0.5) < 5)]
reg = reg[np.random.default_rng(0).choice(len(reg), min(3000, len(reg)), replace=False)]
print('plug region', len(reg), np.round(reg.min(0), 2), np.round(reg.max(0), 2))
out = {}
for f in sorted(glob.glob(geo.RAW + A + 'Legs*/*.stl')) + sorted(glob.glob(geo.RAW + A + 'Legs*/Mirrored/*.stl')):
    rel = f.split(geo.RAW)[1]; V, T = geo.load(rel); S = plug(V, T)
    # candidate plug points: highest stuff
    top = S[:, 2].max(); C = S[S[:, 2] > top - 4]; tree = cKDTree(C)
    best = None
    for ax in ([1, 0, 0], [0, 1, 0]):
        for deg in range(-60, 61, 15):
            R0 = geo.F.pose(np.eye(3), np.zeros(3))[:3, :3] if False else None
            a = np.radians(deg); ax_ = np.array(ax, float)
            K = np.array([[0, -ax_[2], ax_[1]], [ax_[2], 0, -ax_[0]], [-ax_[1], ax_[0], 0]])
            R0 = np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K
            c0 = reg.mean(0); t0 = C[C[:, 2] > top - 1.5].mean(0) - R0 @ c0
            R, t, d = geo.icp(reg, tree, C, R0, t0, 30)
            m = np.median(d)
            if best is None or m < best[0]: best = (m, R, t)
    m, R, t = best
    R, t, d = geo.icp(reg, tree, C, R, t, 60); m = np.median(d)
    out[rel] = {'R': R.tolist(), 't': t.tolist(), 'med': float(m)}
    print('%-28s med %.3f rot %5.2f  plug-top moves %s' % (os.path.basename(f)[:-4], m, geo.ang(R), np.round(R @ [0, 0.5, 26.9] + t - [0, 0.5, 26.9], 2)))
json.dump(out, open('f_legs2.json', 'w'), indent=1)

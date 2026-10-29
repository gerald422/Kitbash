import geo, numpy as np, glob, os
from scipy.spatial import cKDTree
A = 'AssaultMarines-V2/AssaultMarines-V2/RawSTL/'
w = np.array([0, 0.5, 25.5])
V0, T0 = geo.load(A + 'Legs/29-Legs-2.stl')
reg = geo.region(V0, T0, w, 4.5, 2500)
reg = reg[reg[:, 2] > 24.5]
for f in sorted(glob.glob(geo.RAW + A + 'Legs*/*.stl')) + sorted(glob.glob(geo.RAW + A + 'Legs*/Mirrored/*.stl')):
    V, T = geo.load(f.split(geo.RAW)[1])
    S = geo.surf(V, T, 300000); S = S[np.linalg.norm(S - w, axis=1) < 6]
    if len(S) < 50: print('%-28s nothing near the waist' % os.path.basename(f)); continue
    tree = cKDTree(S)
    d0 = np.median(tree.query(reg)[0])
    R, t, d = geo.icp(reg, tree, S, np.eye(3), np.zeros(3), 40)
    print('%-28s as-is %.3f  icp %.3f rot %.2f shift %s' % (os.path.basename(f)[:-4], d0, np.median(d), geo.ang(R), np.round(R @ w + t - w, 3)))

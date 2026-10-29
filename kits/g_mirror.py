"""Are the Left/Mirrored copies exact X-mirrors of the right files, in place?"""
import geo, numpy as np, glob, os, re, sys, json
from scipy.spatial import cKDTree
pairs = []
B = 'AssaultMarines-V2/AssaultMarines-V2/RawSTL/'
for sub, msub in [('Melee', 'Melee/LeftOrientated'), ('Pistols', 'Pistols/LeftOrientated'), ('PowerFist', 'PowerFist/Mirrored'),
                  ('Legs', 'Legs/Mirrored'), ('Legs(JumpPack)', 'Legs(JumpPack)/Mirrored')]:
    R = sorted(glob.glob(geo.RAW + B + sub + '/*.stl')); L = sorted(glob.glob(geo.RAW + B + msub + '/*.stl'))
    Ln = {re.search(r"(\d+)-", os.path.basename(f)).group(1): f for f in L}
    for f in R:
        k = re.search(r"(\d+)-", os.path.basename(f)).group(1)
        if k not in Ln: print('no mirror for', f); continue
        pairs.append((sub, f.split(geo.RAW)[1], Ln[k].split(geo.RAW)[1]))
out = {}
for sub, r, l in pairs:
    V, T = geo.load(r); W, U = geo.load(l)
    P = geo.surf(W, U, 3000)
    tree = cKDTree(geo.surf(V * [-1, 1, 1], T[:, ::-1], 100000))
    d = tree.query(P)[0]
    tag = 'in place' if np.median(d) < 0.02 else ''
    if not tag:
        S = geo.surf(V * [-1, 1, 1], T[:, ::-1], 100000); tr = cKDTree(S)
        Rr, t, dd = geo.icp(P, tr, S, np.eye(3), S.mean(0) - P.mean(0), 60)
        tag = 'moved: rot %.2f t %s med %.3f' % (geo.ang(Rr), np.round(t, 2), np.median(dd))
    out[l] = tag
    print('%-16s %-28s med %.4f %s' % (sub, os.path.basename(l), np.median(d), tag))
json.dump(out, open('g_mirror.json', 'w'), indent=1)

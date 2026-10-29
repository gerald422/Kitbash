"""Mirrored legs files: A with mirrored_file = A @ MX @ original_file."""
import geo, numpy as np, json, os, glob
from scipy.spatial import cKDTree
W = {k: np.array(v) for k, v in json.load(open('waist_frames2.json')).items()}
KIT = 'AssaultMarines-V2/AssaultMarines-V2/RawSTL/'
MX = np.diag([-1.0, 1, 1, 1])
out = {}
for sub in ('Legs', 'Legs(JumpPack)'):
    for mrel in sorted(glob.glob(geo.RAW + KIT + sub + '/Mirrored/*.stl')):
        mrel = mrel.split(geo.RAW)[1]; orel = KIT + sub + '/' + os.path.basename(mrel).replace('Mirrored-', '')
        A0 = W[mrel] @ np.linalg.inv(MX @ W[orel] @ MX)
        V, T = geo.load(orel); S = geo.surf(V * [-1, 1, 1], T[:, ::-1], 200000)
        Wm, Um = geo.load(mrel); P = geo.surf(Wm, Um, 4000)
        Ai = np.linalg.inv(A0)
        R, t, d = geo.icp(P, cKDTree(S), S, Ai[:3, :3], Ai[:3, 3], 80)     # mirrored file -> MX(orig)
        A = np.linalg.inv(geo.M4(R, t))
        out[mrel] = {'orig': orel, 'A': A.tolist(), 'med': float(np.median(d))}
        print('%-26s med %.3f  A rot %.1f' % (os.path.basename(mrel)[:-4], np.median(d), geo.ang(A[:3, :3])))
json.dump(out, open('legs_mirror.json', 'w'), indent=1)

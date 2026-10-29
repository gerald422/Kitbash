import geo, json, numpy as np, glob, os
from scipy.spatial import cKDTree
C = json.load(open('/home/claude/sock/carry.json'))
ref = '126-Arm-11-R-A'; Ti = np.linalg.inv(np.array(C[ref]['T'])); jR = Ti[:3, 3]
V0, T0 = geo.load(C[ref]['src'])
reg = geo.region(V0, T0, jR, 4.0, 2500)
sR = np.array([5.484, 0.202, 31.949])
def find(V, T, region, j, s):
    """move region (joint j) to s, ICP onto V: returns new joint position, rot, median"""
    S = geo.surf(V, T, 300000); S = S[np.linalg.norm(S - s, axis=1) < 9]; tree = cKDTree(S)
    best = None
    for dz in (0, -1, 1):
        for dx in (0, -1, 1):
            R, t, d = geo.icp(region, tree, S, np.eye(3), s - j + [dx, 0, dz], 50)
            m = np.median(d)
            if best is None or m < best[0]: best = (m, R, t)
    m, R, t = best
    return R @ j + t, geo.ang(R), m
fs = sorted(glob.glob(geo.RAW + 'AssaultMarines-V2/AssaultMarines-V2/RawSTL/TwoHandedWeapons/*.stl'))
for f in fs + sorted(glob.glob(geo.RAW + 'AssaultMarines-V2/AssaultMarines-V2/RawSTL/PowerFist/*.stl'))[:6]:
    V, T = geo.load(f.split(geo.RAW)[1])
    out = []
    for side, region, j, s in (('R', reg, jR, sR), ('L', reg * [-1, 1, 1], jR * [-1, 1, 1], sR * [-1, 1, 1])):
        p, a, m = find(V, T, region, j, s)
        out.append('%s %s rot %.1f med %.3f' % (side, np.round(p - s, 2), a, m))
    print('%-26s' % os.path.basename(f)[:-4], ' | '.join(out))

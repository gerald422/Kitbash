import geo, json, numpy as np
from scipy.spatial import cKDTree
C = json.load(open('/home/claude/sock/carry.json'))
S = {s['type']: np.array(s['matrix']).reshape(4, 4) for s in C['23-Torso-2.001']['sidecar']['sockets']}
for k, m in S.items(): print(k, np.round(m, 3).tolist())
base = 'AssaultMarines-V2/AssaultMarines-V2/RawSTL/Chest/'
V0, T0 = geo.load(base + '23-Torso-2.stl')
for n in ['22-Torso-1', '24-Torso-3', '25-Torso-4', '26-Torso-5', '27-Torso-6']:
    V, T = geo.load(base + n + '.stl'); P = geo.surf(V, T, 200000); tree = cKDTree(P)
    out = []
    for k in ['arm__Torso_r', 'Head', 'Backpack', 'Legs to chest']:
        c = S[k][:3, 3]
        reg = geo.region(V0, T0, c, 4.0, 2000)
        d0 = tree.query(reg)[0]
        R, t, d = geo.icp(reg, tree, P)
        out.append('%s: as-is med %.3f | icp med %.3f rot %.2f t %s' % (k, np.median(d0), np.median(d), geo.ang(R), np.round(t + R @ c - c, 3)))
    print(n); [print('   ', o) for o in out]

import sys; sys.path.insert(0, '/home/claude/kits')
import geo, json, numpy as np, os
from scipy.spatial import cKDTree
inv = np.linalg.inv
O = "ChaplainWithJumpPack (1)/ChaplainWithJumpPack/"
PO = json.load(open('/home/claude/kits/cj/pose.json'))
acc = ['Accesories/Accesories-Raw-STL/23-Book.stl', 'Accesories/Accesories-Raw-STL/24-Badge.stl', 'Accesories/Accesories-Raw-STL/25-Holster.stl', 'Accesories/Accesories-Raw-STL/26-Grenade.stl',
       'Head/Head-Raw-STL/1-Head.stl', 'Jumppack/Jumppack-Raw-STL/11-Jumppack.stl', 'Jumppack/Jumppack-Raw-STL/12-Exhaust.stl', 'Chest/Chest-Raw-STL/2-ChestChaplain.stl']
A = {a: geo.surf(*geo.load(O + a), 20000) for a in acc}
CH = geo.surf(*geo.load(O + 'Chest/Chest-Raw-STL/2-ChestChaplain.stl'), 100000); tch = cKDTree(CH)
JP = geo.surf(*geo.load(O + 'Jumppack/Jumppack-Raw-STL/11-Jumppack.stl'), 100000); tjp = cKDTree(JP)
for X, p in PO.items():
    V, T = geo.load(p['legs']); S = geo.surf(V, T, 200000)
    for key in ('M_marfil', 'M_josh'):
        M = np.array(p[key]); St = S @ M[:3, :3].T + M[:3, 3]; tree = cKDTree(St)
        row = []
        for a, Q in A.items():
            d, _ = tree.query(Q); row.append('%s %.2f/%.0f%%' % (os.path.basename(a)[:-4][:8], np.percentile(d, 5), 100 * (d < 0.15).mean()))
        print(X, key[2:], ' | '.join(row))
for a in acc[:4] + ['Jumppack/Jumppack-Raw-STL/12-Exhaust.stl']:
    d1, _ = tch.query(A[a]); d2, _ = tjp.query(A[a])
    print('%-12s to chest %.2f/%.0f%%  to jumppack %.2f/%.0f%%' % (os.path.basename(a)[:-4], np.percentile(d1, 5), 100 * (d1 < .15).mean(), np.percentile(d2, 5), 100 * (d2 < .15).mean()))

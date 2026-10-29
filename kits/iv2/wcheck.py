import sys; sys.path.insert(0, '/home/claude/kits')
import geo, numpy as np, os
from scipy.spatial import cKDTree
IV = "../Intercessors-V2/Intercessors-V2/Intercessors-Bits/RawSTL/"
WkR = geo.M4(np.eye(3), np.array([-1.13, 2.77, 1.20]))
WbR = geo.M4(np.diag([-1.0, -1, 1]), np.array([0.82, -8.43, -2.94]))
WbL = geo.M4(np.diag([-1.0, -1, 1]), np.array([-0.845, -8.42, -2.855]))
MX = np.diag([-1.0, 1, 1, 1]); WkL = MX @ WkR @ MX
hands = [h for h in sorted(os.listdir(geo.U + IV + "Hands-Raw")) if h.endswith('.stl')]
for tgt, W, Wk, hdir in [("Bolter-Individual-Raw/165-Bolter-A-7-R.stl", WbR, WkR, "Hands-Raw/"), ("Bolter-Individual-Raw/Bolter-Individual-Left/144-Bolter-A-4-L.stl", WbL, WkL, "Hands-Raw/Hand-Left/")]:
    V, T = geo.load(IV + tgt); tree = cKDTree(geo.surf(V, T, 250000))
    res = []
    for h in hands:
        hl = h if 'Left' not in hdir else h.replace('-R.stl', '-L.stl')
        try: P = geo.surf(*geo.load(IV + hdir + hl), 4000)
        except FileNotFoundError: continue
        A = W @ np.linalg.inv(Wk); P2 = P @ A[:3, :3].T + A[:3, 3]
        res.append((float(np.median(tree.query(P2)[0])), hl))
    res.sort(); print(tgt.split('/')[-1], [(h, round(d, 3)) for d, h in res[:4]])

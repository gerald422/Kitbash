"""NoHand bolter frame -> hand-held bolter frame (165-Bolter-A-7-R, 144-L)."""
import sys; sys.path.insert(0, '/home/claude/kits')
import geo, numpy as np, json
from scipy.spatial import cKDTree
IV = "../Intercessors-V2/Intercessors-V2/Intercessors-Bits/RawSTL/"
src = geo.surf(*geo.load(IV + "Weapons-NoHand-Raw/255-Bolter-A-NoHand.stl"), 6000)
out = {}
for tgt in ["Bolter-Individual-Raw/165-Bolter-A-7-R.stl", "Bolter-Individual-Raw/144-Bolter-A-4-R.stl", "Bolter-Individual-Raw/Bolter-Individual-Left/144-Bolter-A-4-L.stl", "Bolter-Individual-Raw/172-Bolter-A-8-R.stl"]:
    V, T = geo.load(IV + tgt); Q = geo.surf(V, T, 250000); tree = cKDTree(Q)
    best = None
    for a in (90, -90):
        c, s = np.cos(np.radians(a)), np.sin(np.radians(a)); R0 = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])
        R, t, d = geo.icp(src, tree, Q, R0, np.zeros(3), 60, trim=0.8)
        if best is None or np.median(d) < best[0]: best = (float(np.median(d)), geo.M4(R, t), a)
    out[tgt] = {'Q': best[1].tolist(), 'med': best[0]}
    print('%-30s start %d  med %.3f  rot %s  t %s' % (tgt.split('/')[-1], best[2], best[0], np.round(best[1][:3, :3], 3).tolist(), np.round(best[1][:3, 3], 3)))
json.dump(out, open('/home/claude/kits/iv2/boltQ.json', 'w'), indent=1)

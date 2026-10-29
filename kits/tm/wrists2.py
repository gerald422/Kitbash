"""Roll for the Techmarine left wrists: arm 12's from Mar Fil's own hand 38 on it; carried to 14/16 by matching 12's
wrist end onto theirs (when the forearm sculpt is the same)."""
import sys; sys.path.insert(0, '/home/claude/kits')
import geo, json, numpy as np
from scipy.spatial import cKDTree
W = json.load(open('/home/claude/kits/tm/wrists.json')); RU = json.load(open('/home/claude/kits/tm/rules.json'))
A = 'Techmarine (2)/Techmarine/Arms/Arms-Raw-STL/'
W12 = np.array(W[A + '12-Arm-1-L.stl']); Wh = np.array(RU['hands']['38-Hand.stl']['L']['M'])
W12c = Wh.copy(); W12c[:3, 3] = W12[:3, 3]
out = dict(W); out[A + '12-Arm-1-L.stl'] = W12c.tolist()
S12 = geo.surf(*geo.load(A + '12-Arm-1-L.stl'), 300000); R12 = S12[np.linalg.norm(S12 - W12[:3, 3], axis=1) < 4.0][::3]
for b in ('14-Arm-2-L', '16-Arm-3-L'):
    Wr = np.array(W[A + b + '.stl']); S = geo.surf(*geo.load(A + b + '.stl'), 300000); tr = cKDTree(S)
    best = None
    for roll in range(0, 360, 30):
        c, s = np.cos(np.radians(roll)), np.sin(np.radians(roll)); Ry = np.array([[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1.0]])
        G0 = Wr @ Ry @ np.linalg.inv(W12)
        R, t, d = geo.icp(R12, tr, S, G0[:3, :3], G0[:3, 3], 40)
        if best is None or np.median(d) < best[0]: best = (float(np.median(d)), geo.M4(R, t))
    md, G = best; Wc = G @ W12c
    ang = np.degrees(np.arccos(np.clip(Wc[:3, 2] @ Wr[:3, 2], -1, 1))); yang = np.degrees(np.arccos(np.clip(Wc[:3, 1] @ Wr[:3, 1], -1, 1)))
    print('%s: arm 12 wrist end matched %.3f; wrist axis %.1f deg from the rule, roll %.0f deg from the rule' % (b, md, yang, ang))
    if md < 0.08: out[A + b + '.stl'] = Wc.tolist()
    else: print('   different forearm: keeps the rule')
json.dump(out, open('/home/claude/kits/tm/wrists.json', 'w'), indent=1)

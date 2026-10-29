import sys; sys.path.insert(0, '/home/claude/kits')
import geo, json, numpy as np, os, glob
from scipy.spatial import cKDTree
inv = np.linalg.inv
def ang(R): return float(np.degrees(np.arccos(np.clip((np.trace(R[:3, :3]) - 1) / 2, -1, 1))))
P = json.load(open('amv2_partial.json'))['side']
TOR = {s['type']: np.array(s['matrix']).reshape(4, 4) for s in P['AssaultMarines-V2/AssaultMarines-V2/RawSTL/Chest/22-Torso-1.stl']['sockets']}
AMT = 'AssaultMarines-V2/AssaultMarines-V2/RawSTL/Chest/22-Torso-1.stl'
O = "Techmarine (2)/Techmarine/"
S = geo.surf(*geo.load(AMT), 300000)
C = geo.surf(*geo.load(O + 'Chest/Chest-Raw-STL/2-Chest.stl'), 300000); tc = cKDTree(C)
out = {}
for t, r in (('Waist', 6.0), ('Shoulder R', 4.5), ('Shoulder L', 4.5), ('Neck', 4.5), ('Back', 5.0)):
    c = TOR[t][:3, 3]; R = S[np.linalg.norm(S - c, axis=1) < r]; R = R[::max(1, len(R) // 3000)]
    Rg, tg, d = geo.icp(R, tc, C, np.eye(3), np.zeros(3), 50); G = geo.M4(Rg, tg)
    out[t] = (G @ TOR[t]).tolist()
    print('%-10s AM region on the TM chest: med %.3f  moved %.2f deg %.3f mm' % (t, np.median(d), ang(G), np.linalg.norm((G @ TOR[t])[:3, 3] - TOR[t][:3, 3])))
json.dump(out, open('/home/claude/kits/tm/chest_sockets.json', 'w'), indent=1)
BP = geo.surf(*geo.load(O + 'Backpack/Backpack-Raw-STL/11-Techmarine-Backpack.stl'), 300000); tb = cKDTree(BP)
d, _ = tb.query(C); print('backpack vs chest: closest %.2f, touching %.1f%%' % (d.min(), 100 * (d < 0.1).mean()))
for f in sorted(glob.glob(geo.U + O + '*/*Raw-STL/*.stl')):
    b = os.path.basename(f)
    if not any(b.startswith(p) for p in ('2', '3', '4', '24', '25', '26', '27', '28', '29', '30', '31', '32', '36', '37', '13', '15', '17', '21', '23', '38')): continue
    Q = geo.surf(*geo.load(f[len(geo.U):]), 40000)
    db, _ = tb.query(Q); dc, _ = tc.query(Q)
    print('%-28s to backpack closest %.2f (%.1f%% within 0.1) | to chest closest %.2f (%.1f%%)' % (b, db.min(), 100 * (db < 0.1).mean(), dc.min(), 100 * (dc < 0.1).mean()))

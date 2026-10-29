"""Vet shin pads (Shin R/L, from the Techmarine rig pads) and pauldrons (Pad R/L, Josh's 62-on-76 example), per file."""
import sys; sys.path.insert(0, '/home/claude/real'); sys.path.insert(0, '/home/claude/kits')
import fitlib as F, numpy as np, json, glob, os
RAW = '/home/claude/raw/'
def rig(prefix, name):
    Z = np.load(prefix + ".npz"); J = json.load(open(prefix + ".json")); k = J[name]["key"]
    v = Z[k + "_v"].astype(float); t = Z[k + "_t"].astype(np.int64); mw = Z[k + "_mw"]
    W = v @ mw[:3, :3].T + mw[:3, 3]
    if np.linalg.det(mw[:3, :3]) < 0: t = t[:, ::-1]
    q = np.round(W, 5); u, inv = np.unique(q, axis=0, return_inverse=True)
    return u, inv.reshape(-1)[t]
TP = "/home/claude/blend/mf/tech_parts"
S, padw = {}, {}
for side, knee, pad in (("R", "Knee-R-Pose", "Intercessor-ShinPad-R"), ("L", "Knee-L-Pose", "Intercessor-ShinPad-L")):
    V, T = rig(TP, knee); f = F.find_shin_points(V, T); S[side] = F.shin_frame(*f[0])
    pv, pt = rig(TP, pad); padw[side] = F.surf(pv, pt, 60000)
out = {}
UP = "/mnt/user-data/uploads/new cults/All Mar All the time/"; NC = "/mnt/user-data/uploads/new cults/"
O = UP + "Techmarine (2)/Techmarine/"
for fn, side in (('7-Shinpad-R', 'R'), ('8-Shinpad-L', 'L')):
    for f in [O + 'Shinpads/Shinpads-Raw-STL/' + fn + '.stl']:
        V, T = F.stl(f); src = F.surf(V, T, 4000)
        R, t, d = F.best_fit(src, padw[side])
        fit = np.linalg.inv(S[side]) @ F.pose(R, t)
        out[f[len(NC):]] = {'type': f'Shin {side}', 'fit': fit.tolist(), 'median': float(np.median(d))}
        print('%-30s Shin %s  match %.3f' % (os.path.basename(f), side, np.median(d)), flush=True)
pf = json.load(open('/home/claude/real/pad_fits.json')); fit62 = np.array(pf['_fit62'])
A = UP + "AssaultMarines-V2/AssaultMarines-V2/RawSTL/"
V62, T62 = F.stl(A + "ShoulderPads/62-ShoulderPad-1.stl"); s62 = F.surf(V62, T62, 5000)
MXv = np.array([-1.0, 1, 1]); MX = np.diag([-1.0, 1, 1, 1])
for f in sorted(glob.glob(O + 'ShoulderPads/Shoulderpad-Raw-STL/*.stl')):
    V, T = F.stl(f); tgt = F.surf(V, T, 80000)
    left = os.path.basename(f).endswith('-L.stl')
    R, t, d = F.best_fit(s62 * MXv if left else s62, tgt); G = F.pose(R, t); md = float(np.median(d))
    fit = (MX @ fit62 @ MX if left else fit62) @ np.linalg.inv(G)
    out[f[len(NC):]] = {'type': 'Pad L' if left else 'Pad R', 'fit': fit.tolist(), 'median': md}
    print('%-30s Pad %s  match %.3f' % (os.path.basename(f), 'L' if left else 'R', md), flush=True)
json.dump(out, open('/home/claude/kits/tm/tm_pads.json', 'w'), indent=1)

"""Mar Fil's Techmarine build file -> the kit frame: register its backpack on the kit backpack, then read where the
servo arm's shoulder ball, the mechadendrite connector and the forge gun sit."""
import sys; sys.path.insert(0, '/home/claude/kits'); sys.path.insert(0, '/home/claude/real')
import geo, json, numpy as np
from scipy.spatial import cKDTree
import fitlib as F
Z = np.load('/home/claude/blend/mf/tech_pack.npz'); J = json.load(open('/home/claude/blend/mf/tech_pack.json'))
def rig(name):
    k = J[name]['key']; v = Z[k + '_v'].astype(float); t = Z[k + '_t'].astype(np.int64); mw = Z[k + '_mw']
    W = v @ mw[:3, :3].T + mw[:3, 3]
    if np.linalg.det(mw[:3, :3]) < 0: t = t[:, ::-1]
    return W, t
O = "Techmarine (2)/Techmarine/"
KB = geo.surf(*geo.load(O + 'Backpack/Backpack-Raw-STL/11-Techmarine-Backpack.stl'), 300000); tk = cKDTree(KB)
W, t = rig('BackPack-Techmarine-Pose'); RB = F.surf(W, t, 20000)
print('rig backpack bbox', np.round(RB.min(0), 1), np.round(RB.max(0), 1), ' kit', np.round(KB.min(0), 1), np.round(KB.max(0), 1))
best = None
for a in range(0, 360, 30):
    for flip in (False, True):
        c, s = np.cos(np.radians(a)), np.sin(np.radians(a)); R0 = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])
        if flip: R0 = R0 @ np.diag([1, -1, -1.0])
        t0 = KB.mean(0) - R0 @ RB.mean(0)
        R, tt, d = geo.icp(RB[::4], tk, KB, R0, t0, 60)
        if best is None or np.median(d) < best[0]: best = (float(np.median(d)), geo.M4(R, tt))
print('rig backpack on the kit backpack: median %.3f' % best[0])
G = best[1]; np.save('/home/claude/kits/tm/rig_to_kit.npy', G)
def kit(name):
    W, t = rig(name); return W @ G[:3, :3].T + G[:3, 3], t
for n in J:
    W, t = kit(n); print('%-26s kit bbox %s %s' % (n, np.round(W.min(0), 1), np.round(W.max(0), 1)))

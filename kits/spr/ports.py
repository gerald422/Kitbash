"""Where the belt plugs in: the belt-fed gun minus the plain gun, the weapon's pack minus the plain hw pack."""
import sys, json, numpy as np
sys.path.insert(0, '/home/claude/kits/cr'); sys.path.insert(0, '/home/claude/real')
import stlcache, fitlib as F
from scipy.spatial import cKDTree
from hands import align
from comp import comps
U = "/mnt/user-data/uploads/new cults/Springles/"
SCR = "/tmp/claude-0/-home-claude/3c0770af-36e9-58fc-b7f7-70184e2b5d36/scratchpad/"
def diff(a, b, thr=0.25):
    V1, T1 = stlcache.load(U + a); V0, T0 = stlcache.load(U + b)
    m, R, t = align(V1, T1, V0, T0)
    S0 = F.surf(V0, T0, 400000, 3); tree = cKDTree(S0)
    d, _ = tree.query(V1[T1].mean(1) @ R.T + t); k = d > thr
    T2 = T1[k]; u, inv = np.unique(T2, return_inverse=True); V2 = V1[u]; T2 = inv.reshape(-1, 3)
    n, lab = comps(V2, T2); lt = lab[T2[:, 0]]; cnt = np.bincount(lt)
    return m, V2, T2, lt, cnt
for a, b, tag in [("heavy weapons/heavy bolter/heavy bolter belt fed no hand.stl", "heavy weapons/heavy bolter/heavy bolter no hands.stl", "hb_gun"),
                  ("heavy weapons/backpacks/hw heavy bolter backpack.stl", "heavy weapons/backpacks/hw backpack.stl", "hb_pack"),
                  ("heavy weapons/las cannon/las cannon underslung belt fed no hands.stl", "heavy weapons/las cannon/las cannon underslung no hands.stl", "lc_gun"),
                  ("heavy weapons/backpacks/hw las cannon backpack.stl", "heavy weapons/backpacks/hw backpack.stl", "lc_pack")]:
    m, V2, T2, lt, cnt = diff(a, b)
    big = np.argsort(-cnt)[:4]
    print(tag, "align %.3f" % m, "diff tris", len(T2), "components", [(int(cnt[i]), V2[T2[lt == i]].reshape(-1, 3).mean(0).round(1).tolist()) for i in big])
    np.savez(SCR + tag + ".npz", V=V2.astype(np.float32), T=T2.astype(np.int32))

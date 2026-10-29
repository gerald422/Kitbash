"""Match each AM legs' waist region (plug + plating) onto a body adaptor, many starts."""
import sys; sys.path.insert(0, '/home/claude/kits'); sys.path.insert(0, '/home/claude/kits/cr')
import numpy as np, json, geo, stlcache
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation as Rot
import legs_match as LM
D = "/mnt/user-data/uploads/new cults/body adaptor/"
def rotz(a): c, s = np.cos(a), np.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
res = {}
for i in [int(a) for a in sys.argv[1:]] or range(1, 7):
    V, T = stlcache.load(D + f"lower_body_(torso)_{i}.stl")
    S = geo.surf(V, T, 300000); tree = cKDTree(S); c = S.mean(0)
    best = None
    for rref, (M, R, j) in list(LM.REFS.items())[:6]:
        Rc = R - j      # region about the waist joint
        for flip in (1, -1):
            # legs +Z (up) -> adaptor +Y*flip ; try twists about that axis
            B = np.array([[1, 0, 0], [0, 0, flip], [0, -flip, 0]], float).T   # maps z->y*flip
            B = np.array([[1, 0, 0], [0, 0, -flip], [0, flip, 0]], float)
            for tw in range(0, 360, 30):
                R0 = B @ rotz(np.radians(tw))
                for dy in (-2, 0, 2):
                    t0 = c + np.array([0, dy, 0])
                    Rg, tg, d = geo.icp(Rc, tree, S, R0, t0, 30)
                    md = float(np.median(d))
                    if best is None or md < best[0]: best = (md, rref, Rg, tg, j, flip, tw, dy)
    md, rref, Rg, tg, j, flip, tw, dy = best
    print(i, "best med %.3f" % md, rref.split('/')[-1], "flip", flip, "tw", tw, "dy", dy, "\n  R", Rg.round(3).tolist(), "t", tg.round(3).tolist(), flush=True)
    res[i] = dict(med=md, ref=rref, R=Rg.tolist(), t=tg.tolist(), j=list(map(float, j)))
json.dump(res, open('/home/claude/kits/cr/ad_match.json', 'w'), indent=1)

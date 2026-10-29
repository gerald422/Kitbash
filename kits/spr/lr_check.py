import sys, json, numpy as np, os, glob
sys.path.insert(0, "/home/claude/blend/forclaude"); sys.path.insert(0, "/home/claude/real")
from stl_io import read_stl
import fitlib as F
from scipy.spatial import cKDTree
U = "/mnt/user-data/uploads/new cults/Springles/"
MX3 = np.diag([-1.0, 1, 1])
pat = sys.argv[1]
files = sorted(glob.glob(U + "pattern%s arms/*/*.stl" % pat))
L = [f for f in files if "Larm" in f]
def load(f):
    v, n, t = read_stl(f); return np.asarray(v, float), np.asarray(t)
res = {}
for lf in L:
    b = os.path.basename(lf)
    rf_guess = lf.replace("Larm", "Rarm").replace("Rarm melee", "melee Rarm")
    if not os.path.exists(rf_guess): print("no R for", b); continue
    VL, TL = load(lf); VR, TR = load(rf_guess)
    src = F.surf(VR @ MX3, TR, 3000, 1); tgt = F.surf(VL, TL, 30000, 2)
    R, t, d = F.best_fit(src, tgt, iters=15)
    print("%-36s vs mirrored R: median %.3f p90 %.3f  nV %d/%d" % (b, np.median(d), np.quantile(d, .9), len(VL), len(VR)), flush=True)
    res[b] = dict(R=os.path.relpath(rf_guess, U), med=float(np.median(d)), p90=float(np.quantile(d, .9)), Rm=R.tolist(), t=t.tolist())
json.dump(res, open("lr_%s.json" % pat, "w"), indent=0)

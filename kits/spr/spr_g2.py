import sys, json, numpy as np
sys.path.insert(0, "/home/claude/blend/forclaude"); sys.path.insert(0, "/home/claude/real")
from stl_io import read_stl
import fitlib as F
from scipy.spatial import cKDTree
U = "/mnt/user-data/uploads/new cults/Springles/"
h = json.load(open("heresy.json")); d = np.load("heresy.npz"); A = json.load(open("arm_files.json"))
out = json.load(open("G.json"))
for name in ["patternC helmet hold arm", "patternS helmet hold arm"]:
    K = 1.1002 if "patternC" in name else 1.1
    v, n, t = read_stl(U + A[name]); V = np.asarray(v, float) * K; T = np.asarray(t)
    J = d[h[name]["key"]].astype(float)
    src = F.surf(V, T, 6000, 1); tgt = J
    R, tt, dd = F.best_fit(src, tgt)
    S = F.surf(V, T, 30000, 2); tree = cKDTree(J); R, tt, dd = F.icp(S, tree, R, tt, 60, 0.95)
    print(name, "median %.4f p95 %.4f max %.4f" % (np.median(dd), np.quantile(dd, .95), dd.max()))
    # extents check
    print("  ext file*K", np.round(np.ptp(V, 0), 2), " josh", np.round(np.ptp(J, 0), 2))
    G = np.eye(4); G[:3, :3] = R; G[:3, 3] = tt
    out[name].update(G=G.tolist(), max=float(dd.max()), scale=K, icp=float(np.median(dd)))
json.dump(out, open("G.json", "w"), indent=0)

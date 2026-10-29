import sys, json, numpy as np
sys.path.insert(0, "/home/claude/blend/forclaude"); sys.path.insert(0, "/home/claude/real")
from stl_io import read_stl
import fitlib as F
U = "/mnt/user-data/uploads/new cults/Springles/"
h = json.load(open("heresy.json")); d = np.load("heresy.npz"); A = json.load(open("arm_files.json"))
K = 1.1002
for name in ["patternC banner arm", "patternC melee Rarm 1"]:
    v, n, t = read_stl(U + A[name]); V = np.asarray(v, float); T = np.asarray(t).reshape(-1)
    _, first = np.unique(T, return_index=True); order = np.argsort(first)   # vertex ids in order of first use
    Vf = V[order]
    J = d[h[name]["key"]].astype(float)
    R, tt = F.kabsch(Vf * K, J); r = np.linalg.norm((Vf * K) @ R.T + tt - J, axis=1)
    print(name, "first-use corr: max %.4f med %.4f" % (r.max(), np.median(r)))

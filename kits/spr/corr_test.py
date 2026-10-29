import sys, json, numpy as np
sys.path.insert(0, "/home/claude/blend/forclaude"); sys.path.insert(0, "/home/claude/real")
from stl_io import read_stl
import fitlib as F
U = "/mnt/user-data/uploads/new cults/Springles/"
h = json.load(open("heresy.json")); d = np.load("heresy.npz"); A = json.load(open("arm_files.json"))
K = 1.1002
for name in ["patternC banner arm", "patternC melee Rarm 1", "patternC helmet hold arm"]:
    v, n, t = read_stl(U + A[name]); V = np.asarray(v, float)
    # first-appearance unique
    q = np.round(V, 6); _, first, inv = np.unique(q, axis=0, return_index=True, return_inverse=True)
    order = np.argsort(first); Vf = V[first[order]]
    J = d[h[name]["key"]].astype(float)
    print(name, len(V), len(Vf), len(J), "tris", len(V)//3 if V.ndim==2 else None)
    if len(Vf) == len(J):
        R, tt = F.kabsch(Vf * K, J); r = np.linalg.norm((Vf * K) @ R.T + tt - J, axis=1)
        print("  corr kabsch: max %.4f med %.4f det %.3f" % (r.max(), np.median(r), np.linalg.det(R)))

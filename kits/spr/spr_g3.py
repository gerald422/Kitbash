import sys, json, numpy as np
sys.path.insert(0, "/home/claude/blend/forclaude"); sys.path.insert(0, "/home/claude/real")
from stl_io import read_stl
import fitlib as F
U = "/mnt/user-data/uploads/new cults/Springles/"
h = json.load(open("heresy.json")); d = np.load("heresy.npz"); A = json.load(open("arm_files.json"))
out = json.load(open("G.json"))
MX3 = np.diag([-1.0, 1, 1])
for name in ["patternC helmet hold arm", "patternS helmet hold arm"]:
    K = 1.1002 if "patternC" in name else 1.1
    v, n, t = read_stl(U + A[name]); V = np.asarray(v, float); T = np.asarray(t).reshape(-1)
    _, first = np.unique(T, return_index=True); Vf = V[np.argsort(first)] * K
    J = d[h[name]["key"]].astype(float)
    for lab, P in (("plain", Vf), ("mirrorX", Vf @ MX3)):
        R, tt = F.kabsch(P, J); r = np.linalg.norm(P @ R.T + tt - J, axis=1)
        print(name, lab, "max %.4f med %.4f" % (r.max(), np.median(r)))
    # also ICP with mirror
    P = Vf @ MX3; R, tt = F.kabsch(P, J); r = np.linalg.norm(P @ R.T + tt - J, axis=1)
    if r.max() < 0.01:
        G = np.eye(4); G[:3, :3] = R @ MX3; G[:3, 3] = tt     # includes the mirror
        out[name].update(G=G.tolist(), max=float(r.max()), scale=K, mirrored=True)
json.dump(out, open("G.json", "w"), indent=0)

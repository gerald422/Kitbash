"""G for each of Josh's 74 heresy arms: rigid map from (K x Springles file coords) to Josh's mesh coords,
by vertex correspondence (Blender keeps first-use vertex order). Also fit the scale freely as a check."""
import sys, json, numpy as np
sys.path.insert(0, "/home/claude/blend/forclaude"); sys.path.insert(0, "/home/claude/real")
from stl_io import read_stl
import fitlib as F
U = "/mnt/user-data/uploads/new cults/Springles/"
h = json.load(open("heresy.json")); d = np.load("heresy.npz"); A = json.load(open("arm_files.json"))
K = 1.1002
def umeyama(P, Q):
    cp, cq = P.mean(0), Q.mean(0); P0, Q0 = P - cp, Q - cq
    U_, S, Vt = np.linalg.svd(P0.T @ Q0); D = np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U_.T))])
    R = Vt.T @ D @ U_.T; s = (S * np.diag(D)).sum() / (P0 ** 2).sum(); return s, R, cq - s * R @ cp
out = {}
for name, rel in sorted(A.items()):
    v, n, t = read_stl(U + rel); V = np.asarray(v, float); T = np.asarray(t).reshape(-1)
    _, first = np.unique(T, return_index=True); Vf = V[np.argsort(first)]
    J = d[h[name]["key"]].astype(float)
    if len(Vf) != len(J): print(name, "COUNT", len(Vf), len(J)); continue
    R, tt = F.kabsch(Vf * K, J); r = np.linalg.norm((Vf * K) @ R.T + tt - J, axis=1)
    s, _, _ = umeyama(Vf, J)
    G = np.eye(4); G[:3, :3] = R; G[:3, 3] = tt
    out[name] = dict(rel=rel, G=G.tolist(), max=float(r.max()), scale=float(s))
    print("%-34s max %.4f  s %.5f" % (name, r.max(), s))
json.dump(out, open("G.json", "w"), indent=0)
print(len(out))

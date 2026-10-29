import sys; sys.path.insert(0,'/home/claude/real')
import fitlib as F, numpy as np, json, glob, os
U = "/mnt/user-data/uploads/new cults/"
A = U + "All Mar All the time/AssaultMarines-V2/AssaultMarines-V2/RawSTL/"
VB = U + "All Mar All the time/VeteranBladeSquad/VeteranBladeSquad/"
M = U + "51 May 2026-20260612T074408Z-3-001/51 May 2026/legs-chin pads and base/"
def rig(prefix, name):
    Z = np.load(prefix + ".npz"); J = json.load(open(prefix + ".json")); k = J[name]["key"]
    v = Z[k + "_v"].astype(float); t = Z[k + "_t"].astype(np.int64); mw = Z[k + "_mw"]
    W = v @ mw[:3, :3].T + mw[:3, 3]
    if np.linalg.det(mw[:3, :3]) < 0: t = t[:, ::-1]
    q = np.round(W, 5); u, inv = np.unique(q, axis=0, return_inverse=True)
    return u, inv.reshape(-1)[t], mw, v
P = "/home/claude/blend/mf/tech_parts"
S = {}; padw = {}; rigmw = {}
for side, knee, pad in (("R", "Knee-R-Pose", "Intercessor-ShinPad-R"), ("L", "Knee-L-Pose", "Intercessor-ShinPad-L")):
    V, T, _, _ = rig(P, knee); f = F.find_shin_points(V, T); assert len(f) == 1, len(f)
    ea, eb, top, op = f[0]; S[side] = F.shin_frame(ea, eb, top, op)
    pv, pt, mw, lv = rig(P, pad); padw[side] = F.surf(pv, pt, 60000); rigmw[side] = mw
print("rig frames: R vs mirrored L %.3f deg" % F.ang(np.linalg.inv(F.MX @ S["L"] @ F.MX) @ S["R"]))
SPL = json.load(open("/home/claude/blend/mf/icp/shin_place.json"))["pads"]
MXL = np.diag([-1.0, 1, 1, 1])
out = {}
def fit_pad(path, side, inits=None):
    V, T = F.stl(path); src = F.surf(V, T, 4000)
    R, t, d = F.best_fit(src, padw[side], inits)
    W = F.pose(R, t)
    return np.linalg.inv(S[side]) @ W, float(np.median(d)), float(np.quantile(d, .9)), W

import re
U2 = "/mnt/user-data/uploads/new cults/Marta/"
L = json.load(open("/home/claude/kits/marta/chin/todo.json"))
out = {}
for rel in L:
    b = os.path.basename(rel)
    side = "L" if re.search(r"_L(\.|_)", b) or b.endswith("_L.stl") else "R"
    fit, med, p90, W = fit_pad(U2 + rel, side)
    out[rel] = {"side": side, "fit": fit.tolist(), "median": med, "p90": p90}
    print("%-40s %s  match median %.3f p90 %.3f" % (b, side, med, p90), flush=True)
    json.dump(out, open("/home/claude/kits/marta/chin/chin_fits.json", "w"), indent=1)

"""Try refinements of the shin finder; save frames for rig knees and library legs per variant."""
import sys, json, numpy as np
sys.path.insert(0, "/home/claude/tiow_blender")
import tiow_inbox as T
from mathutils import Vector
exec(open("/home/claude/test/v16/rigcheck.py").read().split("MXL =")[0].split("def frame")[0])
def frame(found):
    ea, eb, top, op = found
    pts = [Vector(p) for p in (ea, eb, top)]; n = Vector(op)
    return np.array(T._three_point_frame("Shin", pts, [n, n, n]))
orig_spheres = T._spheres
def spheres_var(mode):
    def f(V, N, r, sgn, cell=0.1, minvotes=40):
        C = V - sgn * r * N; found = []
        for shift in (0.0, 0.5):
            key = np.floor(C / cell + shift).astype(np.int64)
            uk, inv, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True)
            for k in np.argsort(-cnt)[:12]:
                if cnt[k] < minvotes: break
                c = C[inv.reshape(-1) == k].mean(0); rr = r
                its, band = {"B": (1, 0.08), "C": (6, 0.08), "D": (6, 0.05)}[mode]
                for _ in range(its):
                    d = np.linalg.norm(V - c, axis=1)
                    P = V[np.abs(d - (r if mode == "B" else rr)) < band]
                    if len(P) < 20: break
                    A = np.c_[2 * P, np.ones(len(P))]
                    x = np.linalg.lstsq(A, (P ** 2).sum(1), rcond=None)[0]
                    c, rr = x[:3], float(np.sqrt(max(x[3] + x[:3] @ x[:3], 0.0)))
                d = np.linalg.norm(V - c, axis=1); on = int((np.abs(d - rr) < 0.05).sum())
                if abs(rr - r) < 0.25 and on >= minvotes and all(np.linalg.norm(c - q[0]) > 0.8 for q in found):
                    found.append((c, rr, on))
        return found
    return f
L = "/home/claude/test/padlib/Mar Fil - Tacticus/Kit/Legs/"
out = {}
for var in ("A",):
    T._spheres = orig_spheres if var == "A" else spheres_var(var)
    for pre, knee in (("tech_parts", "Knee-L-Pose"), ("chap_parts", "Knee-A-Pose.L")):
        V, Tr, _ = rig("/home/claude/blend/mf/" + pre, knee); V, Tr = merge(V, Tr)
        f = T.find_shin_points(V, Tr); out[f"{var}|{pre}"] = [frame(x).tolist() for x in f]
    for legs in ("29-Legs-2", "35-Legs-2-A"):
        V, Tr = T.read_stl_np(L + legs + ".stl")
        f = T.find_shin_points(V, Tr); out[f"{var}|{legs}"] = [frame(x).tolist() for x in f]
    print(var, {k: len(v) for k, v in out.items() if k.startswith(var)})
json.dump(out, open("/home/claude/test/v16/var_frames.json", "w"))

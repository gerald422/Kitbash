"""Springles heresy pattern arms (C/P/S): Shoulder R / Shoulder L fits.
Rule (= Josh's placements in '3rd attempt finalising actual.blend'): mesh scaled by K (heresy scale), the shoulder disc
(largest flat facing the chest: file -Y on right arms, +Y on left arms) centroid on Josh's HeresyArms_r point, file axes.
R: fit = inv(S_R) @ S_H @ T(-c)        L: fit = inv(S_L) @ MX @ S_H @ MY @ T(-c)   (c = disc centroid, scaled)"""
import sys, json, numpy as np, os
sys.path.insert(0, "/home/claude/blend/forclaude")
from stl_io import read_stl
U = "/mnt/user-data/uploads/new cults/Springles/"
h = json.load(open("/home/claude/kits/spr/heresy.json"))
S_H = np.array(h["SOCK:23-Torso-2.001_socket_HeresyArms_r"]["mw"])
S_R = np.eye(4); S_R[:3, 3] = [5.4838, 0.2019, 31.9493]
S_L = np.eye(4); S_L[:3, 3] = [-5.4838, 0.2019, 31.9493]
MX = np.diag([-1.0, 1, 1, 1]); MY = np.diag([1.0, -1, 1, 1])
def K_of(rel): return 1.1002 if "patternC" in rel else 1.1
def T(c): M = np.eye(4); M[:3, 3] = -np.asarray(c); return M
def arm_fit(rel, disc):
    k = K_of(rel); c = np.array(disc["centroid"]) * k
    if disc["n"][1] < 0: return "Shoulder R", np.linalg.inv(S_R) @ S_H @ T(c), k
    return "Shoulder L", np.linalg.inv(S_L) @ MX @ S_H @ MY @ T(c), k
if __name__ == "__main__":
    D = json.load(open("/home/claude/kits/spr/discs_files.json"))
    G = json.load(open("/home/claude/kits/spr/G.json"))
    RZ90 = np.array([[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1.0]])
    out = {}
    for rel, d in sorted(D.items()):
        j, F, k = arm_fit(rel, d)
        out[rel] = dict(joint=j, fit=F.tolist(), scale=k)
    # compare with Josh
    for name, g in sorted(G.items()):
        rel = g["rel"]; j, F, k = out[rel]["joint"], np.array(out[rel]["fit"]), out[rel]["scale"]
        Gm = np.array(g["G"])
        if g.get("mirrored"):
            W_j = MX @ S_H @ Gm; W_r = S_L @ F           # Josh's right placement mirrored onto the left
        else:
            fixed = name.startswith(("patternP", "patternS"))
            W_j = S_H @ (RZ90 @ Gm if fixed else Gm); W_r = S_R @ F
        v, n, t = read_stl(U + rel); V = np.asarray(v, float)[::25] * k
        a = V @ W_j[:3, :3].T + W_j[:3, 3]; b = V @ W_r[:3, :3].T + W_r[:3, 3]
        dd = np.linalg.norm(a - b, axis=1)
        out[rel]["josh_dev"] = float(dd.max())
        print("%-32s %s  rule vs Josh: max %.3f mean %.3f%s" % (name, j, dd.max(), dd.mean(), "  (P/S turned 90)" if name.startswith(("patternP", "patternS")) and not g.get("mirrored") else ""))
    json.dump(out, open("/home/claude/kits/spr/arm_fits.json", "w"), indent=0)
    print(len(out), sum(1 for v in out.values() if v["joint"] == "Shoulder R"), "R")

import sys, json, numpy as np
sys.path.insert(0, "/home/claude/blend/forclaude"); sys.path.insert(0, "/home/claude/real"); sys.path.insert(0, "/home/claude/kits/cr"); sys.path.insert(0, "/home/claude/kits")
from stl_io import read_stl
import flats
U = "/mnt/user-data/uploads/new cults/Springles/"
h = json.load(open("heresy.json")); G = json.load(open("G.json"))
S_H = np.array(h["SOCK:23-Torso-2.001_socket_HeresyArms_r"]["mw"]); S_R = np.array(h["SOCK:23-Torso-2.001_socket_arm__Torso_r"]["mw"])
print("S_R o", S_R[:3, 3].round(3))
rows = []
for name, g in sorted(G.items()):
    v, n, t = read_stl(U + g["rel"]); V = np.asarray(v, float) * g["scale"]; T = np.asarray(t)
    M = S_H @ np.array(g["G"]); P = V @ M[:3, :3].T + M[:3, 3]
    if np.linalg.det(M[:3, :3]) < 0: T = T[:, ::-1]
    F = flats.flats(P, T, min_area=2.0)
    cand = [f for f in F if f[1][0] < -0.8 and np.linalg.norm(f[2] - S_R[:3, 3]) < 4]
    if not cand: print(name, "no disc"); continue
    A, nn, c, o, sel = max(cand, key=lambda f: f[0])
    d = c - S_R[:3, 3]
    print("%-32s area %5.1f n %s  c-S_R %s |%.2f|  ang %.1f" % (name, A, nn.round(3), d.round(2), np.linalg.norm(d), np.degrees(np.arccos(-nn[0]))))

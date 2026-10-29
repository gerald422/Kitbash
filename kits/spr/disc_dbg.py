import sys, json, numpy as np
sys.path.insert(0, "/home/claude/blend/forclaude"); sys.path.insert(0, "/home/claude/kits/cr"); sys.path.insert(0, "/home/claude/kits")
from stl_io import read_stl
import flats
U = "/mnt/user-data/uploads/new cults/Springles/"
h = json.load(open("heresy.json")); G = json.load(open("G.json"))
S_H = np.array(h["SOCK:23-Torso-2.001_socket_HeresyArms_r"]["mw"]); S_R = np.array(h["SOCK:23-Torso-2.001_socket_arm__Torso_r"]["mw"])
for name in sys.argv[1:]:
    g = G[name]
    v, n, t = read_stl(U + g["rel"]); V = np.asarray(v, float) * g["scale"]; T = np.asarray(t)
    M = S_H @ np.array(g["G"]); P = V @ M[:3, :3].T + M[:3, 3]
    print(name, "bbox", P.min(0).round(2), P.max(0).round(2))
    F = flats.flats(P, T, min_area=1.0)
    for A, nn, c, o, sel in F[:8]:
        print("   area %5.1f n %s c-S_R %s" % (A, nn.round(3), (c - S_R[:3, 3]).round(2)))

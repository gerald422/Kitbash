import sys, json, numpy as np
sys.path.insert(0, '/home/claude/kits/cr'); import stlcache
from addon_ns import ns
U = "/mnt/user-data/uploads/new cults/Springles/"
SCR = "/tmp/claude-0/-home-claude/3c0770af-36e9-58fc-b7f7-70184e2b5d36/scratchpad/"
for name in ["hand_grip", "hand_fore", "hand_pp"]:
    z = np.load(SCR + name + ".npz"); V, T = z["V"].astype(float), z["T"]
    N = ns["_vertex_normals"](V, T)
    for r in np.arange(0.9, 2.01, 0.1):
        f = ns["_spheres"](V, N, r, +1, cell=0.08, minvotes=30)
        for c, rr, on in f:
            print(name, "r try %.1f -> c %s r %.3f on %d" % (r, c.round(2), rr, on))

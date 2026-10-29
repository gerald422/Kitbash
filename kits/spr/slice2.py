import sys, json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, '/home/claude/real'); sys.path.insert(0, '/home/claude/kits/cr'); import fitlib as F, stlcache
from cuprule import cup
U = "/mnt/user-data/uploads/new cults/Springles/"
AF = json.load(open("arm_fits.json"))
rel = "patternC arms/tactical arms/patternC ranged Rarm 1.stl"; a = AF[rel]
V, T = stlcache.load(U + rel); V = V * a["scale"]; j = np.linalg.inv(np.array(a["fit"]))[:3, 3]
S = F.surf(V, T, 600000, 0); c = cup(V, T, j, S)
o, Y = c["origin"], c["Y"]; ax = -Y
u = np.cross(ax, [0, 0, 1.0]); u /= np.linalg.norm(u); w = np.cross(ax, u)
L = S - o; h = L @ ax; x = L @ u; y = L @ w
k = (np.abs(y) < 0.03) & (h > -3) & (h < 1) & (np.abs(x) < 3)
fig, axs = plt.subplots(1, 2, figsize=(12, 6))
axs[0].scatter(x[k], h[k], s=0.5); axs[0].set_aspect("equal"); axs[0].grid(True); axs[0].set_title("arm cup (scaled), section; lip plane h=0")
# hand peg (scaled 1.1)
SCR = "/tmp/claude-0/-home-claude/3c0770af-36e9-58fc-b7f7-70184e2b5d36/scratchpad/"
z = np.load(SCR + "hand_grip_big.npz"); Vh, Th = z["V"].astype(float) * 1.1, z["T"]
Sh = F.surf(Vh, Th, 400000, 0)
cc = np.array([-52.8, -63.25, 5.92]) * 1.1; a2 = np.array([-1.0, 0, 0])
u2 = np.array([0, 1.0, 0]); w2 = np.array([0, 0, 1.0])
L2 = Sh - cc; h2 = L2 @ a2; x2 = L2 @ w2; y2 = L2 @ u2
k2 = (np.abs(y2) < 0.03) & (h2 > -3) & (h2 < 1)
axs[1].scatter(x2[k2], h2[k2], s=0.5); axs[1].set_aspect("equal"); axs[1].grid(True); axs[1].set_title("hand peg (x1.1), section")
plt.savefig("rh3/cup_peg.png", dpi=90)

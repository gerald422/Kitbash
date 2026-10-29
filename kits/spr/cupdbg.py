import sys, json, numpy as np
sys.path.insert(0, '/home/claude/kits/cr'); sys.path.insert(0, '/home/claude/real')
import stlcache, fitlib as F
from addon_ns import ns
U = "/mnt/user-data/uploads/new cults/Springles/"
AF = json.load(open("arm_fits.json"))
rel = "patternC arms/tactical arms/patternC ranged Rarm 1.stl"; a = AF[rel]
V, T = stlcache.load(U + rel); V = V * a["scale"]; j = np.linalg.inv(np.array(a["fit"]))[:3, 3]
cen, n, ar = ns["_tri_info"](V, T); dist = np.linalg.norm(cen - j, axis=1); idx = np.where(dist > 0.55 * dist.max())[0]
S = F.surf(V, T, 200000, 0)
for g, nn, A in ns["_flat_patches"](V, T, cen, n, ar, idx, (1.0, 30.0)):
    c = (cen[g] * ar[g, None]).sum(0) / A; out = c - j
    L = S - c; h = L @ nn; lat = L - np.outer(h, nn); r = np.linalg.norm(lat, axis=1)
    lipk = (r > 1.25) & (r < 2.05) & (h > 0.05) & (h < 1.2); inside = (r < 1.15) & (h > 0.1) & (h < 3)
    print("A %5.2f d %.2f facing %.2f nn %s  lip %d inside %d" % (A, np.linalg.norm(out), out @ nn / np.linalg.norm(out), nn.round(2), lipk.sum(), inside.sum()))

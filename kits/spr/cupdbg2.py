import sys, json, numpy as np
from cuprule import *
AF = json.load(open("arm_fits.json"))
for rel in ["patternP arms/2 handed melee/patternP duel melee Larm 1.stl", "patternP arms/heavy weapons/patternP heavy Larm 4.stl"]:
    a = AF[rel]; V, T = stlcache.load(U + rel); V = V * a["scale"]; j = np.linalg.inv(np.array(a["fit"]))[:3, 3]
    cen, n, ar = ns["_tri_info"](V, T); dist = np.linalg.norm(cen - j, axis=1); idx = np.where(dist > 0.55 * dist.max())[0]
    print(rel, "maxdist %.2f" % dist.max())
    for g, nn, A in ns["_flat_patches"](V, T, cen, n, ar, idx, (0.3, 30.0)):
        c = (cen[g] * ar[g, None]).sum(0) / A; out = c - j
        f = out @ nn / np.linalg.norm(out)
        if f > 0.3: print("   A %5.2f d %.2f facing %.2f nn %s" % (A, np.linalg.norm(out), f, nn.round(2)))

import sys, numpy as np
sys.path.insert(0, "/home/claude/kitbash/kits/rw_spr"); from common import *
import flats
REL = RW + "Torso/Prime Techmarine torso (Flat Bottom).stl"
V, T = load(REL); print("bbox", V.min(0).round(2), V.max(0).round(2))
Fl = flats.flats(V, T, min_area=1.0)
for A, n, c, *rest in sorted(Fl, key=lambda f: -f[0])[:25]:
    print("area %6.2f  n %s  c %s" % (A, np.round(n, 2), np.round(c, 2)))

import sys, numpy as np
sys.path.insert(0, "/home/claude/kitbash/kits/pads"); from padfix import *; from padrule import F62, V62, T62; import sheet
Vt, Tt = prev(TOR); GREY, PUR, BLUE, TC = (0.8, 0.8, 0.76, 1), (0.75, 0.45, 0.85, 1), (0.45, 0.65, 0.88, 1), (0.6, 0.72, 0.88, 1)
by = {}
for r in R: by.setdefault(r["name"], r)
cells = []
for n in sys.argv[1].split("|"):
    r = by[n]; W = r.get("new", r["seat"])
    cells.append([(Vt, Tt, TC), (r["V"], r["T"], GREY), (xf(W @ F62, V62), T62, BLUE if "new" in r else PUR)])
sheet.render(cells, sys.argv[2], {"out": ((1, 0.3, 0.3), (0, 0, 1)), "top": ((0.3, 0.2, 1), (0, 1, 0)), "front": ((0.3, 1, 0.2), (0, 0, 1))}, cols=len(cells), px=360, cell=40.0, recentre=False)

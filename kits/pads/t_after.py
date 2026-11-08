import sys, random, numpy as np
sys.path.insert(0, "/home/claude/kitbash/kits/pads"); from padfix import *; from padrule import F62, V62, T62; import sheet
Vt, Tt = prev(TOR)
GREY, PUR, BLUE, TC = (0.8, 0.8, 0.76, 1), (0.75, 0.45, 0.85, 1), (0.45, 0.65, 0.88, 1), (0.6, 0.72, 0.88, 1)
mode = sys.argv[1]; rs = CHANGE
if mode == "sample": random.seed(int(sys.argv[3])); rs = random.sample(CHANGE, 24)
else: rs = [r for r in CHANGE if r["fam"].startswith(mode)]
cells = []
for r in rs:
    if sys.argv[4] == "pair": cells.append([(Vt, Tt, TC), (r["V"], r["T"], GREY), (xf(r["seat"] @ F62, V62), T62, PUR)])
    cells.append([(Vt, Tt, TC), (r["V"], r["T"], GREY), (xf(r["new"] @ F62, V62), T62, BLUE)])
sheet.render(cells, sys.argv[2], {"v": ((1, 0.6, 0.35), (0, 0, 1))}, cols=int(sys.argv[5]), px=int(sys.argv[6]), cell=34.0, recentre=True)
for i, r in enumerate(rs): print(i, r["name"])

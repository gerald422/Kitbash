import sys, json, numpy as np
sys.path.insert(0, "/home/claude/kitbash/kits/pads"); from kb import *; import sheet
NEW = {e["name"]: e for e in json.loads(open("/mnt/user-data/outputs/pads-2026-11-08/_builder/index.json", "rb").read())["parts"]}
TORn = "MarFil Techmarine - Chest"; Vt, Tt = prev(BY[TORn])
GREY, PUR, TC = (0.8, 0.8, 0.76, 1), (0.75, 0.45, 0.85, 1), (0.6, 0.72, 0.88, 1)
def build(ix, arm, pad, side):
    tor, a, p = ix[TORn], ix[arm], ix[pad]
    S = sock(tor, "Shoulder " + side) @ fit(a, "Shoulder " + side); Va, Ta = prev(BY[arm]); Vp, Tp = prev(BY[pad])
    F = fit(p, "Pad " + side)
    if F is None: F = conj(fit(p, "Pad R")); Vp = Vp * [-1, 1, 1]; Tp = Tp[:, ::-1]
    return [(Vt, Tt, TC), (xf(S, Va), Ta, GREY), (xf(S @ sock(a, "Pad " + side) @ F, Vp), Tp, PUR)]
cells = []
for ix in (BY, NEW):
    cells.append(build(ix, "MarFil Assault - Arm 7B R", "BBoosty Medusas Mortals - Shoulder Pad Studs", "R") + build(ix, "MarFil Intercessor - Arm 1 L", "BBoosty Medusas Mortals - Shoulder Pad Bolts", "L"))
sheet.render(cells, "/home/claude/work/pads/exba", {"front": ((0, 1, 0.3), (0, 0, 1)), "right": ((1, 0.35, 0.25), (0, 0, 1)), "left": ((-1, 0.35, 0.25), (0, 0, 1))}, cols=2, px=560, cell=36.0)

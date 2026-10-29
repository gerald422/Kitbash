import sys; sys.path.insert(0, '/home/claude/kits')
import geo, qr, ksheet, numpy as np
IV = "../Intercessors-V2/Intercessors-V2/Intercessors-Bits/RawSTL/Legs-Raw/"
rows = []
V3 = {"front": (0, 1, 0.1), "side": (1, 0, 0.05)}
row = []
for f in ("33-Legs-17.stl", "36-Legs-20.stl", "39-Legs-23.stl", "34-Legs-18.stl"):
    p = qr.run("lg" + f[:2], [(IV + f, np.eye(4), qr.GREY)], views=V3, out="/home/claude/kits/iv2/look", res=360)
    row += [(p[v], f"{f} {v}") for v in V3]
ksheet.sheet([row[:4], row[4:]], "/home/claude/kits/iv2/look8.png", cell=260)

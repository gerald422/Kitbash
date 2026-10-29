import sys; sys.path.insert(0, '/home/claude/kits')
import geo, qr, ksheet, numpy as np
IV = "../Intercessors-V2/Intercessors-V2/Intercessors-Bits/RawSTL/Legs-Raw/"
row = []
for f, c in (("33-Legs-17.stl", (6.5, 1.6, 5)), ("34-Legs-18.stl", (4.5, 3.5, 5.5)), ("36-Legs-20.stl", (8.9, 1.1, 5))):
    V3 = {"front": (0, 1, 0.1), "out": (1, 0, 0.05), "in": (-1, 0, 0.05)}
    p = qr.run("ank" + f[:2], [(IV + f, np.eye(4), qr.GREY)], views=V3, out="/home/claude/kits/iv2/look", res=400, centre=c, size=14)
    row += [(p[v], f"{f} {v}") for v in V3]
ksheet.sheet([row[:3], row[3:6], row[6:]], "/home/claude/kits/iv2/look9.png", cell=260)

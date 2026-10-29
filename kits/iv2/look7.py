import sys, json; sys.path.insert(0, '/home/claude/kits')
import geo, qr, ksheet, numpy as np
IV = "../Intercessors-V2/Intercessors-V2/Intercessors-Bits/RawSTL/"
SH = json.load(open('/home/claude/kits/iv2/shoulder_all.json'))
B = IV + "Bolter-Individual-Raw/"
rows = []
V3 = {"out": (1, 0, 0), "in": (-1, 0, 0), "front": (0, -1, 0), "back": (0, 1, 0)}
for nm, piece in [("g125", B + "125-Bolter-A-1-R.stl"), ("g131", B + "131-Bolter-A-2-Individual-R.stl"), ("g137", B + "137-Bolter-A-3-R.stl")]:
    G = np.array(SH[piece]['G']); c = G[:3, :3] @ np.array([5.568, 0.202, 31.949]) + G[:3, 3]
    items = [(piece, np.eye(4), (0.9, 0.58, 0.35, 1)), (IV + "Arms-Raw/57-Arm-1-R.stl", G, (0.45, 0.65, 0.88, 0.45))]
    p = qr.run(nm, items, views=V3, out="/home/claude/kits/iv2/look", res=420, centre=c, size=14)
    rows.append([(p[v], f"{nm} {v}") for v in V3])
    p = qr.run(nm + "a", [(piece, np.eye(4), (0.9, 0.58, 0.35, 1))], views=V3, out="/home/claude/kits/iv2/look", res=420, centre=c, size=14)
    rows.append([(p[v], f"{nm} alone {v}") for v in V3])
ksheet.sheet(rows, "/home/claude/kits/iv2/look7.png", cell=250)

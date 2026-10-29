import sys; sys.path.insert(0, '/home/claude/kits')
import geo, qr, ksheet, numpy as np
IV = "../Intercessors-V2/Intercessors-V2/Intercessors-Bits/RawSTL/"
B = "Bolter-Individual-Raw/"; BL = B + "Bolter-Individual-Left/"
rows = []
V3 = {"front": (0, -1, 0), "out": (1, 0, 0), "in": (-1, 0, 0), "top": (0, 0, 1)}
for nm, piece, ref, c in [("s125", B + "125-Bolter-A-1-R.stl", "Arms-Raw/57-Arm-1-R.stl", (6, 0.2, 32)), ("s131", B + "131-Bolter-A-2-Individual-R.stl", "Arms-Raw/57-Arm-1-R.stl", (6, 0.2, 32)),
                          ("s137", B + "137-Bolter-A-3-R.stl", "Arms-Raw/57-Arm-1-R.stl", (6, 0.2, 32)), ("s125L", BL + "125-Bolter-A-1-L.stl", "Arms-Raw/Arms-Left/57-Arm-1-L.stl", (-6, 0.2, 32)),
                          ("s188", "PlasmaIncinerator-Raw/188-PlasmaIncinerator-4-A-R.stl", "Arms-Raw/57-Arm-1-R.stl", (6, 0.2, 32))]:
    items = [(IV + "Chest-Raw/12-Chest-1.stl", np.eye(4), (0.8, 0.8, 0.76, 1)), (IV + ref, np.eye(4), (0.45, 0.65, 0.88, 0.55)), (IV + piece, np.eye(4), (0.9, 0.58, 0.35, 0.85))]
    p = qr.run(nm, items, views=V3, out="/home/claude/kits/iv2/look", res=420, centre=c, size=16)
    rows.append([(p[v], f"{nm} {v}") for v in V3])
ksheet.sheet(rows, "/home/claude/kits/iv2/look6.png", cell=260)

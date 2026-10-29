import sys; sys.path.insert(0, '/home/claude/kits')
import geo, qr, ksheet, numpy as np
IV = "../Intercessors-V2/Intercessors-V2/Intercessors-Bits/RawSTL/"
G, O, B, P = qr.GREY, qr.ORANGE, qr.BLUE, qr.PURPLE
BI = "Bolter-Individual-Raw/"; BL = BI + "Bolter-Individual-Left/"
ch = ("Chest-Raw/12-Chest-1.stl", G)
groups = {
 'p125': [ch, (BI + "125-Bolter-A-1-R.stl", O), (BL + "125-Bolter-A-1-L.stl", B)],
 'p131': [ch, (BI + "131-Bolter-A-2-Individual-R.stl", O), (BL + "131-Bolter-A-2-Individual-L.stl", B)],
 'p137': [ch, (BI + "137-Bolter-A-3-R.stl", O), (BL + "137-Bolter-A-3-L.stl", B)],
 'p144': [(BI + "144-Bolter-A-4-R.stl", O), (BL + "144-Bolter-A-4-L.stl", B)],
 'p151_158_165': [(BI + "151-Bolter-A-5-R.stl", O), (BI + "158-Bolter-A-6-R.stl", B), (BI + "165-Bolter-A-7-R.stl", P)],
 'arms': [ch, ("Arms-Raw/57-Arm-1-R.stl", O), ("Arms-Raw/58-Arm-2-R.stl", B), ("Arms-Raw/Arms-Left/59-Arm-3-L.stl", P), ("Arms-Raw/Arms-Left/60-Arm-4-L.stl", qr.GREEN)],
}
rows = []
V3 = {"front": (0, -1, 0), "side": (1, 0, 0), "top": (0, 0, 1)}
for g, items in groups.items():
    for rel, _ in items: geo.load(IV + rel)
    p = qr.run(g, [(IV + r, np.eye(4), c) for r, c in items], views=V3, out="/home/claude/kits/iv2/look", res=420)
    rows.append([(p[v], f"{g} {v}") for v in V3])
ksheet.sheet(rows, "/home/claude/kits/iv2/look2.png", cell=300)

import sys; sys.path.insert(0, '/home/claude/kits')
import geo, qr, ksheet, numpy as np
C = "ChaplainWithJumpPack (1)/ChaplainWithJumpPack/"
G, OR, B, P, GR = qr.GREY, qr.ORANGE, qr.BLUE, qr.PURPLE, qr.GREEN
groups = {
 'cjA': [(C + "Chest/Chest-Raw-STL/2-ChestChaplain.stl", G), (C + "Head/Head-Raw-STL/1-Head.stl", P), (C + "Legs/Legs-Raw-STL/3-Legs-A-ChaplainWithJumppack.stl", B), (C + "Jumppack/Jumppack-Raw-STL/11-Jumppack.stl", GR),
         (C + "Arms/Arms-Raw-STL/13-Arm-Right-A.stl", OR), (C + "Arms/Arms-Raw-STL/17-Arm-Left-A.stl", OR), (C + "Weapons/Weapons-Raw-STL/22-Crozius.stl", P), (C + "Weapons/Weapons-Raw-STL/21-AbsolvorPistol.stl", P), (C + "Rocks/Rocks-Raw-STL/29-Rock-A.stl", G)],
 'cjB': [(C + "Chest/Chest-Raw-STL/2-ChestChaplain.stl", G), (C + "Legs/Legs-Raw-STL/4-Legs-B-ChaplainWithJumppack.stl", B), (C + "Arms/Arms-Raw-STL/14-Arm-Right-B.stl", OR), (C + "Arms/Arms-Raw-STL/18-Arm-Left-B.stl", OR), (C + "Rocks/Rocks-Raw-STL/28-Rock-B.stl", G)],
 'cjCD': [(C + "Chest/Chest-Raw-STL/2-ChestChaplain.stl", G), (C + "Legs/Legs-Raw-STL/5-Legs-C-ChaplainWithJumppack.stl", B), (C + "Legs/Legs-Raw-STL/6-Legs-D-ChaplainWithJumppack.stl", P), (C + "Rocks/Rocks-Raw-STL/27-Rock-C.stl", G), (C + "Rocks/Rocks-Raw-STL/30-Rock-D.stl", GR)],
}
rows = []
V3 = {"front": (0, 1, 0.1), "side": (1, 0, 0.05), "top": (0, 0, 1)}
for g, items in groups.items():
    for rel, _ in items: geo.load(rel)
    p = qr.run(g, [(r, np.eye(4), c) for r, c in items], views=V3, out="/home/claude/kits/cj/look", res=420)
    rows.append([(p[v], f"{g} {v}") for v in V3])
ksheet.sheet(rows, "/home/claude/kits/cj/look1.png", cell=300)

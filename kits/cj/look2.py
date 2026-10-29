import sys; sys.path.insert(0, '/home/claude/kits')
import geo, qr, ksheet, json, numpy as np
C = "ChaplainWithJumpPack (1)/ChaplainWithJumpPack/"
PO = json.load(open('/home/claude/kits/cj/pose.json'))
G, OR, B, P, GR, RD = qr.GREY, qr.ORANGE, qr.BLUE, qr.PURPLE, qr.GREEN, qr.RED
I = np.eye(4)
rows = []
p = qr.run('jp', [(C + "Jumppack/Jumppack-Raw-STL/11-Jumppack.stl", I, G), (C + "Jumppack/Jumppack-Raw-STL/12-Exhaust.stl", I, RD)], views={"back": (0, -1, 0.2), "top": (0, 0, 1), "side": (1, 0, 0)}, out="/home/claude/kits/cj/look", res=420)
rows.append([(p[v], 'jump pack ' + v) for v in ("back", "top", "side")])
TORSO = [("Chest/Chest-Raw-STL/2-ChestChaplain.stl", G), ("Head/Head-Raw-STL/1-Head.stl", P), ("Jumppack/Jumppack-Raw-STL/11-Jumppack.stl", GR), ("Jumppack/Jumppack-Raw-STL/12-Exhaust.stl", RD),
         ("Accesories/Accesories-Raw-STL/23-Book.stl", RD), ("Accesories/Accesories-Raw-STL/24-Badge.stl", RD), ("Accesories/Accesories-Raw-STL/25-Holster.stl", RD), ("Accesories/Accesories-Raw-STL/26-Grenade.stl", RD)]
ARMS = {'A': ('13-Arm-Right-A', '17-Arm-Left-A'), 'B': ('14-Arm-Right-B', '18-Arm-Left-B'), 'C': ('15-Arm-Right-C', '19-Arm-Left-C'), 'D': ('16-Arm-Right-D', '20-Arm-Left-D')}
ROCK = {'A': '29-Rock-A', 'B': '28-Rock-B', 'C': '27-Rock-C', 'D': '30-Rock-D'}
for X, pp in PO.items():
    Px = np.array(pp['P'])
    items = [(pp['legs'], I, B), (C + 'Rocks/Rocks-Raw-STL/' + ROCK[X] + '.stl', I, G)]
    items += [(C + r, Px, c) for r, c in TORSO]
    items += [(C + 'Arms/Arms-Raw-STL/' + a + '.stl', I, OR) for a in ARMS[X]]
    if X == 'A': items += [(C + "Weapons/Weapons-Raw-STL/22-Crozius.stl", I, P), (C + "Weapons/Weapons-Raw-STL/21-AbsolvorPistol.stl", I, P)]
    for r, _, _ in items: geo.load(r)
    p = qr.run('pose' + X, items, views={"front": (0, 1, 0.1), "side": (1, 0, 0.05), "back": (0, -1, 0.1)}, out="/home/claude/kits/cj/look", res=420)
    rows.append([(p[v], f"pose {X} {v}") for v in ("front", "side", "back")])
ksheet.sheet(rows, "/home/claude/kits/cj/look2.png", cell=300)

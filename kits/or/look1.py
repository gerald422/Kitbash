import sys; sys.path.insert(0, '/home/claude/kits')
import geo, qr, ksheet, numpy as np
O = "Outriders (1)/Outriders/"
G, OR, B, P, GR = qr.GREY, qr.ORANGE, qr.BLUE, qr.PURPLE, qr.GREEN
bike = [(O + "Bike/RawSTL/" + f, G) for f in ("19-Body-1.stl", "21-Body-2.stl", "22-FrontWing.stl", "23-FrontWheel.stl", "24-RearWheel.stl", "25-ExhaustRight.stl", "26-ExhaustLeft.stl", "29-HandleRight.stl", "30-HandleLeft.stl")]
groups = {
 'rider_A': bike + [(O + "Legs/RawSTL/1-Legs-A.stl", B), (O + "Arms(WithHandles)/RawSTL(Right)/7-ArmWithHandle-Right-A.stl", OR), (O + "Arms(WithHandles)/RawSTL-Mirrored(Left)/7-ArmWightHandle-Left-A-1.stl", P), (O + "Torsos/RawSTL/1-Torso-A.stl", GR)],
 'rider_B': bike + [(O + "Legs/RawSTL/2-Legs-B.stl", B), (O + "Arms(WithHandles)/RawSTL(Right)/8-ArmWithHandle-Right-B.stl", OR), (O + "Arms/RawSTL-Mirrored-(Left)/14-Arm-2-Mirrored-A.stl", P)],
 'rider_Bm': bike + [(O + "Legs/MirroredRawSTL/2-Legs-B-Mirrored.stl", B), (O + "Arms(WithHandles)/RawSTL-Mirrored(Left)/8-ArmWightHandle-Left-B-1.stl", OR), (O + "Arms/RawSTL(Right)/14-Arm-2.stl", P)],
}
rows = []
V3 = {"side": (0, -1, 0.2), "front": (1, 0, 0.2), "top": (0, 0, 1)}
for g, items in groups.items():
    for rel, _ in items: geo.load(rel)
    p = qr.run(g, [(r, np.eye(4), c) for r, c in items], views=V3, out="/home/claude/kits/or/look", res=420)
    rows.append([(p[v], f"{g} {v}") for v in V3])
ksheet.sheet(rows, "/home/claude/kits/or/look1.png", cell=300)

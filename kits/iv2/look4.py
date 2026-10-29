import sys; sys.path.insert(0, '/home/claude/kits')
import geo, qr, ksheet, numpy as np
IV = "../Intercessors-V2/Intercessors-V2/Intercessors-Bits/RawSTL/"
items = [(IV + "Hands-Raw/282-Hand-10-R.stl", np.eye(4), (0.9, 0.58, 0.35, 1)), (IV + "Hands-Raw/274-Hand-2-R.stl", np.eye(4), (0.3, 0.5, 0.95, 0.5))]
for r, _, _ in items: geo.load(r)
V3 = {"front": (0, -1, 0), "side": (1, 0, 0), "top": (0, 0, 1), "back": (0, 1, 0.3)}
p = qr.run("h282", items, views=V3, out="/home/claude/kits/iv2/look", res=500, centre=(0, 0, 2), size=16)
ksheet.sheet([[(p[v], v) for v in V3]], "/home/claude/kits/iv2/look4.png", cell=300)

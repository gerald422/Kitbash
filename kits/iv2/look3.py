import sys; sys.path.insert(0, '/home/claude/kits')
import geo, qr, ksheet, numpy as np
IV = "../Intercessors-V2/Intercessors-V2/Intercessors-Bits/RawSTL/"
items = [(IV + "Bolter-Individual-Raw/165-Bolter-A-7-R.stl", np.eye(4), (0.9, 0.58, 0.35, 0.55)), (IV + "Hands-Raw/280-Hand-8-R.stl", np.eye(4), (0.3, 0.5, 0.95, 1))]
V3 = {"front": (0, -1, 0), "back": (0, 1, 0), "side": (1, 0, 0), "oside": (-1, 0, 0), "top": (0, 0, 1), "bottom": (0, 0, -1)}
p = qr.run("b165_h280", items, views=V3, out="/home/claude/kits/iv2/look", res=500, centre=(0, 0, 0), size=34)
ksheet.sheet([[(p[v], v) for v in list(V3)[:3]], [(p[v], v) for v in list(V3)[3:]]], "/home/claude/kits/iv2/look3.png", cell=330)

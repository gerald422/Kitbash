import sys; sys.path.insert(0, '/home/claude/kits')
import geo, qr, ksheet, numpy as np
O = "Techmarine (2)/Techmarine/"
I = np.eye(4); rows = []
for n in ('29-ExtensibleArm-1', '30-ExtensibleArm-2', '31-ExtensibleArm-3', '32-ExtensibleArm-4'):
    its = [(O + "Backpack/Backpack-Raw-STL/11-Techmarine-Backpack.stl", I, qr.BLUE), (O + "ExtensibleArms/ExtensibleArm-Raw-STL/" + n + ".stl", I, qr.ORANGE)]
    p = qr.run('tm3_' + n[:2], its, views={"back": (0, -1, 0.1), "below": (0, -0.3, -1), "right": (1, 0, 0.1), "q": (0.6, -0.6, -0.3)}, out="/home/claude/kits/tm/look", res=420, centre=(3, -8, 32), size=30)
    rows.append([(p[v], n[:2] + ' ' + v) for v in ("back", "below", "right", "q")])
ksheet.sheet(rows, "/home/claude/kits/tm/look3.png", cell=260)

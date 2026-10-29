import sys; sys.path.insert(0, '/home/claude/kits')
import geo, qr, ksheet, numpy as np
O = "Techmarine (2)/Techmarine/"
I = np.eye(4)
base = [(O + "Chest/Chest-Raw-STL/2-Chest.stl", qr.GREY), (O + "Backpack/Backpack-Raw-STL/11-Techmarine-Backpack.stl", qr.BLUE)]
rows = []
for nm, items in (('servo', [(O + "MechanicArms/MechanicArm-Raw-STL/24-MechanicArm-1.stl", qr.ORANGE), (O + "MechanicArms/MechanicArm-Raw-STL/26-MechanicArm-3.stl", qr.GREEN), (O + "MechanicArms/MechanicArm-Raw-STL/28-MechanicArm-5.stl", qr.PURPLE)]),
                  ('mech', [(O + "ExtensibleArms/ExtensibleArm-Raw-STL/29-ExtensibleArm-1.stl", qr.ORANGE), (O + "ExtensibleArms/ExtensibleArm-Raw-STL/30-ExtensibleArm-2.stl", qr.GREEN), (O + "ExtensibleArms/ExtensibleArm-Raw-STL/31-ExtensibleArm-3.stl", qr.PURPLE), (O + "ExtensibleArms/ExtensibleArm-Raw-STL/32-ExtensibleArm-4.stl", qr.RED)]),
                  ('guns', [(O + "Weapons/Weapons-Raw-STL/36-ForgeBolter.stl", qr.ORANGE), (O + "DoubleArms/DoubleArms-Raw-STL/22-DoubleArm-2.stl", qr.GREEN), (O + "DoubleArms/DoubleArms-Raw-STL/23-DoubleArm-2-Cable.stl", qr.PURPLE)])):
    its = [(r, I, c) for r, c in base + items]
    for r, _, _ in its: geo.load(r)
    p = qr.run('tm_' + nm, its, views={"back": (0, -1, 0.15), "left": (-1, 0, 0.1), "top": (0, 0.01, 1), "q": (-0.6, -0.6, 0.4)}, out="/home/claude/kits/tm/look", res=420)
    rows.append([(p[v], nm + ' ' + v) for v in ("back", "left", "top", "q")])
ksheet.sheet(rows, "/home/claude/kits/tm/look1.png", cell=260)

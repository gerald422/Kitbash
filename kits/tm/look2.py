import sys; sys.path.insert(0, '/home/claude/kits')
import geo, qr, ksheet, numpy as np
O = "Techmarine (2)/Techmarine/"
I = np.eye(4)
rows = []
for nm, items in (('pack', [(O + "Backpack/Backpack-Raw-STL/11-Techmarine-Backpack.stl", qr.BLUE)]),
                  ('s26', [(O + "Backpack/Backpack-Raw-STL/11-Techmarine-Backpack.stl", qr.BLUE), (O + "MechanicArms/MechanicArm-Raw-STL/26-MechanicArm-3.stl", qr.ORANGE)]),
                  ('s28', [(O + "Backpack/Backpack-Raw-STL/11-Techmarine-Backpack.stl", qr.BLUE), (O + "MechanicArms/MechanicArm-Raw-STL/28-MechanicArm-5.stl", qr.ORANGE)])):
    p = qr.run('tm2_' + nm, [(r, I, c) for r, c in items], views={"back": (0, -1, 0.1), "left": (-1, 0, 0.1), "top": (0, -0.01, 1), "right": (1, 0, 0.1)}, out="/home/claude/kits/tm/look", res=520,
               centre=(-3, -8, 36), size=34 if nm != 'pack' else 26)
    rows.append([(p[v], nm + ' ' + v) for v in ("back", "left", "top", "right")])
ksheet.sheet(rows, "/home/claude/kits/tm/look2.png", cell=300)

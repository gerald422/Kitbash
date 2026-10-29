import sys; sys.path.insert(0, '/home/claude/kits')
import geo, qr, ksheet, numpy as np, glob, os
O = "Outriders (1)/Outriders/Accesories/"
fs = sorted(glob.glob(geo.U + O + 'AccesoriesRawSTL/*.stl')) + sorted(glob.glob(geo.U + O + 'AccesoriesRawSTL-Mirrored/*.stl'))
rows = []
V3 = {"+y": (0, 1, 0.0001), "-y": (0, -1, 0.0001), "+x": (1, 0, 0.0001), "+z": (0, 0.0001, 1)}
for f in fs:
    rel = f[len(geo.U):]; geo.load(rel)
    p = qr.run('acc_' + os.path.basename(f)[:-4], [(rel, np.eye(4), qr.ORANGE)], views=V3, out="/home/claude/kits/or/look", res=300)
    rows.append([(p[v], os.path.basename(f)[:-4][:14] + ' ' + v) for v in V3])
ksheet.sheet(rows[:5], "/home/claude/kits/or/look_acc1.png", cell=200); ksheet.sheet(rows[5:], "/home/claude/kits/or/look_acc2.png", cell=200)

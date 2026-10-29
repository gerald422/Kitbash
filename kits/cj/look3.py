import sys; sys.path.insert(0, '/home/claude/kits')
import geo, qr, ksheet, numpy as np
C = "ChaplainWithJumpPack (1)/ChaplainWithJumpPack/"
rows = []
for a in ('17-Arm-Left-A', '18-Arm-Left-B', '13-Arm-Right-A'):
    p = qr.run('arm' + a[:2], [(C + 'Arms/Arms-Raw-STL/' + a + '.stl', np.eye(4), qr.ORANGE)], views={"front": (0, 1, 0.1), "end": (0.2, 1, 0.2), "side": (-1, 0, 0.05), "top": (0, 0, 1)}, out="/home/claude/kits/cj/look", res=400)
    rows.append([(p[v], a + ' ' + v) for v in ("front", "end", "side", "top")])
ksheet.sheet(rows, "/home/claude/kits/cj/look3.png", cell=260)

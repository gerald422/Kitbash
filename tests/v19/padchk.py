import sys, json, numpy as np, os
sys.path.insert(0, '/home/claude/kits')
import qr, ksheet
res = json.load(open(sys.argv[1]))
src = open('/home/claude/tiow_blender/tiow_inbox.py').read()
import re, zlib, base64
i = src.index('_REFS_PACKED = ('); j = src.index(')', i)
ref = json.loads(zlib.decompress(base64.b64decode("".join(re.findall(r'"([^"]*)"', src[i:j+1])))))['Pad'][0]
PTS = np.array(ref['points']).reshape(3, 3)
F = json.load(open('/home/claude/test/kitlib/All Mar All the time/AssaultMarines-V2/AssaultMarines-V2/RawSTL/ShoulderPads/_fits.json'))
fitR = np.array(F['Pad R']['m']).reshape(4, 4)
MX = np.diag([-1.0, 1, 1, 1])
PAD = 'AssaultMarines-V2/AssaultMarines-V2/RawSTL/ShoulderPads/62-ShoulderPad-1.stl'
rows = []
for rel, r in res.items():
    if len(sys.argv) > 3 and not any(k in rel for k in sys.argv[3].split(',')): continue
    sd = r['side']; R = np.array(r['R']); t = np.array(r['t'])
    P = PTS * ([-1, 1, 1] if sd == 'L' else 1)
    a, b, c = P @ R.T + t
    y = (b - a) / np.linalg.norm(b - a); mid = (a + b) / 2; off = (c - mid) - y * ((c - mid) @ y); z = off / np.linalg.norm(off); x = np.cross(y, z)
    if x[0] * (1 if sd == 'R' else -1) < 0: x, y = -x, -y
    A = np.eye(4); A[:3, 0], A[:3, 1], A[:3, 2], A[:3, 3] = x, y, z, c
    padM = A @ fitR if sd == 'R' else A @ (MX @ fitR @ MX) @ MX
    p = qr.run('padchk_' + os.path.basename(rel)[:-4], [(rel, np.eye(4), qr.GREY), (PAD, padM, qr.ORANGE)], views={'front': (0, 1, 0.2), 'side': (1 if sd == 'R' else -1, 0, 0.2)}, res=360, centre=c, size=22)
    rows.append([(p['front'], '%s %.3f' % (os.path.basename(rel)[:-4], r['full'])), (p['side'], 'side')])
R2 = [rows[k] + (rows[k + 1] if k + 1 < len(rows) else []) for k in range(0, len(rows), 2)]
ksheet.sheet(R2, sys.argv[2], 260, 'Pauldron 62 on the copied Pad anchor (staged full-swing match)')

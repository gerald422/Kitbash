"""Shoulder disc (the flat round inner face of the shoulder) on each Intercessor arm piece: centre, normal, radius."""
import sys, json, os, glob
import numpy as np, importlib.util
spec = importlib.util.spec_from_file_location('ti', '/home/claude/tiow_blender/tiow_inbox.py'); T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
NC = "/mnt/user-data/uploads/new cults/"; IV = "Intercessors-V2/Intercessors-V2/Intercessors-Bits/RawSTL/"
J = np.array([5.568, 0.202, 31.949])
def disc(path, side):
    V, Tr = T.read_stl_np(path); V = np.asarray(V, float); Tr = np.asarray(Tr)
    inward = np.array([-1.0, 0, 0]) if side == 'R' else np.array([1.0, 0, 0])
    cen, n, a = T._tri_info(V, Tr)
    idx = np.where(n @ inward > 0.6)[0]
    best = []
    for g, nn, A in T._flat_patches(V, Tr, cen, n, a, idx, (6.0, 80.0)):
        if nn @ inward < 0.6: continue
        c, r, B = T._face_circle(V, Tr, g, nn)
        rim = B - c; rim = np.linalg.norm(rim - (rim @ nn)[:, None] * nn, axis=1)
        best.append((A, c, nn, r, float(rim.std() / max(r, 1e-6))))
    best.sort(key=lambda x: -x[0])
    return best[:4]
paths = [(IV + "Arms-Raw/" + f, 'R') for f in ("57-Arm-1-R.stl", "58-Arm-2-R.stl", "62-Arm-6-R.stl")] + [(IV + "Arms-Raw/Arms-Left/57-Arm-1-L.stl", 'L')]
SH = json.load(open('/home/claude/kits/iv2/shoulder_all.json'))
for k, v in SH.items():
    if 'Arms-Raw' in k: continue
    paths.append((k[3:], v['side']))
out = {}
for rel, side in paths:
    d = disc(NC + rel, side)
    if not d: print('%-44s %s  NO DISC' % (rel.split('/')[-1], side)); continue
    A, c, nn, r, rs = d[0]
    out[rel] = {'c': c.tolist(), 'n': nn.tolist(), 'r': r, 'area': A, 'side': side, 'others': [(x[0], x[1].tolist(), x[3]) for x in d[1:]]}
    jj = J * ([1, 1, 1] if side == 'R' else [-1, 1, 1])
    print('%-44s %s  area %5.1f r %.2f rimdev %.2f  c-J %s  n %s  next %s' % (rel.split('/')[-1], side, A, r, rs, np.round(c - jj, 2), np.round(nn, 2), [round(x[0], 1) for x in d[1:]]), flush=True)
json.dump(out, open('/home/claude/kits/iv2/discs.json', 'w'), indent=1)

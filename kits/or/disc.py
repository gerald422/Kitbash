import sys, json, os, glob
import numpy as np, importlib.util
spec = importlib.util.spec_from_file_location('ti', '/home/claude/tiow_blender/tiow_inbox.py'); T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
U = "/mnt/user-data/uploads/new cults/All Mar All the time/"; O = "Outriders (1)/Outriders/"
def discs(path, side):
    V, Tr = T.read_stl_np(path); V = np.asarray(V, float); Tr = np.asarray(Tr)
    cen, n, a = T._tri_info(V, Tr)
    out = []
    for g, nn, A in T._flat_patches(V, Tr, cen, n, a, np.arange(len(Tr)), (8.0, 22.0)):
        c, r, B = T._face_circle(V, Tr, g, nn)
        rim = B - c; rim = np.linalg.norm(rim - (rim @ nn)[:, None] * nn, axis=1); rd = float(rim.std() / max(r, 1e-6))
        if 1.9 <= r <= 2.7 and rd < 0.2: out.append((A, c, nn, r, rd))
    out.sort(key=lambda x: x[4]); return out
res = {}
files = [(f, 'R') for f in sorted(glob.glob(U + O + "Arms/RawSTL(Right)/*.stl")) + sorted(glob.glob(U + O + "Arms(WithHandles)/RawSTL(Right)/*.stl"))]
files += [(f, 'L') for f in sorted(glob.glob(U + O + "Arms/RawSTL-Mirrored-(Left)/*.stl")) + sorted(glob.glob(U + O + "Arms(WithHandles)/RawSTL-Mirrored(Left)/*.stl"))]
for f, side in files:
    d = discs(f, side)
    rel = f[len(U):]
    res[rel] = [{'c': x[1].tolist(), 'n': x[2].tolist(), 'r': x[3], 'rd': x[4], 'area': x[0]} for x in d]
    print('%-40s %s ' % (os.path.basename(f), side) + ' | '.join('a %.1f r %.2f rd %.2f c %s n %s' % (x[0], x[3], x[4], np.round(x[1], 2), np.round(x[2], 2)) for x in d[:3]), flush=True)
json.dump(res, open('/home/claude/kits/or/discs.json', 'w'), indent=1)

import bpy, sys, json, glob, os
import numpy as np
import importlib.util
spec = importlib.util.spec_from_file_location('ti', '/home/claude/tiow_blender/tiow_inbox.py'); T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
RAW = '/home/claude/raw/'
P = json.load(open('/home/claude/kits/amv2_partial.json'))['side']
files = [r for r, d in P.items() if d.get('category') == 'Arms'] + [f[len(RAW):] for f in glob.glob(RAW + 'VeteranSquad/VeteranSquad/Arms/*/*.stl')]
for rel in sorted(files)[::1]:
    V, Tr = T.read_stl_np(RAW + rel); d = P.get(rel, {})
    sh = [k for k in d.get('fits', {}) if k.startswith('Shoulder')]
    sd = sh[0][-1] if sh else ('L' if 'Mirrored' in rel else 'R')
    joint = np.linalg.inv(np.array(d['fits'][sh[0]]).reshape(4, 4))[:3, 3] if sh else np.array([5.48 * (1 if sd == 'R' else -1), 0.2, 31.95])
    Vs, Ts, js = (V * [-1.0, 1, 1], Tr[:, ::-1], joint * [-1.0, 1, 1]) if sd == 'L' else (V, Tr, joint)
    cen, n, a = T._tri_info(Vs, Ts); dist = np.linalg.norm(cen - js, axis=1); idx = np.where(dist > 0.55 * dist.max())[0]
    cand = []
    for g, nn, A in T._flat_patches(Vs, Ts, cen, n, a, idx, (3.0, 25.0)):
        c = (cen[g] * a[g, None]).sum(0) / A; out = c - js
        if out @ nn >= 0.3 * np.linalg.norm(out): cand.append((float(np.linalg.norm(out)), g, nn, A))
    if not cand: print('%-40s NO FACE' % os.path.basename(rel)); continue
    _d, g, nn, A = max(cand, key=lambda x: x[0])
    o, r, B = T._face_circle(Vs, Ts, g, nn)
    rr = np.linalg.norm((B - o) - ((B - o) @ nn)[:, None] * nn, axis=1)
    print('%-40s area %5.1f r %.2f  roundness %.3f  fill %.2f' % (os.path.basename(rel), A, r, rr.std() / r, A / (np.pi * r * r)))

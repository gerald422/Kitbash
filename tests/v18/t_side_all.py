import bpy, sys, json, time, os
import numpy as np
import importlib.util
spec = importlib.util.spec_from_file_location('ti', '/home/claude/tiow_blender/tiow_inbox.py'); T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
RAW = '/home/claude/raw/'
P = json.load(open('/home/claude/kits/amv2_partial.json'))['side']
files = sorted(r for r, d in P.items() if d.get('category') in ('Melee', 'Pistols', 'Shields'))
import glob
files += [f[len(RAW):] for f in sorted(glob.glob(RAW + 'VeteranSquad/VeteranSquad/Melee/*/*.stl')) if 'PowerFist' not in f]
wrong = 0; margins = []
for rel in files:
    sd = 'L' if ('Left' in rel or 'Mirrored' in rel) else 'R'
    V, Tr = T.read_stl_np(RAW + rel); caps = T.hand_caps(V, Tr); near = T._bvh_nearest(V, Tr)
    m = {s: T.hand_wrist_frame(V, Tr, s, near, caps)[1] for s in 'RL'}
    pick = min(m, key=m.get); wrong += pick != sd; margins.append(m['L' if sd == 'R' else 'R'] / m[sd])
    print('%-38s true %s  full R %.3f L %.3f -> %s %s' % (os.path.basename(rel), sd, m['R'], m['L'], pick, '' if pick == sd else 'WRONG'), flush=True)
print('wrong', wrong, 'of', len(files), ' smallest ratio wrong/right %.2f' % min(margins))

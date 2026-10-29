import bpy, sys, json, time, os
import numpy as np
import importlib.util
spec = importlib.util.spec_from_file_location('ti', '/home/claude/tiow_blender/tiow_inbox.py'); T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
RAW = '/home/claude/raw/'
P = json.load(open('/home/claude/kits/amv2_partial.json'))['side']
out = {}
files = sorted(r for r, d in P.items() if d.get('category') in ('Melee', 'Pistols', 'Shields'))
for rel in files:
    sd = 'L' if 'Left' in rel else 'R'
    Hj = np.linalg.inv(np.array(P[rel]['fits']['Hand ' + sd]).reshape(4, 4))
    V, Tr = T.read_stl_np(RAW + rel); t = time.time()
    M, med = T.hand_wrist_frame(V, Tr, sd); dt = time.time() - t
    dy = np.degrees(np.arccos(np.clip(M[:3, 1] @ Hj[:3, 1], -1, 1)))
    dz = np.degrees(np.arctan2(M[:3, 2] @ Hj[:3, 0], M[:3, 2] @ Hj[:3, 2]))
    out[rel] = dict(M=M.tolist(), med=med, dt=dt)
    print('%-36s med %.3f axis %4.1f roll %+5.1f  %.1fs' % (os.path.basename(rel), med, dy, dz, dt), flush=True)
json.dump(out, open('/home/claude/kits/handrule_addon.json', 'w'))
r = np.array([[v['dt']] for v in out.values()]); print('time median %.1f max %.1f' % (np.median(r), r.max()))

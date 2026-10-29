import bpy, sys, json, time, os
import numpy as np
import importlib.util
spec = importlib.util.spec_from_file_location('ti', '/home/claude/tiow_blender/tiow_inbox.py'); T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
RAW = '/home/claude/raw/'
H = json.load(open('/home/claude/kits/handrule_addon.json'))
def ang(R): return np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1)))
for rel in list(H)[::9]:
    sd = 'L' if 'Left' in rel else 'R'
    V, Tr = T.read_stl_np(RAW + rel); t = time.time()
    M, med = T.hand_wrist_frame(V, Tr, sd); dt = time.time() - t
    Mp = np.array(H[rel]['M'])
    t = time.time(); caps = T.hand_caps(V, Tr); near = T._bvh_nearest(V, Tr)
    q = {s: T.hand_wrist_frame(V, Tr, s, near, caps, quick=True)[1] for s in 'RL'}; dq = time.time() - t
    print('%-36s vs before %.2f deg %.3f mm  %.1fs (was %.1fs)  quick R %.3f L %.3f -> %s (%.1fs)' % (os.path.basename(rel), ang(M[:3,:3].T @ Mp[:3,:3]), np.linalg.norm(M[:3,3]-Mp[:3,3]), dt, H[rel]['dt'], q['R'], q['L'], min(q, key=q.get), dq))

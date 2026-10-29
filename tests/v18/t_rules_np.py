"""The add-on's wrist rules on raw meshes vs the prototype results."""
import bpy, sys, json, time, os
import numpy as np
sys.path.insert(0, '/home/claude/tiow_blender')
import importlib.util
spec = importlib.util.spec_from_file_location('ti', '/home/claude/tiow_blender/tiow_inbox.py'); T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
sys.path.insert(0, '/home/claude/kits')
RAW = '/home/claude/raw/'
A = json.load(open('/home/claude/kits/armrule_res.json')); H = json.load(open('/home/claude/kits/handrule_res.json')); VS = json.load(open('/home/claude/kits/vs_rules.json'))
P = json.load(open('/home/claude/kits/amv2_partial.json'))['side']
def ang(R): return np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1)))
def cmp(M, Mp): return ang(M[:3, :3].T @ Mp[:3, :3]), np.linalg.norm(M[:3, 3] - Mp[:3, 3])
pick = int(sys.argv[-1]) if sys.argv[-1].isdigit() else 6
arms = list(A.items())[::max(1, len(A) // pick)] + list(VS['arms'].items())[::3]
for rel, r in arms:
    V, Tr = T.read_stl_np(RAW + rel)
    sd = r['side']
    if rel in P:
        sh = [k for k in P[rel]['fits'] if k.startswith('Shoulder')]
        joint = np.linalg.inv(np.array(P[rel]['fits'][sh[0]]).reshape(4, 4))[:3, 3]
    else:
        joint = np.array([5.48 * (1 if sd == 'R' else -1), 0.2, 31.95])
    t = time.time(); M = T.arm_wrist_frame(V, Tr, joint, sd); dt = time.time() - t
    a, d = cmp(M, np.array(r['M']))
    print('ARM  %-34s %s  vs prototype %.2f deg %.3f mm  det %+.0f  %.1fs' % (os.path.basename(rel), sd, a, d, np.linalg.det(M[:3, :3]), dt))
hands = list(H.items())[::max(1, len(H) // pick)] + list(VS['hands'].items())[::4]
for rel, r in hands:
    V, Tr = T.read_stl_np(RAW + rel)
    sd = r.get('side') or ('L' if 'Left' in rel else 'R')
    t = time.time(); M, med = T.hand_wrist_frame(V, Tr, sd); dt = time.time() - t
    a, d = cmp(M, np.array(r['M']))
    print('HAND %-34s %s  vs prototype %.2f deg %.3f mm  fist %.3f (proto %.3f) det %+.0f  %.1fs' % (os.path.basename(rel), sd, a, d, med, r['med'], np.linalg.det(M[:3, :3]), dt))

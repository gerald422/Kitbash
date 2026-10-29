import sys, json, os
import numpy as np, importlib.util
spec = importlib.util.spec_from_file_location('ti', '/home/claude/tiow_blender/tiow_inbox.py'); T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
U = "/mnt/user-data/uploads/new cults/All Mar All the time/"; O = "ChaplainWithJumpPack (1)/ChaplainWithJumpPack/"
D = json.load(open('/home/claude/kits/cj/discs.json'))
inv = np.linalg.inv
out = {'arms': {}, 'weapons': {}}
for a in sorted(D):
    side = 'L' if '-Left-' in a else 'R'
    V, Tr = T.read_stl_np(U + a)
    M = T.arm_wrist_frame(np.asarray(V, float), np.asarray(Tr), np.array(D[a][0]['c']), side)
    out['arms'][a] = None if M is None else np.asarray(M).tolist()
    print(os.path.basename(a), side, None if M is None else np.round(np.asarray(M)[:3, 3], 2), flush=True)
for w in ('Weapons/Weapons-Raw-STL/21-AbsolvorPistol.stl', 'Weapons/Weapons-Raw-STL/22-Crozius.stl'):
    V, Tr = T.read_stl_np(U + O + w); V = np.asarray(V, float); Tr = np.asarray(Tr)
    caps = T.hand_caps(V, Tr); near = T._bvh_nearest(V, Tr)
    for s in ('R', 'L'):
        M, md = T.hand_wrist_frame(V, Tr, s, near, caps)
        out['weapons'][O + w + '|' + s] = None if M is None else {'M': np.asarray(M).tolist(), 'med': md}
        print(os.path.basename(w), s, md, None if M is None else np.round(np.asarray(M)[:3, 3], 2), flush=True)
json.dump(out, open('/home/claude/kits/cj/wrist.json', 'w'), indent=1)

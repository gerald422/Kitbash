import sys, json, os, glob
import numpy as np, importlib.util
spec = importlib.util.spec_from_file_location('ti', '/home/claude/tiow_blender/tiow_inbox.py'); T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
U = "/mnt/user-data/uploads/new cults/All Mar All the time/"; O = "Outriders (1)/Outriders/"
out = {}
files = [(f, 'R') for f in sorted(glob.glob(U + O + 'Weapons/WeaponsRawSTL(Right)/*.stl')) if 'NoHand' not in f]
files += [(f, 'L') for f in sorted(glob.glob(U + O + 'Weapons/WeaponsRawSTLMirrored(Left)/*.stl'))]
for f, sd in files:
    V, Tr = T.read_stl_np(f); V = np.asarray(V, float); Tr = np.asarray(Tr)
    caps = T.hand_caps(V, Tr); near = T._bvh_nearest(V, Tr)
    r = {}
    for s in ('R', 'L'):
        M, md = T.hand_wrist_frame(V, Tr, s, near, caps)
        r[s] = None if M is None else {'M': np.asarray(M).tolist(), 'med': md}
    out[f[len(U):]] = r
    print('%-34s %s  R %s  L %s  o %s' % (os.path.basename(f)[:34], sd, None if r['R'] is None else round(r['R']['med'], 3), None if r['L'] is None else round(r['L']['med'], 3),
          None if r[sd] is None else np.round(np.array(r[sd]['M'])[:3, 3], 2)), flush=True)
json.dump(out, open('/home/claude/kits/or/hands.json', 'w'), indent=1)

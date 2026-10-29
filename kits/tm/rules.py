import sys, json, os, glob
import numpy as np, importlib.util
spec = importlib.util.spec_from_file_location('ti', '/home/claude/tiow_blender/tiow_inbox.py'); T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
U = "/mnt/user-data/uploads/new cults/All Mar All the time/"; O = "Techmarine (2)/Techmarine/"
out = {'discs': {}, 'wrists': {}, 'hands': {}}
def discs(V, Tr):
    cen, n, a = T._tri_info(V, Tr); res = []
    for g, nn, A in T._flat_patches(V, Tr, cen, n, a, np.arange(len(Tr)), (8.0, 22.0)):
        c, r, B = T._face_circle(V, Tr, g, nn); rim = B - c; rim = np.linalg.norm(rim - (rim @ nn)[:, None] * nn, axis=1); rd = rim.std() / r
        if 1.9 <= r <= 2.7 and rd < 0.2: res.append((c, nn, r, rd))
    return res
J = np.array([5.484, 0.202, 31.949])
for f in sorted(glob.glob(U + O + 'Arms/Arms-Raw-STL/*.stl')) + sorted(glob.glob(U + O + 'DoubleArms/DoubleArms-Raw-STL/*.stl')):
    b = os.path.basename(f)
    if 'Cable' in b: continue
    V, Tr = T.read_stl_np(f); V = np.asarray(V, float); Tr = np.asarray(Tr)
    ds = discs(V, Tr); out['discs'][b] = [{'c': c.tolist(), 'n': n.tolist(), 'r': r} for c, n, r, rd in ds]
    for c, n, r, rd in ds:
        sd = 'R' if c[0] > 0 else 'L'; jj = J * ([1, 1, 1] if sd == 'R' else [-1, 1, 1])
        print('%-22s disc %s side %s, %.2f mm from the kit joint, n %s' % (b, np.round(c, 2), sd, np.linalg.norm(c - jj), np.round(n, 2)), flush=True)
        if 'Double' not in b:
            W = T.arm_wrist_frame(V, Tr, c, sd); out['wrists'][b] = None if W is None else np.asarray(W).tolist()
            print('     wrist', None if W is None else np.round(np.asarray(W)[:3, 3], 2), flush=True)
for f in [U + O + 'Accesories/Raw-STL/38-Hand.stl'] + sorted(glob.glob(U + O + 'Weapons/Weapons-Raw-STL/3[345]-*.stl')):
    V, Tr = T.read_stl_np(f); V = np.asarray(V, float); Tr = np.asarray(Tr); caps = T.hand_caps(V, Tr); near = T._bvh_nearest(V, Tr)
    r = {}
    for s in 'RL':
        M, md = T.hand_wrist_frame(V, Tr, s, near, caps); r[s] = None if M is None else {'M': np.asarray(M).tolist(), 'med': md}
    out['hands'][os.path.basename(f)] = r
    print('%-22s hand R %s L %s' % (os.path.basename(f), None if r['R'] is None else (round(r['R']['med'], 3), np.round(np.array(r['R']['M'])[:3, 3], 2).tolist()), None if r['L'] is None else (round(r['L']['med'], 3), np.round(np.array(r['L']['M'])[:3, 3], 2).tolist())), flush=True)
json.dump(out, open('/home/claude/kits/tm/rules.json', 'w'), indent=1)

"""Wrist rule on the Chaplain arms, taking the outermost ROUND flat face (17-Arm-Left-A has its rosary cross further out)."""
import sys, json, os
import numpy as np, importlib.util
spec = importlib.util.spec_from_file_location('ti', '/home/claude/tiow_blender/tiow_inbox.py'); T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
U = "/mnt/user-data/uploads/new cults/All Mar All the time/"
D = json.load(open('/home/claude/kits/cj/discs.json'))
orig = T._flat_patches
def round_only(V, Tr, cen, n, a, idx, rng):
    for g, nn, A in orig(V, Tr, cen, n, a, idx, rng):
        o, r, B = T._face_circle(V, Tr, g, nn); rim = B - o; rim = np.linalg.norm(rim - (rim @ nn)[:, None] * nn, axis=1)
        if 1.0 <= r <= 2.8 and rim.std() <= 0.12 * r: yield g, nn, A
out = {}
for a in sorted(D):
    side = 'L' if '-Left-' in a else 'R'
    V, Tr = T.read_stl_np(U + a); V = np.asarray(V, float); Tr = np.asarray(Tr); j = np.array(D[a][0]['c'])
    M0 = T.arm_wrist_frame(V, Tr, j, side)
    T._flat_patches = round_only; M = T.arm_wrist_frame(V, Tr, j, side); T._flat_patches = orig
    same = M0 is not None and np.allclose(M0, M, atol=1e-6)
    out[a] = np.asarray(M).tolist()
    print(os.path.basename(a), side, np.round(np.asarray(M)[:3, 3], 2), 'same as the add-on' if same else 'add-on: ' + ('none' if M0 is None else 'different'), flush=True)
json.dump(out, open('/home/claude/kits/cj/wrist2.json', 'w'), indent=1)

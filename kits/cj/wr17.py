import sys, json, os
import numpy as np, importlib.util
spec = importlib.util.spec_from_file_location('ti', '/home/claude/tiow_blender/tiow_inbox.py'); T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
U = "/mnt/user-data/uploads/new cults/All Mar All the time/"; O = "ChaplainWithJumpPack (1)/ChaplainWithJumpPack/"
D = json.load(open('/home/claude/kits/cj/discs.json'))
for a in sorted(D):
    side = 'L' if '-Left-' in a else 'R'
    V, Tr = T.read_stl_np(U + a); V = np.asarray(V, float); Tr = np.asarray(Tr); joint = np.array(D[a][0]['c'])
    if side == 'L': V, Tr, joint = V * [-1.0, 1, 1], Tr[:, ::-1], joint * [-1.0, 1, 1]
    cen, n, ar = T._tri_info(V, Tr)
    dist = np.linalg.norm(cen - joint, axis=1); idx = np.where(dist > 0.55 * dist.max())[0]
    print(os.path.basename(a), 'max dist %.2f' % dist.max())
    for g, nn, A in T._flat_patches(V, Tr, cen, n, ar, idx, (3.0, 25.0)):
        c = (cen[g] * ar[g, None]).sum(0) / A; out = c - joint
        if out @ nn >= 0.3 * np.linalg.norm(out):
            o, r, B = T._face_circle(V, Tr, g, nn); rim = B - o; rim = np.linalg.norm(rim - (rim @ nn)[:, None] * nn, axis=1)
            print('   d %.2f  area %.1f r %.2f  rimdev %.2f  %s' % (np.linalg.norm(out), A, r, rim.std() / r, 'OK' if (1.0 <= r <= 2.8 and rim.std() <= 0.12 * r) else ''))

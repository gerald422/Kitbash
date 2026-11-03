import sys, json, numpy as np, pickle
exec(open('/home/claude/work/plates/buckle4.py').read().split('Pref, Mref =')[0])
D = '/mnt/user-data/uploads/d/Kitbash Library/_backups/techmarine-waist-2026-11-03/'
FB = pickle.load(open('/home/claude/work/plates/buckle_final.pkl', 'rb')); J = dict(jobs)
V, T = load(D + 'Waist-Pose.stl'); P, N = belt.surf_n(V, T, 400000); front = P[np.argmin(P[:, 0])]
for sc in (1.0, 1 / 0.95):
    Q = P * sc; f = front * sc; tgt = Q[np.linalg.norm(Q - f, axis=1) < 7]; tree = cKDTree(tgt)
    for ref in ('S2', '6A', '8A'):
        pass
    for ref in ('S2', '6A', '8A'):
        Pr, Mr = torso_pts(J[ref]); A = Mr @ FB[ref]; TPL = Pr[np.linalg.norm(Pr - A[:3, 3], axis=1) < 2.6][::3]; best = None
        for yaw in range(-30, 31, 10):
            for tilt in (-15, 0, 15):
                for dz in (-1, 0, 1):
                    Rz = np.eye(4); Rz[:3, :3] = R.from_euler('zx', [yaw + 90, tilt], degrees=True).as_matrix(); T0 = np.eye(4); T0[:3, 3] = f + [0.5, 0, dz]; C = np.eye(4); C[:3, 3] = -A[:3, 3]
                    r = icp_t(TPL, tree, tgt, T0 @ Rz @ C, keep=90)
                    if best is None or r[0] < best[0]: best = r
        print('scale %.3f: %s buckle on the techmarine waist: median %.3f / 75%% %.3f' % (sc, ref, best[0], best[1]))

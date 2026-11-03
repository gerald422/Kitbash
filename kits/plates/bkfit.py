import sys, json, numpy as np, pickle
exec(open('/home/claude/work/plates/buckle4.py').read().split('Pref, Mref =')[0])
FB = pickle.load(open('buckle_final.pkl', 'rb')); J = dict(jobs)
V, T = load('/mnt/user-data/uploads/Desktop/buckle.stl'); B, NB_ = belt.surf_n(V, T, 40000); c = (V.min(0) + V.max(0)) / 2
res = {}
for a, path in jobs:
    P, M = torso_pts(path); A = M @ FB[a]; tgt = P[np.linalg.norm(P - A[:3, 3], axis=1) < 4.5]; tree = cKDTree(tgt); best = None
    for out in (1, -1):
        Fb = frame(c, np.array([0, out, 0.0]), np.array([0, 0, 1.0]))          # buckle frame guess: out = +-Y, up = +Z
        for yaw in (-15, 0, 15):
            for tilt in (-10, 0, 10):
                for dz in (-0.5, 0, 0.5):
                    Rz = np.eye(4); Rz[:3, :3] = R.from_euler('yx', [yaw, tilt], degrees=True).as_matrix(); Tz = np.eye(4); Tz[:3, 3] = [0, dz, 0]
                    M0 = A @ Tz @ Rz @ np.linalg.inv(Fb)
                    Bf = B[(NB_ @ (np.array([0, out, 0.0]))) > -0.2]           # front and sides only: the back is the cut
                    r = icp_t(Bf, tree, tgt, M0, keep=70)
                    if best is None or r[0] < best[0]: best = (r[0], r[1], r[2], out)
    med, p75, Mx, out = best; res[a] = dict(M=np.linalg.inv(M) @ Mx, med=med, out=out)   # buckle file -> legs file
    print('%-5s buckle.stl on the legs buckle: median %.3f / 75%% %.3f mm (front = %sY)' % (a, med, p75, '+' if out > 0 else '-'))
pickle.dump(res, open('buckle_part_fit.pkl', 'wb'))

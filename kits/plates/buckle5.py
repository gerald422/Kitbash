exec(open('buckle4.py').read().split('Pref, Mref =')[0])
NB = pickle.load(open('buckle_anchor2.pkl', 'rb')); JB = pickle.load(open('buckle_josh.pkl', 'rb')); J = dict(jobs)
d = np.linalg.inv(NB['S2']) @ JB['S2']; print('reference correction in the anchor frame:', d[:3, 3].round(3))
final = {}
for a in J:
    final[a] = JB[a] if a in ('6A', '8A', 'S3') else NB[a] @ d
# Standing 3 by shape match from Josh's 6A, to compare with his own S3
P6, M6 = torso_pts(J['6A']); A6 = M6 @ JB['6A']; TPL = P6[np.linalg.norm(P6 - A6[:3, 3], axis=1) < 2.6][::3]
P, M = torso_pts(J['S3']); A0 = M @ JB['S3']; tgt = P[np.linalg.norm(P - A0[:3, 3], axis=1) < 7]; tree = cKDTree(tgt); best = None
for yaw in range(-30, 31, 10):
    for tilt in (-15, 0, 15):
        Rz = np.eye(4); Rz[:3, :3] = R.from_euler('zx', [yaw, tilt], degrees=True).as_matrix(); T0 = np.eye(4); T0[:3, 3] = A0[:3, 3]; C = np.eye(4); C[:3, 3] = -A6[:3, 3]
        r = icp_t(TPL, tree, tgt, T0 @ Rz @ C, keep=90)
        if best is None or r[0] < best[0]: best = r
As = best[2] @ A6
print('S3 from 6A by shape: median %.3f mm; vs your S3 spot %.2f mm, %.1f deg' % (best[0], np.linalg.norm(As[:3, 3] - A0[:3, 3]), np.degrees(R.from_matrix(As[:3, :3] @ A0[:3, :3].T).magnitude())))
pickle.dump(final, open('buckle_final.pkl', 'wb'))

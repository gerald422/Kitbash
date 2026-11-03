exec(open('buckle2.py').read().split('# reference buckle')[0])
prev = pickle.load(open('buckle_anchor.pkl', 'rb'))
def icp_t(A, tree, B, M0, it=50, keep=75):
    Mx = M0.copy()
    for _ in range(it):
        X = A @ Mx[:3, :3].T + Mx[:3, 3]; d, j = tree.query(X); k = d <= np.percentile(d, keep)
        P, Q = X[k], B[j[k]]; pc, qc = P.mean(0), Q.mean(0); U, S, Vt = np.linalg.svd((P - pc).T @ (Q - qc))
        D = np.eye(3); D[2, 2] = np.sign(np.linalg.det(Vt.T @ U.T)); Rr = Vt.T @ D @ U.T
        St = np.eye(4); St[:3, :3] = Rr; St[:3, 3] = qc - Rr @ pc; Mx = St @ Mx
    d = tree.query(A @ Mx[:3, :3].T + Mx[:3, 3])[0]; return np.percentile(d, 50), np.percentile(d, 75), Mx
Pref, Mref = torso_pts(LS % 2); Aref = Mref @ BF['S2']['Belt Front']; c0 = Aref[:3, 3]
dd = np.linalg.norm(Pref - c0, axis=1); TPL = Pref[(dd < 3.4) & (dd > 1.4)][::3]; print('template points (buckle plate without the boss)', len(TPL))
new = {}
for a, path in jobs:
    P, M = torso_pts(path); A0 = M @ prev[a]; tgt = P[np.linalg.norm(P - A0[:3, 3], axis=1) < 7]; tree = cKDTree(tgt); best = None
    for yaw in range(-20, 21, 10):
        for tilt in (-10, 0, 10):
            for dx in (-0.8, 0, 0.8):
                Rz = np.eye(4); Rz[:3, :3] = R.from_euler('zx', [yaw, tilt], degrees=True).as_matrix(); T0 = np.eye(4); T0[:3, 3] = A0[:3, 3] + A0[:3, 0] * dx; C = np.eye(4); C[:3, 3] = -c0
                r = icp_t(TPL, tree, tgt, T0 @ Rz @ C)
                if best is None or r[1] < best[1]: best = r
    med, p75, Mx = best; An = Mx @ Aref; new[a] = np.linalg.inv(M) @ An
    print('%-5s plate match median %.3f / 75%% %.3f mm; vs boss match %.2f mm, %.1f deg' % (a, med, p75, np.linalg.norm(An[:3, 3] - A0[:3, 3]), np.degrees(R.from_matrix(An[:3, :3] @ A0[:3, :3].T).magnitude())))
pickle.dump(new, open('buckle_anchor2.pkl', 'wb'))

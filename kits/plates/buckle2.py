import sys, json, numpy as np, pickle
sys.path.insert(0, '/home/claude/kitbash/kits'); import belt
exec(open('/home/claude/work/plates/plates.py').read().split('out = {}')[0])
exec(open('buckle.py').read().split('BF = ')[0].split('LS = ')[1].join(['LS = ', '']))
from scipy.spatial.transform import Rotation as R
BF = pickle.load(open('beltfront.pkl', 'rb'))
def torso_pts(path, n=400000):
    sc = json.load(open(path + '.sockets.json')); M = S_WAIST @ M16(sc['fits']['Waist'])
    V, T = load(path + '.stl'); P, N = belt.surf_n(V, T, n); return P @ M[:3, :3].T + M[:3, 3], M
def icp(A, tree, B, M0, it=40):
    Mx = M0.copy()
    for _ in range(it):
        X = A @ Mx[:3, :3].T + Mx[:3, 3]; d, j = tree.query(X); k = d <= np.percentile(d, 90)
        P, Q = X[k], B[j[k]]; pc, qc = P.mean(0), Q.mean(0); U, S, Vt = np.linalg.svd((P - pc).T @ (Q - qc))
        D = np.eye(3); D[2, 2] = np.sign(np.linalg.det(Vt.T @ U.T)); Rr = Vt.T @ D @ U.T
        St = np.eye(4); St[:3, :3] = Rr; St[:3, 3] = qc - Rr @ pc; Mx = St @ Mx
    d = tree.query(A @ Mx[:3, :3].T + Mx[:3, 3])[0]; return np.median(d), np.percentile(d, 90), Mx
# reference buckle: Standing Legs 2 (Josh: correct), points within 2.6 mm of its Belt Front anchor
Pref, Mref = torso_pts(LS % 2); Aref = Mref @ BF['S2']['Belt Front']; c0 = Aref[:3, 3]
TPL = Pref[np.linalg.norm(Pref - c0, axis=1) < 2.6][::3]; print('template points', len(TPL))
new = {}
for a, path in jobs:
    P, M = torso_pts(path); A0 = M @ BF[a]['Belt Front']; tgt = P[np.linalg.norm(P - A0[:3, 3], axis=1) < 7]; tree = cKDTree(tgt)
    best = None
    for yaw in range(-40, 41, 10):
      for tilt in (-15, 0, 15):
        for dz in (-0.6, 0, 0.6):
            Rz = np.eye(4); Rz[:3, :3] = R.from_euler('zx', [yaw, tilt], degrees=True).as_matrix()
            T0 = np.eye(4); T0[:3, 3] = A0[:3, 3] + [0, 0, dz]; C = np.eye(4); C[:3, 3] = -c0
            r = icp(TPL, tree, tgt, T0 @ Rz @ C)
            if best is None or r[0] < best[0]: best = r
    med, p90, Mx = best; An = Mx @ Aref                        # buckle anchor on this legs (torso coords)
    rv = R.from_matrix(An[:3, :3] @ A0[:3, :3].T).as_euler('zxy', degrees=True)
    new[a] = np.linalg.inv(M) @ An
    print('%-5s buckle fit median %.3f / 90%% %.3f mm; moved %.2f mm from the old spot; turned yaw %.1f, tilt %.1f/%.1f deg' % (a, med, p90, np.linalg.norm(An[:3, 3] - A0[:3, 3]), *rv))
pickle.dump(new, open('buckle_anchor.pkl', 'wb'))

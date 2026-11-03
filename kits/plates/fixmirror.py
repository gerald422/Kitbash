import sys, numpy as np, pickle, itertools
sys.path.insert(0, '/home/claude/work/van'); import reg
from scipy.spatial import cKDTree
exec(open('/home/claude/work/plates/plates.py').read().split('out = {}')[0])
out = pickle.load(open('plates.pkl', 'rb')); mp = pickle.load(open('mfplate.pkl', 'rb'))
for k, r in sorted(mp['res'].items()): print(k, 'mirror' if r['mirror'] else '', round(r['med'], 3))
def register_hand(A, B, want, it=40):
    ca, cb = A.mean(0), B.mean(0); _, _, Ea = np.linalg.svd(A - ca, full_matrices=False); _, _, Eb = np.linalg.svd(B - cb, full_matrices=False)
    tree = cKDTree(B); best = None
    for s in itertools.product((1, -1), repeat=3):
        R = Eb.T @ np.diag(s) @ Ea
        if np.sign(np.linalg.det(R)) != want: continue
        t = cb - R @ ca
        for _ in range(it):
            X = A @ R.T + t; d, j = tree.query(X); k = d < np.percentile(d, 90)
            P, Q = A[k], B[j[k]]; pc, qc = P.mean(0), Q.mean(0); U, S, Vt = np.linalg.svd((P - pc).T @ (Q - qc))
            D = np.eye(3); D[2, 2] = np.sign(np.linalg.det(Vt.T @ U.T)) * want; R = Vt.T @ D @ U.T; t = qc - R @ pc
        d = tree.query(A @ R.T + t)[0]; sc = np.median(d)
        if best is None or sc < best[0]: M = np.eye(4); M[:3, :3] = R; M[:3, 3] = t; best = (sc, M, np.percentile(d, 95))
    return best
WP = '/mnt/user-data/uploads/d/new cults/All Mar All the time/AssaultMarines-V2/WaistPlate.stl'
VW, TW = load(WP); PW = samples(VW, TW, 20000)
for s in 'RL':
    flags = [mp['res'][('%dA' % n, s)]['mirror'] for n in range(1, 9)]; want_mirror = sum(flags) > 4
    for n in range(1, 9):
        a = '%dA' % n
        if mp['res'][(a, s)]['mirror'] == want_mirror: continue
        VB, TB = load(LD % ('%dB' % n) + '.stl'); Bp = samples(VB, TB[out[a][s]['sel']], 15000)
        med, Mbw, p95 = register_hand(Bp, PW, -1 if want_mirror else 1)
        print('refit %s %s: median %.3f (was %.3f), 95%% %.3f' % (a, s, med, mp['res'][(a, s)]['med'], p95))
        mp['res'][(a, s)] = dict(W=np.linalg.inv(Mbw), med=med, p95=p95, mirror=want_mirror)
pickle.dump(mp, open('mfplate.pkl', 'wb'))

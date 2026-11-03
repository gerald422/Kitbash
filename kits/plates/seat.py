import sys, numpy as np, pickle, json
exec(open('/home/claude/work/plates/plates.py').read().split('out = {}')[0])
from scipy.spatial.transform import Rotation as R
out = pickle.load(open('plates.pkl', 'rb')); mp = pickle.load(open('mfplate.pkl', 'rb'))
WP = '/mnt/user-data/uploads/d/new cults/All Mar All the time/AssaultMarines-V2/WaistPlate.stl'
VW, TW = load(WP); PW = samples(VW, TW, 20000)
def sampn(V, T, n=300000, seed=0):
    A = V[T]; c = np.cross(A[:, 1] - A[:, 0], A[:, 2] - A[:, 0]); a = np.linalg.norm(c, axis=1); rng = np.random.default_rng(seed)
    i = rng.choice(len(T), n, p=a / a.sum()); u, w = rng.random(n), rng.random(n); f = u + w > 1; u[f], w[f] = 1 - u[f], 1 - w[f]
    return A[i, 0] + (A[i, 1] - A[i, 0]) * u[:, None] + (A[i, 2] - A[i, 0]) * w[:, None], c[i] / a[i, None]
def hips(path):
    sc = json.load(open(path + '.sockets.json')); return {s['type']: M16(s['matrix']) for s in sc['sockets'] if s['type'] in ('Hip R', 'Hip L')}
def mean_pose(Ms):
    q = R.from_matrix(np.array([m[:3, :3] for m in Ms])).mean().as_matrix(); T = np.eye(4); T[:3, :3] = q; T[:3, 3] = np.mean([m[:3, 3] for m in Ms], 0); return T
def err(A, B): return np.abs(PW[::20] @ (A[:3, :3] - B[:3, :3]).T + (A[:3, 3] - B[:3, 3])).max()
def tf(P, M): return P @ M[:3, :3].T + M[:3, 3]
jl = list(out); L = {}
for a in jl:
    VA, TA = load(LD % a + '.stl'); S, N = sampn(VA, TA); L[a] = (S, N, cKDTree(S), hips(LD % a))
# plate points that touch the legs (in the plate file), counted over the jump legs
cnt = {s: np.zeros(len(PW)) for s in 'RL'}
for a in jl:
    for s in 'RL': cnt[s] += L[a][2].query(tf(PW, mp['res'][(a, s)]['W']))[0] < 0.25
CP = {s: PW[cnt[s] >= len(jl) / 2] for s in 'RL'}; print('contact points: R %d, L %d' % (len(CP['R']), len(CP['L'])))
def seat(W0, S, N, tree, C, it=30, lam=1.0):
    """point-to-plane ICP of the plate's contact points onto the legs, pulled back toward the start pose (lam)"""
    W = W0.copy()
    for _ in range(it):
        X = tf(C, W); d, j = tree.query(X); k = d < 1.5
        if k.sum() < 20: break
        p, q, n = X[k], S[j[k]], N[j[k]]; cx = W[:3, 3]
        A = np.hstack([np.cross(p - cx, n), n]); b = ((q - p) * n).sum(1)
        # regulariser: small motion away from W0 (rotation in rad*10mm, translation in mm)
        dW = W @ np.linalg.inv(W0); rv = R.from_matrix(dW[:3, :3]).as_rotvec(); tv = W[:3, 3] - W0[:3, 3]
        Areg = np.sqrt(lam * k.sum() / 100) * np.diag([10, 10, 10, 1, 1, 1.0]); breg = -np.sqrt(lam * k.sum() / 100) * np.r_[10 * rv, tv]
        x = np.linalg.lstsq(np.vstack([A, Areg]), np.r_[b, breg], rcond=None)[0]
        D = np.eye(4); D[:3, :3] = R.from_rotvec(x[:3]).as_matrix(); D[:3, 3] = cx - D[:3, :3] @ cx + x[3:]
        W = D @ W
    return W
rel = {s: {a: np.linalg.inv(L[a][3]['Hip ' + s]) @ mp['res'][(a, s)]['W'] for a in jl} for s in 'RL'}
for lam in (0.0, 0.3, 1.0, 3.0):
    for s in 'RL':
        e0, e1 = [], []
        for a in jl:
            W0 = L[a][3]['Hip ' + s] @ mean_pose([r for b, r in rel[s].items() if b != a]); S, N, tree, _ = L[a]
            C = PW[(cnt[s] - (L[a][2].query(tf(PW, mp['res'][(a, s)]['W']))[0] < 0.25)) >= (len(jl) - 1) / 2]   # contact set without this leg
            W1 = seat(W0, S, N, tree, C, lam=lam); Wt = mp['res'][(a, s)]['W']
            e0.append(err(W0, Wt)); e1.append(err(W1, Wt))
        print('lam %.1f side %s: hip only median %.2f / max %.2f mm -> seated median %.2f / max %.2f mm' % (lam, s, np.median(e0), max(e0), np.median(e1), max(e1)))
pickle.dump(dict(CP=CP, rel=rel), open('seat.pkl', 'wb'))

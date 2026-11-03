import sys, numpy as np, pickle, json, itertools
sys.path.insert(0, '/home/claude/work/plates')
exec(open('/home/claude/work/plates/plates.py').read().split('out = {}')[0])
exec('def register_hand' + open('fixmirror.py').read().split('def register_hand')[1].split('WP = ')[0])
from scipy.spatial.transform import Rotation as R
LS = '/mnt/user-data/uploads/d/Kitbash Library/Mar Fil - Tacticus/AssaultMarines-V2/Legs/MarFil Assault - Legs %s'
out = pickle.load(open('plates.pkl', 'rb')); mp = pickle.load(open('mfplate.pkl', 'rb'))
WP = '/mnt/user-data/uploads/d/new cults/All Mar All the time/AssaultMarines-V2/WaistPlate.stl'
VW, TW = load(WP); PW = samples(VW, TW, 20000)
def legsM(path):
    sc = json.load(open(path + '.sockets.json')); M = S_WAIST @ M16(sc['fits']['Waist'])
    return sc, M, {s['type']: M16(s['matrix']) for s in sc['sockets'] if s['type'] in ('Hip R', 'Hip L')}
# 1) the mirrored-pose jump legs (2A L, 3A L, 4A L) have B twins: same plate extraction as before
for n in (2, 3, 4):
    a, b = '%dA L' % n, '%dB L' % n
    VA, TA = load(LD % a + '.stl'); VB, TB = load(LD % b + '.stl'); sc, M, hips = legsM(LD % a)
    SA = samples(VA, TA); tA = cKDTree(SA)
    cB = VB[TB].mean(1); idx = np.where(tA.query(cB)[0] > 0.12)[0]; Tf = TB[idx]
    G = coo_matrix((np.ones(Tf.size), (np.repeat(np.arange(len(idx)), 3), Tf.ravel() + len(idx))), shape=(len(idx) + len(VB),) * 2)
    lab = connected_components(G, directed=False)[1][:len(idx)]; up_legs = np.linalg.inv(M)[:3, :3] @ np.array([0, 0, 1.0]); found = {}
    for k in np.unique(lab):
        sel = idx[lab == k]; P = VB[TB[sel]].reshape(-1, 3)
        area = np.linalg.norm(np.cross(VB[TB[sel, 1]] - VB[TB[sel, 0]], VB[TB[sel, 2]] - VB[TB[sel, 0]]), axis=1).sum() / 2
        cx = (P @ M[:3, :3].T + M[:3, 3]).mean(0)
        if not (35 < area < 120) or abs(cx[0]) < 3.5: continue
        side = 'R' if cx[0] > 0 else 'L'
        c = P.mean(0); _, _, E = np.linalg.svd(P - c, full_matrices=False); nrm = E[2]
        if nrm @ (np.linalg.inv(M)[:3, :3] @ np.array([np.sign(cx[0]), 0, 0])) < 0: nrm = -nrm
        seam = P[tA.query(P)[0] < 0.3]; F = frame(seam.mean(0) if len(seam) > 20 else c, nrm, up_legs)
        if side in found and found[side][1] > area: continue
        found[side] = (F, area, sel, np.linalg.inv(hips['Hip ' + side]) @ F)
    out[a] = {s: dict(F=v[0], area=v[1], sel=v[2], rel=v[3]) for s, v in found.items()}
    for s in found:
        Bp = samples(VB, TB[found[s][2]], 15000); med, Mbw, p95 = register_hand(Bp, PW, 1)
        mp['res'][(a, s)] = dict(W=np.linalg.inv(Mbw), med=med, p95=p95, mirror=False)
        print('%s %s: plate %.0f mm2, WaistPlate fit median %.3f, 95%% %.3f mm' % (a, s, found[s][1], med, p95))
pickle.dump(out, open('plates.pkl', 'wb')); pickle.dump(mp, open('mfplate.pkl', 'wb'))
# 2) the hip anchor -> plate relation over all jump legs, and how well it predicts a plate it hasn't seen (leave one out)
jl = [k for k in out]
def mean_pose(Ms):
    q = R.from_matrix(np.array([m[:3, :3] for m in Ms])).mean().as_matrix(); T = np.eye(4); T[:3, :3] = q; T[:3, 3] = np.mean([m[:3, 3] for m in Ms], 0); return T
def err(A, B): return np.abs(PW[::20] @ (A[:3, :3] - B[:3, :3]).T + (A[:3, 3] - B[:3, 3])).max()
relW = {}
for s in 'RL':
    rel = {a: np.linalg.inv(legsM(LD % a)[2]['Hip ' + s]) @ mp['res'][(a, s)]['W'] for a in jl}
    relW[s] = mean_pose(list(rel.values()))
    loo = [err(legsM(LD % a)[2]['Hip ' + s] @ mean_pose([r for b, r in rel.items() if b != a]), mp['res'][(a, s)]['W']) for a in jl]
    print('side %s: hip-anchor estimate vs the real plate, leave-one-out over %d legs: worst plate point off by median %.2f, max %.2f mm' % (s, len(jl), np.median(loo), max(loo)))
pickle.dump(relW, open('relW.pkl', 'wb'))

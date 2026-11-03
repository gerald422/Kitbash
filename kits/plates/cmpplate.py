import sys, numpy as np, pickle, struct, json, glob
sys.path.insert(0, '/home/claude/work/van'); from reg import register
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
exec(open('/home/claude/work/plates/plates.py').read().split('out = {}')[0])
out = pickle.load(open('plates.pkl', 'rb'))
def shells(V, T):
    G = coo_matrix((np.ones(T.size), (np.repeat(np.arange(len(T)), 3), T.ravel() + len(T))), shape=(len(T) + len(V),) * 2)
    lab = connected_components(G, directed=False)[1][:len(T)]; return [T[lab == k] for k in np.unique(lab)]
def pext(P): c = P.mean(0); _, s, E = np.linalg.svd(P - c, full_matrices=False); Q = (P - c) @ E.T; return np.sort(Q.max(0) - Q.min(0))[::-1]
VB, TB = load(LD % '4B' + '.stl')
B = {s: samples(VB, TB[out['4A'][s]['sel']], 15000) for s in 'RL'}
print('4B sculpted plates: R %s, L %s mm' % (pext(B['R']).round(1), pext(B['L']).round(1)))
N = '/mnt/user-data/uploads/d/new cults/All Mar All the time/'
for f in ['AssaultMarines-V2/WaistPlate.stl', 'CaptainWithJumpPack/CaptainWithJumpPack/RawStl/8-WaistPlate-1.stl', 'CaptainWithJumpPack/CaptainWithJumpPack/RawStl/9-WaistPlate-2.stl',
          'CaptainWithJumpPack/CaptainWithJumpPack/RawStl/10-WaistPlate-3.stl', 'AssaultSquad/RawSTL/73-WaistPlate.stl', 'IntecessorSquad/IntercessorSquad/Legs/Legs-RawStl/25-WaistPlate.stl']:
    V, T = load(N + f); sh = [s for s in shells(V, T) if len(s) > 50]
    for i, t in enumerate(sh):
        P = samples(V, t, 20000)
        best = min(((register(B[s], P), s) for s in 'RL'), key=lambda x: x[0][0])
        (med, M, p95), s = best
        print('%-55s shell %d/%d  %s mm  vs 4B plate %s: median %.3f, 95%% %.3f mm %s' % (f.split('/')[-1] + ' (' + f.split('/')[0] + ')', i + 1, len(sh), pext(P).round(1), s, med, p95, '(mirror)' if np.linalg.det(M[:3, :3]) < 0 else ''))

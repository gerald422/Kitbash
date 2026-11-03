import sys, numpy as np, pickle, struct, json
sys.path.insert(0, '/home/claude/work/van'); from reg import surf
from scipy.spatial import cKDTree
exec(open('/home/claude/work/plates/plates.py').read().split('out = {}')[0])       # load(), samples(), frame(), LD, M16
CH = '/home/claude/work/chap/objects/'; V1 = '/home/claude/work/van/v1/'
def vk_frame(D, legs, plate):
    """VitalyKhan plate frame in its own file (= model coords): seam with the legs, out from the hip, model up (+Z)"""
    P = surf(D + plate + '.stl', 30000); L = surf(D + legs + '.stl', 200000); lc = L.mean(0)
    seam = P[cKDTree(L).query(P)[0] < 0.3]; c = P.mean(0); _, _, E = np.linalg.svd(P - c, full_matrices=False); nrm = E[2]
    out = c - lc; out[2] = 0
    if nrm @ out < 0: nrm = -nrm
    return frame(seam.mean(0), nrm, np.array([0, 0, 1.0])), P
FL, PL = vk_frame(CH, 'Legs', 'Hip l')                 # chaplain: plate on the model's left
FR, PR = vk_frame(V1, 'Legs', 'Hip r')                 # vanguard 1: on the model's right
def pext(P): c = P.mean(0); _, s, E = np.linalg.svd(P - c, full_matrices=False); Q = (P - c) @ E.T; return np.sort(Q.max(0) - Q.min(0))[::-1]
out = pickle.load(open('plates.pkl', 'rb'))
VB, TB = load(LD % '4B' + '.stl')
mf = [pext(VB[TB[out['4A'][s]['sel']]].reshape(-1, 3)) for s in 'RL']
print('plate sizes (principal extents): VitalyKhan L %s, R %s; Mar Fil 4B sculpted R %s, L %s' % (pext(PL).round(1), pext(PR).round(1), mf[0].round(1), mf[1].round(1)))
pickle.dump(dict(FL=FL, FR=FR), open('vkframes.pkl', 'wb'))

"""The four CyberBrush arm pieces with no round face found at all (Guns 3, Knife 1 and 6, Spear 4): placed like a sibling
by ICP of the sibling's upper arm, started from many points of the part (no shoulder face to start from)."""
import numpy as np, json
from scipy.spatial import cKDTree
from geo import *; from bbrules import *; from align import icp, rots
R = lambda M: [round(float(x), 6) for x in np.asarray(M).ravel()]
D = json.load(open('cb_discs.json')); A = json.load(open('cb_side_arms.json'))
key = lambda rel: rel[:-4].replace('/', '__')
placed = {key(r): d for r, d in A.items()}
JOBS = {'CyberBrush__Space Bugs Hunters__Space Bug Hunters Guns__3': ['CyberBrush__Space Bugs Hunters__Space Bug Hunters Guns__3 (Bayonet)'],
        'CyberBrush__Space Bugs Hunters__Space Bug Hunters Knife__1': None, 'CyberBrush__Space Bugs Hunters__Space Bug Hunters Knife__6': None,
        'CyberBrush__Space Bugs Hunters__Space Bug Hunters Spears__Unsupported__4': None}
def world(d):
    side = 'R' if 'Shoulder R' in d['fits'] else 'L'
    return (S_R if side == 'R' else S_L) @ np.array(d['fits'][f'Shoulder {side}']).reshape(4, 4), side
def fps(P, n):
    i = [0]; d = np.linalg.norm(P - P[0], axis=1)
    for _ in range(n - 1):
        j = int(np.argmax(d)); i.append(j); d = np.minimum(d, np.linalg.norm(P - P[j], axis=1))
    return P[i]
out = {}
for k, sibs in JOBS.items():
    folder = k.rsplit('__', 1)[0]
    sibs = sibs or [s for s in placed if s.rsplit('__', 1)[0] == folder and A[s.replace('__', '/') + '.stl']['category'] == 'Arms']
    V = load('npz/' + k + '.npz')[0]
    starts = fps(V[::7], 40)
    best = None
    for s in sibs:
        d = A[s.replace('__', '/') + '.stl']
        if d['category'] != 'Arms': continue
        Ws, side = world(d)
        G = load('npz/' + s + '.npz')[0]
        # the sibling's shoulder joint in its file coords = inverse placement of the torso's shoulder point
        c = (np.linalg.inv(Ws) @ np.r_[(S_R if side == 'R' else S_L)[:3, 3], 1])[:3]
        src = G[np.linalg.norm(G - c, axis=1) < 9.0]
        rs = np.random.default_rng(0); src = src[rs.choice(len(src), min(1500, len(src)), replace=False)]
        cand = []
        for p in starts:
            for Rk in rots():
                M0 = np.eye(4); M0[:3, :3] = Rk; M0[:3, 3] = p - Rk @ c
                M, med, q = icp(src, V, M0, it=8, trim=0.7); cand.append((med, M))
        cand.sort(key=lambda t: t[0])
        for med0, M0 in cand[:6]:
            M, med, q = icp(src, V, M0, it=60, trim=0.7)
            if best is None or med < best[1]: best = (s, med, M, Ws, side)
        print(k.split('__')[-1], '<-', s.split('__')[-1], 'best so far %.3f' % best[1], flush=True)
    s, med, M, Ws, side = best
    W = Ws @ np.linalg.inv(M)
    S = S_R if side == 'R' else S_L
    rel = k.replace('__', '/') + '.stl'
    out[rel] = dict(schemaVersion=1, part=k.split('__')[-1], category='Arms', sockets=[], fits={f'Shoulder {side}': R(np.linalg.inv(S) @ W)},
                    noPad=True, notes={"Shoulder": "CyberBrush arm in the model's own axes (front -Y), round shoulder face on the heresy shoulder point (as Springles / BBoosty); "
                                       f"the arm of {s.split('__')[-1]} (ICP {med:.2f} mm)", "Pad": "no pauldron anchor yet (CyberBrush pads to come)"})
    print('PLACED %-40s <- %-20s %s med %.3f' % (k.split('__', 2)[-1], s.split('__')[-1], side, med), flush=True)
json.dump(out, open('cb_side_arms2.json', 'w'))
print(len(out), 'done')

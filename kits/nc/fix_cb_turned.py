"""CyberBrush Chainsword 2 / 4 and Sword 4 have no shoulder face found, but their second round face (r 2.15) has the same
normal as on Axe/Hammer/Sword 2 and 4: they are exported in the same orientation, only moved. Placement = the sibling's,
moved by a translation-only ICP of the sibling's upper arm (started from the second faces)."""
import numpy as np, json
from scipy.spatial import cKDTree
from geo import load; from bbrules import S_R, S_L
R = lambda M: [round(float(x), 6) for x in np.asarray(M).ravel()]
D = json.load(open('cb_discs.json')); A = json.load(open('cb_side_arms.json'))
B = 'CyberBrush__Space Bugs Hunters__'
JOBS = {B + 'Space Bug Hunters Chainsword__2': [B + 'Space Bug Hunter Axe__2', B + 'Space Bug Hunters Hammer__2', B + 'Space Bug Hunters Sword__Unsupported__2'],
        B + 'Space Bug Hunters Chainsword__4': [B + 'Space Bug Hunter Axe__4', B + 'Space Bug Hunters Hammer__4'],
        B + 'Space Bug Hunters Sword__Unsupported__4': [B + 'Space Bug Hunter Axe__4', B + 'Space Bug Hunters Hammer__4']}
rel = lambda k: k.replace('__', '/') + '.stl'
second = lambda k: [d for d in D[k] if abs(d['r'] - 2.15) < 0.05][0]
for k, sibs in JOBS.items():
    V = load('npz/' + k + '.npz')[0]; tree = cKDTree(V)
    c2 = np.array(second(k)['cc']); best = None
    for s in sibs:
        d = A[rel(s)]; side = 'R' if 'Shoulder R' in d['fits'] else 'L'
        Ws = (S_R if side == 'R' else S_L) @ np.array(d['fits'][f'Shoulder {side}']).reshape(4, 4)
        G = load('npz/' + s + '.npz')[0]
        sh = [x for x in D[s] if abs(abs(x['n'][0]) - 1) < 0.05][0]
        src = G[np.linalg.norm(G - np.array(sh['cc']), axis=1) < 9.0]
        t = c2 - np.array(second(s)['cc'])
        for _ in range(60):
            dd, j = tree.query(src + t); keep = dd <= np.quantile(dd, 0.7)
            t = t + (V[j[keep]] - (src[keep] + t)).mean(0)
        dd = tree.query(src + t)[0]; med = float(np.median(dd))
        print('%-30s <- %-25s t %s med %.3f' % (k.split('__')[-2][-12:] + '/' + k.split('__')[-1], s.split('__')[-2][-12:] + '/' + s.split('__')[-1], t.round(2), med))
        if best is None or med < best[0]:
            Tm = np.eye(4); Tm[:3, 3] = -t
            best = (med, s, Ws @ Tm, side)
    med, s, W, side = best
    S = S_R if side == 'R' else S_L
    A[rel(k)]['fits'] = {f'Shoulder {side}': R(np.linalg.inv(S) @ W)}
    A[rel(k)]['notes']['Shoulder'] = ("CyberBrush arm in the model's own axes (front -Y), round shoulder face on the heresy shoulder point (as Springles / BBoosty); "
                                      f"exported turned like {s.split('__')[-2]} {s.split('__')[-1]} (same second round face), moved to match its upper arm ({med:.2f} mm)")
    print('  ->', s.split('__')[-1], side, '%.3f' % med)
json.dump(A, open('cb_side_arms.json', 'w'))

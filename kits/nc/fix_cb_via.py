"""Every CyberBrush arm placed by rotating ICP onto a sibling: if it is the sibling's arm only moved (a round face with the
same normal and radius on both, translation-only ICP of the sibling's upper arm < 0.03 mm), use that translation instead."""
import numpy as np, json, sys
from scipy.spatial import cKDTree
from geo import load; from bbrules import S_R, S_L
R = lambda M: [round(float(x), 6) for x in np.asarray(M).ravel()]
FILE = sys.argv[1] if len(sys.argv) > 1 else 'cb_side_arms.json'
D = json.load(open('cb_discs.json')); A = json.load(open('cb_side_arms.json')); TGT = json.load(open(FILE))
key = lambda rel: rel[:-4].replace('/', '__')
own = [key(r) for r, d in A.items() if d['category'] == 'Arms' and 'shoulder face on the heresy shoulder point' in d['notes']['Shoulder']
       and 'the arm of' not in d['notes']['Shoulder'] and 'exported turned like' not in d['notes']['Shoulder']]
FAM = ('Space Bug Hunter Axe', 'Space Bug Hunters Chainsword', 'Space Bug Hunters Hammer', 'Space Bug Hunters Sword')
fam = lambda x: any(a in x for a in FAM)
changed = 0
for rel, d in TGT.items():
    if d['category'] != 'Arms' or 'the arm of' not in d['notes']['Shoulder']: continue
    k = key(rel); folder = k.rsplit('__', 1)[0]
    sibs = [s for s in own if s.rsplit('__', 1)[0] == folder or (fam(k) and fam(s))]
    V = load('npz/' + k + '.npz')[0]; tree = cKDTree(V); best = None
    for s in sibs:
        pairs = [(a, b) for a in D[k] for b in D[s] if np.dot(a['n'], b['n']) > 0.999 and abs(a['r'] - b['r']) < 0.1]
        if not pairs: continue
        ds = A[s.replace('__', '/') + '.stl']; side = 'R' if 'Shoulder R' in ds['fits'] else 'L'
        Ws = (S_R if side == 'R' else S_L) @ np.array(ds['fits'][f'Shoulder {side}']).reshape(4, 4)
        G = load('npz/' + s + '.npz')[0]
        sh = max([x for x in D[s] if abs(abs(x['n'][0]) - 1) < 0.05], key=lambda x: x['A'])
        src = G[np.linalg.norm(G - np.array(sh['cc']), axis=1) < 9.0]
        rs = np.random.default_rng(0); src = src[rs.choice(len(src), min(3000, len(src)), replace=False)]
        for a, b in pairs:
            t = np.array(a['cc']) - np.array(b['cc'])
            for _ in range(40):
                dd, j = tree.query(src + t); keep = dd <= np.quantile(dd, 0.7)
                t = t + (V[j[keep]] - (src[keep] + t)).mean(0)
            med = float(np.median(tree.query(src + t)[0]))
            if best is None or med < best[0]:
                Tm = np.eye(4); Tm[:3, 3] = -t; best = (med, s, Ws @ Tm, side)
    old = d['notes']['Shoulder'].split('(ICP ')[-1]
    if best is None or best[0] > 0.03:
        print('%-55s keep (%s best moved-only %s)' % (rel[-55:], old.rstrip(')'), 'none' if best is None else '%.3f' % best[0])); continue
    med, s, W, side = best
    S = S_R if side == 'R' else S_L
    d['fits'] = {f'Shoulder {side}': R(np.linalg.inv(S) @ W)}
    d['notes']['Shoulder'] = ("CyberBrush arm in the model's own axes (front -Y), round shoulder face on the heresy shoulder point (as Springles / BBoosty); "
                              f"exported like {s.split('__')[-2]} {s.split('__')[-1]}, only moved ({med:.3f} mm)")
    changed += 1
    print('%-55s %s -> moved-only %.3f from %s' % (rel[-55:], old.rstrip(')'), med, s.split('__')[-1]))
json.dump(TGT, open(FILE, 'w'))
print(changed, 'changed')

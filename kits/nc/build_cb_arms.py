"""CyberBrush arms: like BBoosty, the arm parts come in the model's own axes (front -Y), only moved for printing,
whenever their round flat shoulder face (r ~2.5) faces +X (right) or -X (left): that face goes on the heresy shoulder
point (S_H). Parts printed turned (no +-X face) take the pose of a sibling with the same arm (ICP)."""
import numpy as np, json, os
from geo import *; from bbrules import *; from align import icp, rots
R = lambda M: [round(float(x), 6) for x in np.asarray(M).ravel()]
D = json.load(open('/home/claude/kits/nc/cb_discs.json'))
def rel_of(k): return k.replace('__', '/') + '.stl'
SKIP = ('Shields__1 A', 'Shields__1 B', 'Guns__Gun', 'Guns__Gun (Bayonet)', 'Spears__Unsupported__Free', 'Sword__Unsupported__Free')
TWO = {'Space Bug Hunters Guns': 'Two-Handed Guns', 'Space Bug 2 hand Sword': 'Two-Handed Melee', 'Space Bug Hunter 2H Axe': 'Two-Handed Melee'}
def discs(k):
    return [dict(cc=np.array(d['cc']), n=np.array(d['n']), r=d['r'], A=d['A']) for d in D[k] if abs(abs(d['n'][0]) - 1) < 0.05]
placed = {}       # key -> (W, side, how)
for k, ds in D.items():
    if not k.startswith('CyberBrush') or any(k.endswith(s) for s in SKIP): continue
    ax = discs(k)
    if not ax: continue
    if len({np.sign(d['n'][0]) for d in ax}) == 2:
        d = max([d for d in ax if d['n'][0] > 0], key=lambda d: d['A']); side = 'R'; two = True
    else:
        d = max(ax, key=lambda d: d['A']); side = 'R' if d['n'][0] > 0 else 'L'; two = False
    placed[k] = (arm_world(d, side), side, 'own shoulder face', two)
# turned prints: the sibling (same folder, or the same arm pose in the axe/chainsword/hammer/sword sets) whose arm matches best
own = list(placed)
for k, ds in D.items():
    if k in placed or any(k.endswith(s) for s in SKIP) or not ds: continue
    folder = k.rsplit('__', 1)[0]
    ARMFAM = ('Space Bug Hunter Axe', 'Space Bug Hunters Chainsword', 'Space Bug Hunters Hammer', 'Space Bug Hunters Sword')
    fam = lambda x: any(a in x for a in ARMFAM)
    sibs = [s for s in own if s.rsplit('__', 1)[0] == folder or (fam(k) and fam(s) and s.split('__')[-1] == k.split('__')[-1])]
    if not sibs: print('no sibling', k); continue
    V = load('/home/claude/kits/nc/npz/' + k + '.npz')[0]
    best = None
    for s in sibs:
        G = load('/home/claude/kits/nc/npz/' + s + '.npz')[0]
        Ws, side_s, _, two_s = placed[s]
        # the upper arm: within 9 mm of the sibling's shoulder face
        dsib = [d for d in discs(s) if (d['n'][0] > 0) == (side_s == 'R')]
        c = max(dsib, key=lambda d: d['A'])['cc']
        src = G[np.linalg.norm(G - c, axis=1) < 9.0]
        rs = np.random.default_rng(0); src = src[rs.choice(len(src), min(2500, len(src)), replace=False)]
        b2 = None
        for Rk in rots():
            M0 = np.eye(4); M0[:3, :3] = Rk; M0[:3, 3] = np.array(ds[0]['cc']) - Rk @ c
            M, med, q = icp(src, V, M0, it=15, trim=0.7)
            if b2 is None or med < b2[1]: b2 = (M, med)
        M, med, q = icp(src, V, b2[0], it=60, trim=0.7)
        if best is None or med < best[1]: best = (s, med, M)
    s, med, M = best; Ws, side_s, _, two_s = placed[s]
    placed[k] = (Ws @ np.linalg.inv(M), side_s, f'the arm of {s.split("__")[-1]} (ICP {med:.2f} mm)', two_s)
    print('via %-50s <- %-30s med %.3f' % (k.split('__', 2)[-1][-50:], s.split('__')[-1], med))
side_out = {}
for k, (W, side, how, two) in placed.items():
    folder = k.split('__')[2] if k.count('__') >= 3 else ''
    stem = k.split('__')[-1]
    if two:
        cat = TWO.get(folder, 'Two-Handed Guns'); fits = {"Shoulder R": R(np.linalg.inv(S_R) @ W)}
        note = "CyberBrush two-armed piece in the model's own axes: the right arm's round shoulder face on the heresy shoulder point (as Springles / BBoosty); the left arm comes with it"
    else:
        cat = 'Arms'; S = S_R if side == 'R' else S_L; fits = {f"Shoulder {side}": R(np.linalg.inv(S) @ W)}
        note = "CyberBrush arm in the model's own axes (front -Y), round shoulder face on the heresy shoulder point (as Springles / BBoosty); " + how
    d = dict(schemaVersion=1, part=stem, category=cat, sockets=[], fits=fits, notes={"Shoulder": note})
    if cat == 'Arms':
        d['noPad'] = True; d['notes']['Pad'] = "no pauldron anchor yet (CyberBrush pads to come)"
    side_out[rel_of(k)] = d
json.dump(side_out, open('/home/claude/kits/nc/cb_side_arms.json', 'w'))
from collections import Counter
print(len(side_out), Counter(d['category'] for d in side_out.values()))

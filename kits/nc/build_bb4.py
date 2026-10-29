"""BBoosty phase 1d: two-handed swords (two hands on the hilt): upper hand -> Hand R grip, lower -> offHand."""
import numpy as np, json, os
from geo import *; from bbrules import *; from handfind import find_hand
R = lambda M: [round(float(x), 6) for x in np.asarray(M).ravel()]
def rel_of(f): return os.path.basename(f)[:-4].replace('__', '/') + '.stl'
def get(key): return [x for x in key_files('') if x.endswith(key + '.npz')][0]
P = 'Praetor with Paragon Blade__Praetor with Paragon Blade__'; MM = 'Medusas Mortals__Medusas Mortals__'
def hand_frame(c, r, a, zhint): return frame_YZ(c + (r - 0.55) * a, a, zhint)
TPL = {}
for t in [MM + 'Stuff__Hand_Fist', MM + 'Stuff__Bionic_Hand_Fist', 'Chaplain__Hand', 'Chaplain__HandBionic']:
    V, F = load(get(t)); b = balls(V, F, 0.95, 1.45, minc=0.35, k=1)[0]; TPL[t] = dict(V=V, c=b['c'], r=b['r'], free=b['free'])
side_out = {}
for f in [x for x in key_files('BBoosty') if 'TwoHands' in x]:
    V, F = load(f)
    starts = [b['c'] for b in balls(V, F, 0.95, 1.45, minc=0.3, k=10)]
    found = []
    for k in range(2):
        st = [s for s in starts if all(np.linalg.norm(s - h['c']) > 3.0 for h in found)]
        if found:
            w_, U_ = np.linalg.eigh(np.cov((V - V.mean(0)).T)); L_ = U_[:, -1]
            st = st[:4] + [found[0]['c'] + d_ * L_ for d_ in (3.0, 4.0, 5.0, -3.0, -4.0, -5.0)]
        best = None
        for t, T_ in TPL.items():
            M, med, q9 = find_hand(T_['V'], T_['c'], V, F, starts=st[:6], nrot=30)
            if best is None or q9 < best[2]: best = (t, M, q9, med)
        t, M, q9, med = best; T_ = TPL[t]
        found.append(dict(t=t, q9=q9, c=M[:3, :3] @ T_['c'] + M[:3, 3], a=M[:3, :3] @ T_['free'], r=T_['r']))
    # blade direction: PCA long axis, signed toward the tip (away from both hands)
    mid = (found[0]['c'] + found[1]['c']) / 2
    w, U = np.linalg.eigh(np.cov((V - V.mean(0)).T)); L = U[:, -1]
    if (V.mean(0) - mid) @ L < 0: L = -L
    up, lo = sorted(found, key=lambda h: -(h['c'] @ L))        # the hand nearer the blade grips (right)
    G = hand_frame(up['c'], up['r'], up['a'], L)
    O = hand_frame(lo['c'], lo['r'], lo['a'], L)
    fitG = np.linalg.inv(G)
    d = dict(schemaVersion=1, part=os.path.splitext(os.path.basename(rel_of(f)))[0], category="Two-Handed Held", sockets=[],
             fits={"Hand R": R(fitG)}, offHand=R(O), pivot=[round(float(x), 6) for x in (up['c'] + up['r'] * up['a'])],
             notes={"Hand R": f"the upper hand on the hilt ({up['t'].split('__')[-1]}, q90 {up['q9']:.2f}): its wrist ball in the right wrist socket, blade to the torso's up+forward",
                    "offHand": f"the lower hand's wrist ({lo['t'].split('__')[-1]}, q90 {lo['q9']:.2f}): the sword turns about the right wrist to bring it to the left wrist"})
    side_out[rel_of(f)] = d
    print('%-60s up %s q%.2f  lo %s q%.2f  hands %.1f mm apart' % (os.path.basename(f)[-60:], np.round(up['c'], 1), up['q9'], np.round(lo['c'], 1), lo['q9'], np.linalg.norm(up['c'] - lo['c'])))
json.dump(side_out, open('/home/claude/kits/nc/bb_side_2h.json', 'w'))

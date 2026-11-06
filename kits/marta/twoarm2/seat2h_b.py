"""Fallback for sets the compact-face test missed: the Oct 30 two-armed rule (kits/marta/twoarm.py shoulder_pair: flat
faces > 10 mm2 within 11 deg of +-X, facing each other 9-15 mm apart, within 2.5 mm in Y and Z), fit as mgeo.arm_fit."""
import sys, json, numpy as np
sys.path.insert(0, '/home/claude/work/m2h'); import mgeo as M
NC = '/mnt/user-data/uploads/d/new cults/'; out = json.load(open('results.json'))
def pair(V, T):
    cand = [m for m in M.merge_flats(M.flats(V, T, min_area=1.0)) if abs(m[1][0]) > 0.98 and m[0] > 10]; best = None
    for i, (a1, n1, c1) in enumerate(cand):
        for a2, n2, c2 in cand[i + 1:]:
            if n1 @ n2 > -0.97: continue
            d = c2[0] - c1[0]
            if (n1[0] > 0 and d < 0) or (n1[0] < 0 and d > 0): continue
            if not (9 < abs(d) < 15) or abs(c1[1] - c2[1]) > 2.5 or abs(c1[2] - c2[2]) > 2.5: continue
            if best is None or a1 + a2 > best[0]: best = (a1 + a2, (a1, n1, c1), (a2, n2, c2))
    return None if best is None else ((best[1], best[2]) if best[1][1][0] > 0 else (best[2], best[1]))
import re
GUN = re.compile(r'pistol|gun|bolt|rifle|plasma|melta|flamer|las|shotgun|combi|volkite|grav|carbine|launcher|cannon|bfg|weapon', re.I)
for rel, r in out.items():
    if r['ok']: continue
    V, T = M.load(NC + rel); p = pair(V, T); n = rel.rsplit('/', 1)[-1][:-4]
    if p is None: print('STILL NO PAIR', rel[6:100]); continue
    R_, L_ = p; side, F = M.arm_fit(R_); d = np.linalg.norm(np.array(R_[2]) - np.array(L_[2]))
    out[rel] = {'ok': True, 'side': side, 'fit': np.asarray(F).tolist(), 'cat': 'Two-Handed Guns' if GUN.search(n) else 'Two-Handed Melee', 'faces': [round(float(R_[0]), 1), round(float(L_[0]), 1)], 'apart': round(float(d) * 0.9, 2), 'rule': 'oct30'}
    print('%-16s faces %5.1f / %5.1f, %5.2f mm apart at 90%% | %s' % (out[rel]['cat'], R_[0], L_[0], d * 0.9, rel[6:100]))
json.dump(out, open('results.json', 'w'), indent=0)
# validate against the library's sidecar for the set already in (Oct 30)
k = [x for x in out if x.endswith('set_arms_1_with_weapon_1.stl')][0]
lib = json.load(open('/home/claude/kitbash/library/Marta PunkGirl - Tacticus/51 May 2026/amrs and weapons/Two-Handed Guns/Marta May 2026 - Set Arms 1 With Weapon 1.sockets.json', encoding='utf-8-sig'))
A = np.array(lib['fits']['Shoulder R']).reshape(4, 4); B = np.array(out[k]['fit']) if out[k]['ok'] else None
if B is not None:
    R = A[:3, :3].T @ B[:3, :3]; print('vs the Oct 30 fit: %.2f deg, %.3f mm' % (np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))), np.linalg.norm(A[:3, 3] - B[:3, 3])))

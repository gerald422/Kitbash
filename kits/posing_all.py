import geo, numpy as np, json, os, sys
from scipy.spatial.transform import Rotation as Rr
sys.path.insert(0, '.'); from posing_cmp import raw_to_local, info, A
L = json.load(open('lip_seat2.json'))
W = {k: np.array(v) for k, v in json.load(open('waist_frames2.json')).items()}
Z = W[A + 'Legs/28-Legs-1.stl'][:3, 2]
socks = {info[k]['parent']: k for k in info if not k.startswith('_') and 'Chest to legs' in k}
res = {}
for legs, s in sorted(socks.items()):
    base = legs.split('.')[0]
    sub = 'Legs/' if int(base.split('-')[0]) <= 32 else 'Legs(JumpPack)/'
    rel = A + sub + base + '.stl'
    TL, m = raw_to_local(legs, rel)
    Mj = np.linalg.inv(np.array(info[s]['mw'])) @ np.array(info[legs]['mw']) @ TL      # legs raw -> torso raw
    D = Mj @ np.linalg.inv(np.array(L[rel]['M']))
    rv = np.degrees(Rr.from_matrix(D[:3, :3]).as_rotvec())
    res[legs] = {'rel': rel, 'Mj': Mj.tolist(), 'D': D.tolist(), 'med': m}
    print('%-16s T med %.3f | vs lip-match: about X %6.1f  Y %6.1f  Z %6.1f   shift %s   vs raw kit rot %.1f' % (legs, m, rv[0], rv[1], rv[2], np.round(D[:3, :3] @ [0, 2, 26.5] + D[:3, 3] - [0, 2, 26.5], 2), geo.ang(Mj[:3, :3])))
json.dump(res, open('posing_all.json', 'w'), indent=1)

"""Josh's own torso-on-legs placements (posing for claude.blend: every legs' 'Chest to legs' socket) and his
Right/Left Hip sockets, in each legs file's raw coordinates."""
import geo, numpy as np, json, os, sys
from scipy.spatial.transform import Rotation as Rr
from posing_cmp import raw_to_local, info, A
P = json.load(open('posing_all.json'))
L = json.load(open('lip_seat2.json'))
out = {}
for legs, d in P.items():
    rel = d['rel']
    TL, m = raw_to_local(legs, rel); TLi = np.linalg.inv(TL)
    hips = {}
    for ch in info[legs]['children']:
        if ch in info and ('Right Hip' in ch or 'Left Hip' in ch or 'Tabard' in ch):
            hips[('Hip R' if 'Right' in ch else 'Hip L' if 'Left' in ch else 'Belt Front')] = (TLi @ np.array(info[ch]['ml'])).tolist()
    out[rel] = {'M': d['Mj'], 'D': d['D'], 'hips': hips, 'med': m}
    print(os.path.basename(rel), 'hips', list(hips), 'T med %.3f' % m)
Ds = [np.array(v['D']) for v in out.values()]
rot = Rr.from_matrix([D[:3, :3] for D in Ds]).mean().as_matrix()
t = np.mean([D[:3, 3] for D in Ds], axis=0)
Davg = geo.M4(rot, t)
print('average D: rot', np.round(np.degrees(Rr.from_matrix(rot).as_rotvec()), 2), 't', np.round(t, 3))
for rel, v in out.items():
    D = np.array(v['D']); X = D @ np.linalg.inv(Davg)
    v['dev'] = geo.ang(X[:3, :3])
json.dump({'legs': out, 'Davg': Davg.tolist()}, open('legs_josh.json', 'w'), indent=1)
print('spread from average (deg):', sorted(round(v['dev'], 1) for v in out.values()))

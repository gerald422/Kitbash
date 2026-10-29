import sys; sys.path.insert(0, '/home/claude/kits')
import geo, numpy as np, os, json, wristrule as W
from fist import side
UP = np.array([-0.72, 0.52, 0.45])
def arm_items():
    for rel, d in sorted(side.items()):
        if d.get('category') != 'Arms': continue
        hs = [s for s in d['sockets'] if s['type'] in ('Hand R', 'Hand L')]
        sh = [k for k in d.get('fits', {}) if k.startswith('Shoulder')]
        if not hs or not sh: continue
        S = np.array(hs[0]['matrix']).reshape(4, 4); sd = hs[0]['type'][-1]
        joint = np.linalg.inv(np.array(d['fits'][sh[0]]).reshape(4, 4))[:3, 3]
        yield rel, sd, S, joint
if __name__ == '__main__':
    out = {}; offs = []
    for rel, sd, S, joint in arm_items():
        V, T = geo.load(rel)
        up = UP * (np.array([-1, 1, 1]) if sd == 'L' else 1)
        M = W.wrist_frame(V, T, joint, up)
        if M is None: print(os.path.basename(rel), 'NONE'); continue
        R = S[:3, :3] / np.linalg.norm(S[:3, :3], axis=0)
        o = (M[:3, 3] - S[:3, 3]) @ R
        if sd == 'L': o = o * [-1, 1, 1]
        offs.append(o)
        dy = np.degrees(np.arccos(np.clip(M[:3, 1] @ R[:, 1], -1, 1)))
        dz = np.degrees(np.arctan2(M[:3, 2] @ R[:, 0], M[:3, 2] @ R[:, 2]))
        out[rel] = dict(M=M.tolist(), side=sd, dy=float(dy), dz=float(dz), off=o.tolist())
        print('%-26s %s  off %s  axis %4.1f roll %5.1f' % (os.path.basename(rel)[:-4], sd, o.round(2), dy, dz))
    offs = np.array(offs); print('arm: rule origin in Josh socket frame  median', np.median(offs, 0).round(3), 'spread', offs.std(0).round(3))
    json.dump(out, open('/home/claude/kits/armrule_res.json', 'w'))

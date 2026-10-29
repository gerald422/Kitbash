import numpy as np, json, os, sys
sys.path.insert(0, '/home/claude/kits/nc')
from pads import *
R = lambda M: [round(float(x), 6) for x in np.asarray(M).ravel()]
arms = json.load(open('/home/claude/kits/nc/cb_side_arms2.json'))
out = {}
for rel, d in arms.items():
    if d['category'] != 'Arms': continue
    side = 'R' if 'Shoulder R' in d['fits'] else 'L'
    S = S_R if side == 'R' else S_L
    W = S @ np.array(d['fits'][f'Shoulder {side}']).reshape(4, 4)
    V, F = load('/home/claude/kits/nc/npz/' + rel[:-4].replace('/', '__') + '.npz')
    dm = dome_world(V, F, W, side)
    if dm is None: print('%-60s no dome' % rel[-60:]); continue
    out[rel] = R(np.linalg.inv(W) @ anchor_world(dm['c'], side))
    print('%-60s %s dome r %.2f c %s' % (rel[-60:], side, dm['r'], np.round(dm['c'], 2)))
json.dump(out, open('/home/claude/kits/nc/cb_pad_anchors2.json', 'w')); print(len(out), 'anchors')

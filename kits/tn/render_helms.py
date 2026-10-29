import sys; sys.path.insert(0,'/home/claude/kits'); sys.path.insert(0,'/home/claude/kits/cr'); sys.path.insert(0,'/home/claude/kits/tn')
import numpy as np, json, stlcache
import conv
from render_cross import am, fit, ARM_R, ARM_L, C_T, C_MF, C_TN
from tn_sockets import sockets_for
from tn_torso import TN
H = json.load(open('/home/claude/kits/tn/helm/sample_fits.json'))
REFT = {"Mk2": "TurtleNinja's Mk2-6 Builder/Mk2/Torsos/Upper A 1.stl", "Mk3": "TurtleNinja's Mk2-6 Builder/Mk3/Torsos/Upper A 9.stl", "Mk4": "TurtleNinja's Mk2-6 Builder/Mk4/Torsos/Upper A 1.stl",
        "Mk5": "TurtleNinja's Mk2-6 Builder/Mk4/Torsos/Upper A 1.stl", "Mk6/": "TurtleNinja's Mk2-6 Builder/Mk6/Torsos/Upper A 9.stl", "Updated": "TurtleNinja's Mk2-6 Builder/Mk6/Torsos/Upper A 9.stl",
        "Mk7-8": "TurtleNinja's Mk7-8 Builder/Mk7-8/Torsos/Upper A 1.stl", "Tactical": "TurtleNinja's Mk2-6 Builder/Mk4/Torsos/Upper A 1.stl"}
models = []
for i, (rel, F) in enumerate(H.items()):
    tor = next(v for k, v in REFT.items() if k in rel); F = np.array(F).reshape(4, 4)
    S, f = sockets_for(tor); W = conv.KB @ np.linalg.inv(S['Flat Waist'])
    models.append(dict(name=f'T{i}', items=[[stlcache.npz(TN + tor), W.ravel().tolist(), C_T], [stlcache.npz(TN + rel), (W @ S['Neck'] @ F).ravel().tolist(), C_TN],
          [am(ARM_R), (W @ S['Shoulder R'] @ fit(ARM_R, 'Shoulder R')).ravel().tolist(), C_MF], [am(ARM_L), (W @ S['Shoulder L'] @ fit(ARM_L, 'Shoulder L')).ravel().tolist(), C_MF]]))
    models.append(dict(name=f'M{i}', items=[[am(conv.AMT), np.eye(4).ravel().tolist(), C_MF], [stlcache.npz(TN + rel), (conv.S_AM['Neck'] @ F).ravel().tolist(), C_TN],
          [am(ARM_R), (conv.S_AM['Shoulder R'] @ fit(ARM_R, 'Shoulder R')).ravel().tolist(), C_MF], [am(ARM_L), (conv.S_AM['Shoulder L'] @ fit(ARM_L, 'Shoulder L')).ravel().tolist(), C_MF]]))
json.dump({"out": "/home/claude/kits/tn/rhs", "res": 260, "pad": 1.05, "models": models, "views": {"front": [0, 1, 0], "side": [1, 0, 0]}}, open('j_hs.json', 'w'))
json.dump(list(H), open('rhs_list.json', 'w'))

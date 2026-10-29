import sys; sys.path.insert(0,'/home/claude/kits'); sys.path.insert(0,'/home/claude/kits/cr'); sys.path.insert(0,'/home/claude/kits/tn'); sys.path.insert(0,'/home/claude/kits/cr/dev')
import numpy as np, json, stlcache, flats
from topface import merge_flats
from flatface import frame
import conv
from render_cross import C_T, C_TN, C_MF
from tn_sockets import sockets_for
from tn_torso import TN
QIR = np.linalg.inv(conv.Q['Shoulder R'])
def disc_fit(path, up=(0, 1, 0)):
    V, T = stlcache.load(path); M = merge_flats([(A, n, c) for A, n, c, o, s in flats.flats(V, T, min_area=1.0)])
    d = max([m for m in M if 6 < m[0] < 30], key=lambda m: m[0])
    return QIR @ np.linalg.inv(frame(d[2], -d[1], up)), d
tor = "TurtleNinja's Mk10 Assault Intercessor + Jumppack Addon/Torso/Mk10_Assault_Torso_Skull_Aquilla_1.stl"
S, f = sockets_for(tor); W = conv.KB @ np.linalg.inv(S['Flat Waist'])
P = "TurtleNinja's Mk10 Assault Intercessor + Jumppack Addon/Arms/"
models = []
for i, n in enumerate(["Mk10_2.0_Arm_Right_A_1", "Mk10_Powerfist_Fist_1", "Mk10_Powerfist_Fist_2", "Mk10_Powerfist_Fist_4", "Mk10_Powerfist_Relaxed_1"]):
    F, d = disc_fit(TN + P + n + ".stl"); print(n, 'disc A %.1f n %s' % (d[0], d[1].round(2)))
    models.append(dict(name=f'F{i}', items=[[stlcache.npz(TN + tor), W.ravel().tolist(), C_T], [stlcache.npz(TN + P + n + ".stl"), (W @ S['Shoulder R'] @ F).ravel().tolist(), C_TN]]))
json.dump({"out": "/home/claude/kits/tn/rf", "res": 260, "pad": 1.05, "models": models, "views": {"front": [0, 1, 0], "side": [1, 0, 0], "top": [0, 0.01, 1]}}, open('j_pf.json', 'w'))

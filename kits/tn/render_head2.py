import sys; sys.path.insert(0,'/home/claude/kits'); sys.path.insert(0,'/home/claude/kits/cr'); sys.path.insert(0,'/home/claude/kits/tn')
import numpy as np, json, stlcache
import conv
from render_cross import am, fit, ARM_R, ARM_L, HELM, C_T, C_MF, C_TN
from render_head import tn_helmet_frame
from tn_sockets import sockets_for, face_frames
from tn_torso import TN
AM_DROP = conv.S_AM['Neck'][2, 3] - conv.S_AM['Shoulder R'][2, 3]     # AM neck seat above the shoulder joints
print('AM neck above shoulders %.2f' % AM_DROP)
def model(torso_rel, frac):
    S, f = sockets_for(torso_rel); W = conv.KB @ np.linalg.inv(S['Flat Waist'])
    up = f['up']; hs = 0.5 * (f['shR'][2] + f['shL'][2]) @ up; hn = f['neck'][2] @ up
    drop = (hn - (hs + AM_DROP)) * frac
    N = S['Neck'].copy(); N[:3, 3] -= up * drop
    return [[stlcache.npz(TN + torso_rel), W.ravel().tolist(), C_T],
            [am(ARM_R), (W @ S['Shoulder R'] @ fit(ARM_R, 'Shoulder R')).ravel().tolist(), C_MF],
            [am(ARM_L), (W @ S['Shoulder L'] @ fit(ARM_L, 'Shoulder L')).ravel().tolist(), C_MF],
            [am(HELM), (W @ N @ fit(HELM, 'Neck')).ravel().tolist(), C_MF]], drop
models = []
for t, tag in (("TurtleNinja's Mk6 Assault Addon 1/Torsos/Mk6_Assault_Torso_A_2.stl", 'TN6'), ("TurtleNinja's Mk7-8 Builder/Mk7-8/Torsos/Mk8 Torso A 1.stl", 'TN8'), ("TurtleNinja's Mk10 Assault Intercessor + Jumppack Addon/Torso/Mk10_Assault_Torso_Skull_Aquilla_1.stl", 'TN10')):
    for frac, lab in ((0, 'A_now'), (0.5, 'C_half'), (1, 'B_shoulder')):
        it, d = model(t, frac); print(tag, lab, 'drop %.2f' % d)
        models.append(dict(name=f'{tag}_{lab}', items=it))
json.dump({"out": "/home/claude/kits/tn/rh2", "res": 420, "pad": 1.05, "models": models, "views": {"front": [0, 1, 0], "side": [1, 0, 0]}}, open('j_head2.json', 'w'))

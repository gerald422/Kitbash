import sys; sys.path.insert(0,'/home/claude/kits'); sys.path.insert(0,'/home/claude/kits/cr'); sys.path.insert(0,'/home/claude/kits/tn')
import numpy as np, json, stlcache
import conv
from flatface import frame
from render_cross import am, fit, ARM_R, ARM_L, HELM, C_T, C_MF
from tn_sockets import sockets_for
from tn_torso import TN
def shoulder_frame(SR, SL):
    o = 0.5 * (SR[:3, 3] + SL[:3, 3]); x = SR[:3, 3] - SL[:3, 3]; up = SR[:3, 2] + SL[:3, 2]
    z = up - (up @ x) / (x @ x) * x
    return frame(o, z, np.cross(z, x))          # y = z x x = front
K_AM = shoulder_frame(conv.S_AM['Shoulder R'], conv.S_AM['Shoulder L'])
NECK_IN_SH = np.linalg.inv(K_AM) @ conv.S_AM['Neck']
print('AM shoulder frame o', K_AM[:3, 3].round(3), 'axes ok', np.allclose(K_AM[:3, :3], np.eye(3), atol=1e-3), 'neck in it', NECK_IN_SH[:3, 3].round(3))
def model(torso_rel):
    S, f = sockets_for(torso_rel); W = conv.KB @ np.linalg.inv(S['Flat Waist'])
    N = shoulder_frame(S['Shoulder R'], S['Shoulder L']) @ NECK_IN_SH
    d = np.linalg.inv(S['Neck']) @ N
    print(torso_rel.split('/')[-1], 'vs face rule: moved %s, turned %.1f deg' % (d[:3, 3].round(2), np.degrees(np.arccos(np.clip((np.trace(d[:3, :3]) - 1) / 2, -1, 1)))))
    return [[stlcache.npz(TN + torso_rel), W.ravel().tolist(), C_T],
            [am(ARM_R), (W @ S['Shoulder R'] @ fit(ARM_R, 'Shoulder R')).ravel().tolist(), C_MF],
            [am(ARM_L), (W @ S['Shoulder L'] @ fit(ARM_L, 'Shoulder L')).ravel().tolist(), C_MF],
            [am(HELM), (W @ N @ fit(HELM, 'Neck')).ravel().tolist(), C_MF]]
ref = [[am(conv.AMT), np.eye(4).ravel().tolist(), C_MF], [am(ARM_R), (conv.S_AM['Shoulder R'] @ fit(ARM_R, 'Shoulder R')).ravel().tolist(), C_MF],
       [am(ARM_L), (conv.S_AM['Shoulder L'] @ fit(ARM_L, 'Shoulder L')).ravel().tolist(), C_MF], [am(HELM), (conv.S_AM['Neck'] @ fit(HELM, 'Neck')).ravel().tolist(), C_MF]]
models = [dict(name='D_MF', items=ref)]
for t, tag in (("TurtleNinja's Mk6 Assault Addon 1/Torsos/Mk6_Assault_Torso_A_2.stl", 'TN6'), ("TurtleNinja's Mk7-8 Builder/Mk7-8/Torsos/Mk8 Torso A 1.stl", 'TN8'),
               ("TurtleNinja's Mk10 Assault Intercessor + Jumppack Addon/Torso/Mk10_Assault_Torso_Skull_Aquilla_1.stl", 'TN10'), ("TurtleNinja's Mk2-6 Builder/Mk2/Torsos/Upper A 1.stl", 'TN2')):
    models.append(dict(name=f'D_{tag}', items=model(t)))
json.dump({"out": "/home/claude/kits/tn/rh3", "res": 420, "pad": 1.05, "models": models, "views": {"front": [0, 1, 0], "side": [1, 0, 0], "q34": [0.7, 1, 0.25]}}, open('j_head3.json', 'w'))

import sys; sys.path.insert(0,'/home/claude/kits'); sys.path.insert(0,'/home/claude/kits/cr'); sys.path.insert(0,'/home/claude/kits/tn')
import numpy as np, json, stlcache, flats
from flatface import frame
import conv
from render_cross import am, fit, ARM_R, ARM_L, HELM, PACK, C_T, C_MF, C_TN
from tn_sockets import sockets_for, face_frames
from tn_torso import torso_faces, TN
def tn_helmet_frame(path, front):
    V, T = stlcache.load(path); F = flats.flats(V, T, min_area=2.0)
    b = max([f for f in F if f[1][1] < -0.95], key=lambda f: f[0] - 0.5 * f[2][1])    # lowest big -Y face
    return frame(b[2], -b[1], front)
def model(torso_rel, helmet=None):
    S, f = sockets_for(torso_rel); W = conv.KB @ np.linalg.inv(S['Flat Waist']); Ff = face_frames(f)
    it = [[stlcache.npz(TN + torso_rel), W.ravel().tolist(), C_T],
          [am(ARM_R), (W @ S['Shoulder R'] @ fit(ARM_R, 'Shoulder R')).ravel().tolist(), C_MF],
          [am(ARM_L), (W @ S['Shoulder L'] @ fit(ARM_L, 'Shoulder L')).ravel().tolist(), C_MF]]
    if helmet is None:
        it.append([am(HELM), (W @ S['Neck'] @ fit(HELM, 'Neck')).ravel().tolist(), C_MF])
    else:
        H = tn_helmet_frame(TN + helmet, f['front']); it.append([stlcache.npz(TN + helmet), (W @ Ff['Neck'] @ np.linalg.inv(H)).ravel().tolist(), C_TN])
    return it
ref = [[am(conv.AMT), np.eye(4).ravel().tolist(), C_MF], [am(ARM_R), (conv.S_AM['Shoulder R'] @ fit(ARM_R, 'Shoulder R')).ravel().tolist(), C_MF],
       [am(ARM_L), (conv.S_AM['Shoulder L'] @ fit(ARM_L, 'Shoulder L')).ravel().tolist(), C_MF], [am(HELM), (conv.S_AM['Neck'] @ fit(HELM, 'Neck')).ravel().tolist(), C_MF]]
t6 = "TurtleNinja's Mk6 Assault Addon 1/Torsos/Mk6_Assault_Torso_A_2.stl"; t8 = "TurtleNinja's Mk7-8 Builder/Mk7-8/Torsos/Mk8 Torso A 1.stl"
models = [dict(name='h1_MF', items=ref), dict(name='h2_TN6_MFhelm', items=model(t6)), dict(name='h3_TN8_MFhelm', items=model(t8)),
          dict(name='h4_TN8_TNhelm', items=model(t8, "TurtleNinja's Mk7-8 Builder/Mk7-8/Helmets/Mk7 Helmet 1.stl"))]
json.dump({"out": "/home/claude/kits/tn/rh", "res": 520, "pad": 1.05, "models": models, "views": {"front": [0, 1, 0], "side": [1, 0, 0]}}, open('j_head.json', 'w'))

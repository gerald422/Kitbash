import sys; sys.path.insert(0,'/home/claude/kits'); sys.path.insert(0,'/home/claude/kits/cr'); sys.path.insert(0,'/home/claude/kits/tn')
import numpy as np, json, hashlib, stlcache, geo
import conv, flatface as FF
from tn_sockets import sockets_for
from tn_torso import TN
P = conv.P
def am(rel): geo.load(rel); return "/home/claude/kits/cache/" + hashlib.md5(rel.encode()).hexdigest() + ".npz"
def fit(rel, j): return np.array(P[rel]['fits'][j], float).reshape(4, 4)
A = 'AssaultMarines-V2/AssaultMarines-V2/RawSTL/'
ARM_R, ARM_L, HELM, PACK, LEGS = A + 'Arms/101-Arm-6-R-A.stl', A + 'Arms/103-Arm-6-L-A.stl', A + 'Helmet-Heads/1-Helmet-1.stl', A + 'JumpPacks/55-JumpPack-1.stl', A + 'Legs/29-Legs-2.stl'
LJ = json.load(open('/home/claude/kits/legs_josh.json'))['legs']
AD = json.load(open('/home/claude/kits/cr/ad_frames.json')); M_AD = np.array(AD['M_ad'])
S_AD_FLAT = FF.frame([3.587, AD['ring_y'], 4.135], [0, -1, 0], [0, 0, -1])
ADP = "/mnt/user-data/uploads/new cults/body adaptor/lower_body_(torso)_1.stl"
C_T, C_MF, C_TN, C_AD, C_MA = [0.9, 0.6, 0.3, 1], [0.6, 0.68, 0.85, 1], [0.8, 0.8, 0.8, 1], [0.95, 0.5, 0.15, 1], [0.7, 0.85, 0.7, 1]
def flat_legs_fit(path, front):
    V, T = stlcache.load(path); A_, nn, c, sel = FF.top_face(V, T, up=(0, 1, 0))
    return np.linalg.inv(FF.frame(c, nn, front))
def tn_model(torso_rel, legs=None, mar=True):
    S, f = sockets_for(torso_rel); W = conv.KB @ np.linalg.inv(S['Flat Waist'])
    it = [[stlcache.npz(TN + torso_rel), W.ravel().tolist(), C_T]]
    if mar:
        it += [[am(ARM_R), (W @ S['Shoulder R'] @ fit(ARM_R, 'Shoulder R')).ravel().tolist(), C_MF],
               [am(ARM_L), (W @ S['Shoulder L'] @ fit(ARM_L, 'Shoulder L')).ravel().tolist(), C_MF],
               [am(HELM), (W @ S['Neck'] @ fit(HELM, 'Neck')).ravel().tolist(), C_MF],
               [am(PACK), (W @ S['Back'] @ fit(PACK, 'Back')).ravel().tolist(), C_MF]]
    if legs is None:
        it.append([am(LEGS), (W @ S['Waist'] @ np.linalg.inv(conv.S_AM['Waist']) @ np.array(LJ[LEGS]['M'])).ravel().tolist(), C_MF])
    else:
        path, front, col = legs
        it.append([stlcache.npz(path), (W @ S['Flat Waist'] @ flat_legs_fit(path, front)).ravel().tolist(), col])
    return it
def mf_on_flat(path, front, col):
    it = [[am(conv.AMT), np.eye(4).ravel().tolist(), C_MF], [stlcache.npz(ADP), M_AD.ravel().tolist(), C_AD],
          [stlcache.npz(path), (M_AD @ S_AD_FLAT @ flat_legs_fit(path, front)).ravel().tolist(), col],
          [am(ARM_R), (conv.S_AM['Shoulder R'] @ fit(ARM_R, 'Shoulder R')).ravel().tolist(), C_MF],
          [am(ARM_L), (conv.S_AM['Shoulder L'] @ fit(ARM_L, 'Shoulder L')).ravel().tolist(), C_MF],
          [am(HELM), (conv.S_AM['Neck'] @ fit(HELM, 'Neck')).ravel().tolist(), C_MF]]
    return it
if __name__ == '__main__':
    MA = "/mnt/user-data/uploads/new cults/Marta/"
    TNL = TN + "TurtleNinja's Mk2-6 Builder/Mk6/Legs/Lower A 1.stl"
    TNL8 = TN + "TurtleNinja's Mk7-8 Builder/Mk7-8/Legs/Lower A 1.stl"
    MAL = MA + "Marta_Captain with Relic Shield/Captain with Relic Shield/legs_1.stl"
    tor = "TurtleNinja's Mk6 Assault Addon 1/Torsos/Mk6_Assault_Torso_A_2.stl"
    tor8 = "TurtleNinja's Mk7-8 Builder/Mk7-8/Torsos/Mk8 Torso A 1.stl"
    models = [
        dict(name='1_MF_reference', items=[[am(conv.AMT), np.eye(4).ravel().tolist(), C_MF], [am(LEGS), np.array(LJ[LEGS]['M']).ravel().tolist(), C_MF],
              [am(ARM_R), (conv.S_AM['Shoulder R'] @ fit(ARM_R, 'Shoulder R')).ravel().tolist(), C_MF], [am(ARM_L), (conv.S_AM['Shoulder L'] @ fit(ARM_L, 'Shoulder L')).ravel().tolist(), C_MF],
              [am(HELM), (conv.S_AM['Neck'] @ fit(HELM, 'Neck')).ravel().tolist(), C_MF], [am(PACK), (conv.S_AM['Back'] @ fit(PACK, 'Back')).ravel().tolist(), C_MF]]),
        dict(name='2_TN6_on_MF_legs', items=tn_model(tor)),
        dict(name='3_TN6_on_TN6_legs', items=tn_model(tor, (TNL, [-1, 0, 0], C_TN))),
        dict(name='4_TN8_on_TN8_legs', items=tn_model(tor8, (TNL8, [-1, 0, 0], C_TN))),
        dict(name='5_MF_adaptor_TN_legs', items=mf_on_flat(TNL, [-1, 0, 0], C_TN)),
        dict(name='6_MF_adaptor_Marta_legs', items=mf_on_flat(MAL, [0, 0, 1], C_MA)),
        dict(name='7_TN6_on_Marta_legs', items=tn_model(tor, (MAL, [0, 0, 1], C_MA))),
    ]
    json.dump({"out": "/home/claude/kits/tn/r", "res": 560, "pad": 1.1, "models": models,
               "views": {"front": [0, 1, 0], "side": [1, 0, 0], "back": [-0.5, -1, 0.3]}}, open('/home/claude/kits/tn/j_cross.json', 'w'))

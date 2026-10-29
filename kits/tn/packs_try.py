import sys; sys.path.insert(0,'/home/claude/kits'); sys.path.insert(0,'/home/claude/kits/cr'); sys.path.insert(0,'/home/claude/kits/tn'); sys.path.insert(0,'/home/claude/kits/cr/dev')
import numpy as np, json, stlcache, flats
from topface import merge_flats
from flatface import frame
import conv
from render_cross import am, fit, ARM_R, ARM_L, HELM, C_T, C_MF, C_TN
from tn_sockets import sockets_for
U = "/mnt/user-data/uploads/new cults/"; TN = U + "Turtle Ninja/"
QBI = np.linalg.inv(conv.Q['Back'])
def pack_fit(path):
    V, T = stlcache.load(path); M = merge_flats([(A, n, c) for A, n, c, o, s in flats.flats(V, T, min_area=0.5)])
    big = max([m for m in M if abs(m[1][2]) > 0.95], key=lambda m: m[0])
    P = frame(big[2], -big[1], [0, 1, 0])
    return QBI @ np.linalg.inv(P)
L = json.load(open('rp_list.json'))
tor = "TurtleNinja's Mk2-6 Builder/Mk6/Torsos/Upper A 9.stl"; S, f = sockets_for(tor); W = conv.KB @ np.linalg.inv(S['Flat Waist'])
models = []
for i, p in enumerate(L):
    F = pack_fit(U + p)
    models.append(dict(name=f'K{i}', items=[[stlcache.npz(TN + tor), W.ravel().tolist(), C_T], [stlcache.npz(U + p), (W @ S['Back'] @ F).ravel().tolist(), C_TN], [am(HELM), (W @ S['Neck'] @ fit(HELM, 'Neck')).ravel().tolist(), C_MF]]))
    models.append(dict(name=f'J{i}', items=[[am(conv.AMT), np.eye(4).ravel().tolist(), C_MF], [stlcache.npz(U + p), (conv.S_AM['Back'] @ F).ravel().tolist(), C_TN], [am(HELM), (conv.S_AM['Neck'] @ fit(HELM, 'Neck')).ravel().tolist(), C_MF]]))
json.dump({"out": "/home/claude/kits/tn/rpk", "res": 230, "pad": 1.05, "models": models, "views": {"side": [1, 0, 0], "back": [0, -1, 0.2]}}, open('j_pk.json', 'w'))

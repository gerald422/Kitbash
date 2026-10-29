import sys; sys.path.insert(0,'/home/claude/kits'); sys.path.insert(0,'/home/claude/kits/cr'); sys.path.insert(0,'/home/claude/kits/tn'); sys.path.insert(0,'/home/claude/kits/tn/oneoff')
import numpy as np, json, stlcache, flats, conv
from flatface import frame
from oneoff import belt_anchors, KB_IN_SH, inv, flat, sock
def body_sockets(V, T, up=np.array([0, 1., 0])):
    F = flats.flats(V, T, min_area=2.0); h0, h1 = (V @ up).min(), (V @ up).max(); H = h1 - h0
    big = [f for f in F[:40] if (f[2] @ up) > h0 + 0.55 * H]; pair = None
    for i in range(len(big)):
        for j in range(i + 1, len(big)):
            Ai, ni, ci = big[i][:3]; Aj, nj, cj = big[j][:3]
            if ni @ nj < -0.9 and abs(Ai - Aj) < 0.2 * max(Ai, Aj) and abs(ni @ up) < 0.6 and Ai > 8:
                if pair is None or Ai + Aj > pair[0]: pair = (Ai + Aj, i, j)
    sh = [big[pair[1]], big[pair[2]]]; ys = np.mean([s[2] @ up for s in sh])
    axis = sh[0][1] - sh[1][1]; axis /= np.linalg.norm(axis)
    side = [f for f in F if abs(f[1] @ up) < 0.3 and abs(f[1] @ axis) < 0.3 and f[0] > 3 and ys - 12 < f[2] @ up < ys + 3]
    mid = (sh[0][2] + sh[1][2]) / 2
    back = max(side, key=lambda f: f[0])
    front = -back[1]; front = front - (front @ up) * up; front /= np.linalg.norm(front)
    right = np.cross(front, up)
    shR, shL = (sh[0], sh[1]) if sh[0][1] @ right > 0 else (sh[1], sh[0])
    face = {'Shoulder R': frame(shR[2], shR[1], up), 'Shoulder L': frame(shL[2], shL[1], up), 'Back': frame(back[2], back[1], up)}
    S = {j: face[j] @ conv.Q[j] for j in face}
    SHF = conv.shoulder_frame(S['Shoulder R'], S['Shoulder L']); S['Neck'] = SHF @ conv.NECK_IN_SH
    FW = SHF @ KB_IN_SH
    P = V[(V @ up) < h0 + 0.6]; base = frame(P.mean(0), up, front)
    return S, FW, base, dict(shR=shR, shL=shL, back=back, front=front)
if __name__ == '__main__':
    D = "/mnt/user-data/uploads/new cults/Turtle Ninja/TurtleNinja's Mk4 Tactical Squad/Bodies/"
    V, T = stlcache.load(D + "Mk4_Body_A_1.stl"); S, FW, base, f = body_sockets(V, T)
    np.set_printoptions(precision=3, suppress=True)
    for k in ('shR', 'shL', 'back'): print(k, f[k][0], f[k][1], f[k][2])
    for k, M in S.items(): print(k, M[:3, 3])
    print('FW', FW[:3, 3], 'base', base[:3, 3])
    sys.path.insert(0, '/home/claude/kits/tn'); from render_cross import am, fit, ARM_R, ARM_L, HELM, C_T, C_MF
    U = conv.KB @ inv(FW); L = lambda x: x.ravel().tolist()
    items = [[stlcache.npz(D + "Mk4_Body_A_1.stl"), L(U), C_T]]
    for rel, j in ((ARM_R, 'Shoulder R'), (ARM_L, 'Shoulder L'), (HELM, 'Neck'), (conv.AMT if False else HELM, 'Neck')):
        items.append([am(rel), L(U @ S[j] @ fit(rel, j)), C_MF])
    json.dump({"out": "/home/claude/kits/tn/mk4b/r", "res": 300, "pad": 1.05, "models": [dict(name='b', items=items)],
               "views": {"front": [0, 1, 0.1], "side": [1, 0, 0.1], "back": [0.3, -1, 0.2]}}, open('j.json', 'w'))

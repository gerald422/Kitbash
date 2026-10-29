import sys; sys.path.insert(0,'/home/claude/kits'); sys.path.insert(0,'/home/claude/kits/cr'); sys.path.insert(0,'/home/claude/kits/cr/dev'); sys.path.insert(0,'/home/claude/kits/tn')
import numpy as np, json, stlcache as sc, flats, conv
from topface import merge_flats
from flatface import frame
QIR = np.linalg.inv(conv.Q['Shoulder R'])
def shoulder_pair(V, T):
    M = merge_flats([(a, n, c) for a, n, c, o, s in flats.flats(V, T, min_area=1.0)])
    cand = [m for m in M if abs(m[1][0]) > 0.98 and m[0] > 10]
    best = None
    for i, (a1, n1, c1) in enumerate(cand):
        for a2, n2, c2 in cand[i + 1:]:
            if n1 @ n2 > -0.97: continue
            d = c2[0] - c1[0]
            # facing each other: the +X face is on the low-x side
            if (n1[0] > 0 and d < 0) or (n1[0] < 0 and d > 0): continue
            if not (9 < abs(d) < 15) or abs(c1[1] - c2[1]) > 2.5 or abs(c1[2] - c2[2]) > 2.5: continue
            s = a1 + a2
            if best is None or s > best[0]: best = (s, (a1, n1, c1), (a2, n2, c2))
    if best is None: return None
    f1, f2 = best[1], best[2]
    R, L = (f1, f2) if f1[1][0] > 0 else (f2, f1)      # Marta: the model's right is -X, its face points +X
    return R, L
def set_fit(V, T):
    pr = shoulder_pair(V, T)
    if pr is None: return None, None
    R, L = pr
    return QIR @ np.linalg.inv(frame(R[2], -R[1], [0, 1, 0])), pr
if __name__ == '__main__':
    from tn_sockets import sockets_for
    from render_cross import am, fit, HELM, C_T, C_MF
    D = "/mnt/user-data/uploads/new cults/Marta/51 May 2026-20260612T074408Z-3-001/51 May 2026/amrs and weapons/"
    TN = "/mnt/user-data/uploads/new cults/Turtle Ninja/"; tor = "TurtleNinja's Mk2-6 Builder/Mk6/Torsos/Upper A 9.stl"; S, f = sockets_for(tor); W = conv.KB @ np.linalg.inv(S['Flat Waist'])
    Lm = lambda x: x.ravel().tolist(); models = []
    for n in ("set_arms_1_with_weapon_1", "set_arms_2_with_weapon_2"):
        V, T = sc.load(D + n + ".stl"); F, pr = set_fit(V, T)
        print(n, 'R face A %.1f c %s  L face A %.1f c %s' % (pr[0][0], pr[0][2].round(2), pr[1][0], pr[1][2].round(2)))
        # where the L face lands relative to the torso's Shoulder L
        Pw = W @ S['Shoulder R'] @ F; Lw = Pw @ np.append(pr[1][2], 1); print('   L face off the Shoulder L socket by %.2f mm' % np.linalg.norm(Lw[:3] - (W @ S['Shoulder L'])[:3, 3]))
        models.append(dict(name=n, items=[[sc.npz(TN + tor), Lm(W), C_T], [sc.npz(D + n + ".stl"), Lm(Pw), C_MF], [am(HELM), Lm(W @ S['Neck'] @ fit(HELM, 'Neck')), [0.95, 0.5, 0.15, 1]]]))
        Pa = conv.S_AM['Shoulder R'] @ F; La = Pa @ np.append(pr[1][2], 1); print('   on the Mar Fil torso: L face off by %.2f mm' % np.linalg.norm(La[:3] - conv.S_AM['Shoulder L'][:3, 3]))
    json.dump({"out": "/home/claude/kits/marta/r2a", "res": 320, "pad": 1.05, "models": models, "views": {"front": [0.2, 1, 0.15], "side": [1, 0.1, 0.1], "top": [0, 0.3, 1]}}, open('j2a.json', 'w'))

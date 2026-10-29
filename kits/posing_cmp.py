import geo, numpy as np, json, os
from scipy.spatial import cKDTree
EX = '/home/claude/blend/posing/ex/'
info = json.load(open(EX + 'info.json'))
A = 'AssaultMarines-V2/AssaultMarines-V2/RawSTL/'
def raw_to_local(obj, rel):
    z = np.load(EX + obj + '.npz'); W = z['V'].astype(float); U = z['T']
    V, T = geo.load(rel); V = V.astype(float)
    src = geo.surf(V, T, 4000); S = geo.surf(W, U, 200000); tree = cKDTree(S)
    # try identity + translation first
    best = None
    for R0 in [np.eye(3)] + geo.F.rots24():
        t0 = S.mean(0) - (src @ R0.T).mean(0)
        R, t, d = geo.icp(src, tree, S, R0, t0, 30)
        if best is None or np.median(d) < best[0]: best = (np.median(d), R, t)
        if best[0] < 0.06: break
    R, t, d = geo.icp(src, tree, S, best[1], best[2], 80)
    return geo.M4(R, t), float(np.median(d))
MW = lambda n: np.array(info[n]['mw'])
out = {}
if __name__ == '__main__':
    Tt, mt = raw_to_local('23-Torso-2.001', A + 'Chest/23-Torso-2.stl'); print('torso 23 T rot %.2f t %s med %.4f' % (geo.ang(Tt[:3, :3]), np.round(Tt[:3, 3], 3), mt))
    T27, m27 = raw_to_local('27-Torso-6', A + 'Chest/27-Torso-6.stl'); print('torso 27 T rot %.2f t %s med %.4f' % (geo.ang(T27[:3, :3]), np.round(T27[:3, 3], 3), m27))
    L = json.load(open('lip_seat2.json'))
    for torso, Tto, legs in (('23-Torso-2.001', Tt, '47-Legs-8-A'), ('27-Torso-6', T27, '39-Legs-4-A')):
        rel = A + 'Legs(JumpPack)/' + legs + '.stl'
        TL, mL = raw_to_local(legs, rel)
        Mj = np.linalg.inv(MW(torso) @ Tto) @ MW(legs) @ TL        # legs raw -> torso raw (Josh)
        Mm = np.array(L[rel]['M'])
        D = Mj @ np.linalg.inv(Mm)
        print('%s on %s: legs T med %.4f | Josh vs my lip match: rot %.2f deg, shift at waist %s' % (torso, legs, mL, geo.ang(D[:3, :3]), np.round(D[:3, :3] @ [0, 2, 26.5] + D[:3, 3] - [0, 2, 26.5], 2)))
        out[legs] = {'josh': Mj.tolist(), 'mine': Mm.tolist()}
    json.dump(out, open('posing_cmp.json', 'w'), indent=1)

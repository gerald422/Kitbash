"""Reference fist: the surface common to several Mar Fil hand-held parts (the hand itself, not the weapon), in the hand frame."""
import sys; sys.path.insert(0, '/home/claude/kits')
import geo, json, numpy as np, os
from scipy.spatial import cKDTree
side = json.load(open('/home/claude/kits/amv2_partial.json'))['side']
def rel_of(stem):
    return [r for r in side if os.path.basename(r)[:-4] == stem][0]
def Hof(rel, sd='R'):
    return np.linalg.inv(np.array(side[rel]['fits']['Hand ' + sd]).reshape(4, 4))
if __name__ == '__main__':
    names = ['211-BoltPistol-R', '178-CombatKnife-1-R', '175-ChainSword-1-R', '193-PowerHammer-A-1-R', '199-PowerSpear-1-R',
             '212-HeavyBoltPistol-R', '186-PowerAxe-A-3-R', '198-PowerHammer-B-3-R', '177-ChainSword-3-R', '182-Esvicerator-2-R', '211-Shield-R']
    H0 = Hof(rel_of(names[0]))
    data = {}
    for n in names:
        r = rel_of(n); V, T = geo.load(r); H = Hof(r)
        print('%-24s frame vs pistol: %.2f deg %.3f mm' % (n, geo.ang(H0[:3, :3].T @ H[:3, :3]), np.linalg.norm(H[:3, 3] - H0[:3, 3])))
        S = geo.surf(V, T, 200000)
        L = (S - H[:3, 3]) @ H[:3, :3]          # in that part's hand frame
        data[n] = (S, L, cKDTree(L))
    # fist region of the pistol in its hand frame
    S0, L0, _ = data[names[0]]
    box = (L0[:, 1] > -6) & (L0[:, 1] < 0.4) & (np.linalg.norm(L0[:, [0, 2]], axis=1) < 4.5)
    P = L0[box]
    print('pistol fist box points', len(P))
    for n in names[1:]:
        d, _ = data[n][2].query(P)
        print('  %-24s share %.0f%% of the pistol fist within 0.08' % (n, 100 * np.mean(d < 0.08)))

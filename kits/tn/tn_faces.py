import sys; sys.path.insert(0,'/home/claude/kits'); sys.path.insert(0,'/home/claude/kits/cr')
import numpy as np, json, os, stlcache, flats
TN = "/mnt/user-data/uploads/new cults/Turtle Ninja/"
def faces(V, T):
    F = flats.flats(V, T, min_area=2.0)
    bot = F[0]; up = -bot[1]
    big = F[:20]; pair = None
    for i in range(len(big)):
        for j in range(i + 1, len(big)):
            Ai, ni, ci = big[i][:3]; Aj, nj, cj = big[j][:3]
            if ni @ nj < -0.9 and abs(Ai - Aj) < 0.2 * max(Ai, Aj) and abs(ni @ up) < 0.6:
                if pair is None or Ai + Aj > pair[0]: pair = (Ai + Aj, i, j)
    _, i, j = pair; sh = [F[i], F[j]]
    axis = sh[0][1] - sh[1][1]; axis /= np.linalg.norm(axis)
    side = [f for f in F if abs(f[1] @ up) < 0.3 and abs(f[1] @ axis) < 0.3 and f[0] > 3]
    tops = [f for f in F if f[1] @ up > 0.8 and f is not bot]
    return bot, up, sh, axis, side, tops
if __name__ == '__main__':
    for p in json.load(open('flat_torsos.json'))[:int(sys.argv[1]) if len(sys.argv) > 1 else None]:
        V, T = stlcache.load(TN + p)
        bot, up, sh, axis, side, tops = faces(V, T)
        lo, hi = V.min(0), V.max(0); cen = (lo + hi) / 2
        print(p.split('/')[-1], 'bottom %.1f n %s c %s | shoulders %.1f/%.1f axis %s' % (bot[0], bot[1].round(2), bot[2].round(2), sh[0][0], sh[1][0], axis.round(2)))
        print('   side faces:', [(round(f[0], 1), f[1].round(2).tolist(), round(float((f[2] - cen) @ f[1]), 2)) for f in side[:4]])
        print('   up faces:', [(round(f[0], 1), round(float(f[2] @ up), 2), round(float(np.linalg.norm((f[2] - bot[2]) - ((f[2] - bot[2]) @ up) * up)), 2)) for f in tops[:4]], 'height %.2f' % float((hi - lo) @ np.abs(up)))

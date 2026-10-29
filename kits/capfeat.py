import sys; sys.path.insert(0, '/home/claude/kits')
import geo, numpy as np, os, json, wristrule as W
from fist import side, Hof
def feats(V, T, c, nn, r, ring):
    cen, n, a = W.tri_info(V, T)
    L = cen - c; h = L @ nn; lat = np.linalg.norm(L - h[:, None] * nn, axis=1)
    fist = a[(np.linalg.norm(L + 2.5 * nn, axis=1) < 3.5)].sum()            # surface area of the blob just behind
    sl = (h < -1.5) & (h > -3.5)
    spread = np.quantile(lat[sl], 0.9) if sl.any() else 0
    neck = (h < -0.2) & (h > -1.2); neckr = np.median(lat[neck & (lat < 3)]) if (neck & (lat < 3)).any() else 0
    X0 = np.cross(nn, [0, 0, 1.0]) if abs(nn[2]) < 0.9 else np.cross(nn, [1.0, 0, 0]); X0 /= np.linalg.norm(X0); Z0 = np.cross(X0, nn)
    Q = np.c_[(ring - c) @ X0, (ring - c) @ Z0]; Q -= Q.mean(0); w = np.linalg.eigvalsh(np.cov(Q.T))
    return dict(r=r, fist=fist, spread=spread, neckr=neckr, aspect=float(np.sqrt(w[1] / max(w[0], 1e-9))))
if __name__ == '__main__':
    rows = []
    files = sorted(r for r, d in side.items() if d.get('category') in ('Melee', 'Pistols', 'Shields'))
    for rel in files:
        sd = 'L' if 'Left' in rel else 'R'
        V, T = geo.load(rel); V = np.asarray(V, float); Hj = Hof(rel, sd)
        for score, c, nn, r, ring in W.stub_caps(V, T):
            f = feats(V, T, c, nn, r, ring); f['ok'] = bool(np.linalg.norm(c - Hj[:3, 3]) < 0.8); f['part'] = os.path.basename(rel); f['score'] = score
            rows.append(f)
    json.dump(rows, open('/home/claude/kits/capfeat.json', 'w'))
    import collections
    for ok in (True, False):
        R = [x for x in rows if x['ok'] == ok]
        print('ok' if ok else 'wrong', len(R))
        for k in ('r', 'fist', 'spread', 'neckr', 'aspect', 'score'):
            v = np.array([x[k] for x in R]); print('   %-7s min %.2f  q10 %.2f  med %.2f  q90 %.2f  max %.2f' % (k, v.min(), *np.quantile(v, [.1, .5, .9]), v.max()))

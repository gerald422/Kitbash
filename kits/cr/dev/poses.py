"""Run on the device: score how 'flat' (axis-aligned) each torso pose is. usage: python3 poses.py <dir> [dir...]"""
import sys, os, re, numpy as np, json, collections
def stl(p):
    b = open(p, 'rb').read()
    n = int.from_bytes(b[80:84], 'little')
    if 84 + 50 * n == len(b):
        a = np.frombuffer(b, dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('x', '<u2')]), count=n, offset=84)
        return a['v'].astype(float)
    tri = []; cur = []
    for line in b.decode('latin1').splitlines():
        s = line.split()
        if s and s[0] == 'vertex':
            cur.append([float(x) for x in s[1:4]])
            if len(cur) == 3: tri.append(cur); cur = []
    return np.array(tri, float)
def flats(F, min_area=4.0, tol=0.02):
    e1 = F[:, 1] - F[:, 0]; e2 = F[:, 2] - F[:, 0]; c = np.cross(e1, e2); a = np.linalg.norm(c, axis=1) / 2
    ok = a > 1e-12; n = np.zeros_like(c); n[ok] = c[ok] / (2 * a[ok, None]); cen = F.mean(1)
    key = np.round(n / tol).astype(int); g = collections.defaultdict(list)
    for i, k in enumerate(map(tuple, key)):
        if ok[i]: g[k].append(i)
    out = []
    for k, idx in g.items():
        idx = np.array(idx)
        if a[idx].sum() < min_area: continue
        nn = (n[idx] * a[idx, None]).sum(0); nn /= np.linalg.norm(nn); off = cen[idx] @ nn
        for o in np.unique(np.round(off / 0.05)):
            sel = idx[np.abs(off / 0.05 - o) < 0.6]; A = a[sel].sum()
            if A >= min_area: out.append((float(A), nn, (cen[sel] * a[sel, None]).sum(0) / A))
    out.sort(key=lambda r: -r[0]); return out
def axis_dev(nv):
    return float(np.degrees(np.arccos(min(1.0, np.abs(nv).max()))))
res = {}
for d in sys.argv[1:]:
    for f in sorted(os.listdir(d)):
        if not f.lower().endswith('.stl'): continue
        p = os.path.join(d, f); F = stl(p); FL = flats(F)
        # biggest faces that are not the bottom (the largest)
        big = FL[:12]
        pair = None
        for i in range(len(big)):
            for j in range(i + 1, len(big)):
                Ai, ni, ci = big[i]; Aj, nj, cj = big[j]
                if ni @ nj < -0.9 and abs(Ai - Aj) < 0.2 * max(Ai, Aj) and abs(ni @ FL[0][1]) < 0.6:
                    if pair is None or Ai + Aj > pair[0]: pair = (Ai + Aj, ni, nj, ci, cj)
        if pair is None:
            res[p] = dict(score=99.0, dev=[], areas=[round(A, 1) for A, nv, c in big[:4]], normals=[nv.round(3).tolist() for A, nv, c in big[:4]])
        else:
            dev = [axis_dev(pair[1]), axis_dev(pair[2])]
            res[p] = dict(score=round(sum(dev), 2), dev=[round(x, 1) for x in dev], areas=[round(pair[0] / 2, 1)], normals=[pair[1].round(3).tolist(), pair[2].round(3).tolist()],
                          centres=[pair[3].round(2).tolist(), pair[4].round(2).tolist()], bottom=[FL[0][1].round(3).tolist(), FL[0][2].round(2).tolist(), round(FL[0][0], 1)])
        print('%-50s score %6.2f  dev %s' % (f, res[p]['score'], res[p]['dev']), flush=True)
json.dump(res, open(os.path.expanduser('~/poses_out.json'), 'w'), indent=0)

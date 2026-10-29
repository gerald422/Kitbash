import sys, numpy as np, collections
sys.path.insert(0, '/home/claude/kits'); sys.path.insert(0, '/home/claude/kits/cr')
import disc, stlcache
def flats(V, T, min_area=3.0, tol=0.02):
    """planar patches: group faces by normal (rounded) and plane offset; return [(area, normal, centroid, offset)]"""
    cen, n, a = disc.tri_info(V, T)
    key = np.round(n / tol).astype(int)
    out = []
    g = collections.defaultdict(list)
    for i, k in enumerate(map(tuple, key)): g[k].append(i)
    for k, idx in g.items():
        idx = np.array(idx)
        if a[idx].sum() < min_area: continue
        nn = (n[idx] * a[idx, None]).sum(0); nn /= np.linalg.norm(nn)
        off = cen[idx] @ nn
        for o in np.unique(np.round(off / 0.05)):
            sel = idx[np.abs(off / 0.05 - o) < 0.6]
            A = a[sel].sum()
            if A >= min_area:
                out.append((A, nn, (cen[sel] * a[sel, None]).sum(0) / A, o * 0.05, sel))
    out.sort(key=lambda r: -r[0])
    return out
if __name__ == '__main__':
    for p in sys.argv[1:]:
        V, T = stlcache.load(p)
        F = flats(V, T)
        print(p.split('/')[-1], "bbox", V.min(0).round(1), V.max(0).round(1))
        for A, nn, c, o, sel in F[:5]: print("   area %.1f  n %s  c %s" % (A, nn.round(3), c.round(2)))

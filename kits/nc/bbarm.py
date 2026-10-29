import numpy as np, os
from geo import *
def all_flats(V, F, cos=0.995, min_area=2.0):
    n, ar, c = tri(V, F)
    # candidate normals from area-weighted clustering on a sphere grid
    out = []
    used = np.zeros(len(F), bool)
    order = np.argsort(-ar)
    dirs = []
    # coarse direction histogram
    q = np.round(n * 6).astype(int)
    keys, inv = np.unique(q, axis=0, return_inverse=True)
    w = np.bincount(inv.ravel(), ar)
    for k in np.argsort(-w)[:30]:
        d = (n[inv.ravel() == k] * ar[inv.ravel() == k, None]).sum(0); d /= np.linalg.norm(d)
        for A, cen, nn, g in flats(V, F, d, cos=cos, min_area=min_area):
            if used[g].mean() > 0.5: continue
            used[g] = True
            P = outline(V, F, g); cc, r, rms = circle_fit(P, nn)
            out.append(dict(A=A, c=cen, n=nn, r=r, rms=rms, cc=cc, nf=len(g)))
    return sorted(out, key=lambda d: -d['A'])
if __name__ == "__main__":
    import sys
    for f in key_files(sys.argv[1]):
        V, F = load(f)
        print(os.path.basename(f)[:-4].split('__')[-1])
        for d in all_flats(V, F)[:4]:
            print('   A %5.1f  c %s  n %s  circle r %.2f rms %.2f' % (d['A'], np.round(d['c'], 2), np.round(d['n'], 2), d['r'], d['rms']))

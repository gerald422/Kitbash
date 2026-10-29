import sys; sys.path.insert(0, '/home/claude/kits')
import geo, glob, os, numpy as np
roots = {'VS': ['/home/claude/raw/VeteranSquad/VeteranSquad/'], 'VBS': [geo.U + 'VeteranBladeSquad/VeteranBladeSquad/']}
for kit, rs in roots.items():
    for r in rs:
        dirs = sorted(set(os.path.dirname(f) for f in glob.glob(r + '**/*.stl', recursive=True)))
        for d in dirs:
            if any(k in d for k in ('Accesories', 'NewBits', 'Additional')): continue
            fs = sorted(glob.glob(d + '/*.stl'))
            lo = []; hi = []
            for f in fs[:4]:
                V, T = geo.load(f[len(geo.RAW):] if f.startswith(geo.RAW) else f[len(geo.U):])
                lo.append(V.min(0)); hi.append(V.max(0))
            lo = np.array(lo); hi = np.array(hi)
            print('%-3s %-45s n=%2d  x %6.1f..%6.1f y %6.1f..%6.1f z %6.1f..%6.1f  (first: %s)' % (kit, d.split('Squad/')[-1][-45:], len(fs), lo[:, 0].min(), hi[:, 0].max(), lo[:, 1].min(), hi[:, 1].max(), lo[:, 2].min(), hi[:, 2].max(), os.path.basename(fs[0])))

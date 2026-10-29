#!/usr/bin/env python3
"""Bounding box / centroid / triangle count of STLs (binary or ascii) -> json lines."""
import os, sys, json, numpy as np, time
def read_stl(p):
    with open(p, 'rb') as f:
        head = f.read(84)
        n = int(np.frombuffer(head[80:84], '<u4')[0])
        size = os.path.getsize(p)
        if size == 84 + 50 * n:
            dt = np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')])
            d = np.fromfile(f, dt, n)
            return d['v'].reshape(-1, 3)
    txt = open(p, 'r', errors='ignore').read()
    vs = [l.split()[1:4] for l in txt.splitlines() if l.strip().startswith('vertex')]
    return np.array(vs, float)
out = open(sys.argv[1], 'a')
done = {json.loads(l)['p'] for l in open(sys.argv[1])} if os.path.getsize(sys.argv[1]) else set()
t0 = time.time()
for p in sys.argv[2:]:
    if p in done or not p.lower().endswith('.stl'):
        continue
    if time.time() - t0 > 150:
        break
    V = read_stl(p)
    lo, hi = V.min(0), V.max(0)
    out.write(json.dumps({'p': p, 'n': len(V) // 3, 'lo': lo.round(3).tolist(), 'hi': hi.round(3).tolist(),
                          'c': V.mean(0).round(3).tolist()}) + '\n'); out.flush()

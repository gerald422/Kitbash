#!/usr/bin/env python3
"""Weld + vertex-cluster STLs to a grid (mm) and save V,F as compressed npz.
    decim.py <out dir> <grid> <root> <list file>   (paths in list relative to root)"""
import os, sys, numpy as np, time
out, g, root, lst = sys.argv[1], float(sys.argv[2]), sys.argv[3], sys.argv[4]
def read_stl(p):
    with open(p, 'rb') as f:
        head = f.read(84)
        n = int(np.frombuffer(head[80:84], '<u4')[0])
        if os.path.getsize(p) == 84 + 50 * n:
            dt = np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')])
            return np.fromfile(f, dt, n)['v'].reshape(-1, 3).astype(np.float64)
    txt = open(p, 'r', errors='ignore').read()
    return np.array([l.split()[1:4] for l in txt.splitlines() if l.strip().startswith('vertex')], float)
t0 = time.time()
os.makedirs(out, exist_ok=True)
for rel in [l.strip() for l in open(lst) if l.strip()]:
    name = rel.replace('/', '__')[:-4] + '.npz'
    dst = os.path.join(out, name)
    if os.path.exists(dst):
        continue
    if time.time() - t0 > 150:
        print('time up'); break
    P = read_stl(os.path.join(root, rel))
    q = np.round(P / g).astype(np.int64)
    key, inv = np.unique(q, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    # cluster representative = mean of member points
    V = np.zeros((len(key), 3)); np.add.at(V, inv, P); V /= np.bincount(inv)[:, None]
    F = inv.reshape(-1, 3)
    F = F[(F[:, 0] != F[:, 1]) & (F[:, 1] != F[:, 2]) & (F[:, 0] != F[:, 2])]
    np.savez_compressed(dst, V=V.astype(np.float32), F=F.astype(np.int32), n0=len(P) // 3)
    print('%7d -> %7d  %s' % (len(P) // 3, len(F), rel))

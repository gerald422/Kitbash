import numpy as np, json, os, sys
sys.path.insert(0, os.path.dirname(__file__)); from settle_lib import settle
L = "/mnt/user-data/uploads/d/Kitbash Library/"
idx = {p['name']: p for p in json.load(open(L + "_builder/index.json", encoding="utf-8"))['parts']}
def load(p):
    d = open(p, 'rb').read(); n = int.from_bytes(d[80:84], 'little')
    a = np.frombuffer(d[84:84 + 50 * n], dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]))
    return a['v'].astype(float)
def prev(name):
    b = open(L + "_builder/" + idx[name]['prev'], 'rb').read()
    nv, nt = int.from_bytes(b[4:8], 'little'), int.from_bytes(b[8:12], 'little')
    V = np.frombuffer(b, '<f4', nv * 3, 12).reshape(-1, 3).astype(float); I = np.frombuffer(b, '<u4', nt * 3, 12 + nv * 12).reshape(-1, 3)
    return V[I]
def M(a): return np.array(a, float).reshape(4, 4)
def xf(T, A): return (A.reshape(-1, 3) @ T[:3, :3].T + T[:3, 3]).reshape(-1, 3, 3)
for lg in ["MarFil Assault - Legs 6A", "MarFil Intercessor - Legs 10", "MarFil Assault - Legs 1A", "Marta May 2026 - Legs 1"]:
    p = idx[lg]; S = M([s['m'] for s in p['sockets'] if s['t'] == 'Base'][0])
    full = xf(np.linalg.inv(S), load(L + p['path'].replace('\\', '/'))); pv = xf(np.linalg.inv(S), prev(lg))
    for bn in ["32_mm_1", "Textured Base", "Base (Chaplain)", "base 40mm", "Base (IronFather)", "50mm_base_1.1", "40_mm_1"]:
        b = idx[bn]; F = M(b['fits']['Base'])
        gf = settle(full, xf(F, load(L + b['path'].replace('\\', '/')))); gp = settle(pv, xf(F, prev(bn)))
        print("%-30s %-18s full %6s  preview %6s" % (lg, bn, "-" if gf is None else "%.2f" % gf, "-" if gp is None else "%.2f" % gp))

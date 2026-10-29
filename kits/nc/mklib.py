"""Test library from the decimated meshes: <LIB>/<creator path>.stl (+ sidecars from a dict)."""
import numpy as np, os, json, glob, sys
NPZ = "/home/claude/kits/nc/npz"; LIB = "/home/claude/test/nclib"
def write_stl(path, V, F):
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]
    dt = np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')])
    d = np.zeros(len(F), dt); d['n'] = n; d['v'] = np.stack([a, b, c], 1); 
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(b'\0' * 80); f.write(np.uint32(len(F)).tobytes()); f.write(d.tobytes())
def build(sides):
    for rel, side in sides.items():
        key = rel[:-4].replace('/', '__') + '.npz'
        src = os.path.join(NPZ, key)
        if not os.path.exists(src): print('missing', key); continue
        dst = os.path.join(LIB, rel)
        if not os.path.exists(dst):
            d = np.load(src); write_stl(dst, d['V'].astype(float), d['F'])
        json.dump(side, open(dst[:-4] + '.sockets.json', 'w'), indent=1)
if __name__ == "__main__":
    sides = {}
    for f in sys.argv[1:]:
        d = json.load(open(f)); d = d.get('side', d); sides.update(d)
    build(sides); print(len(sides))

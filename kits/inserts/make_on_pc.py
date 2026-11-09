"""Run on Josh's PC (device shell, numpy): write the library's insert STLs from the maker's files with Josh's scale
baked in - the same code as build.py, so no 300 MB transfer.  python3 make_on_pc.py PLAN.json NEW_CULTS LIBRARY
PLAN: {"D": [sx, sy, sz], "inserts": [[library rel path, "Inserts\\<set>\\<n>.stl"], ...]}; refuses to overwrite."""
import json, os, sys, numpy as np
plan, NC, LIB = sys.argv[1:4]; P = json.load(open(plan)); D = np.array(P["D"], float)
def stl_read(p):
    d = np.fromfile(p, dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]), offset=84)
    return d['v'].astype(float)
def stl_write(p, T):
    T = np.asarray(T, float); n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    l = np.linalg.norm(n, axis=1); n[l > 0] /= l[l > 0, None]
    rec = np.zeros(len(T), dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]))
    rec['n'] = n; rec['v'] = T
    with open(p, 'xb') as f:
        f.write(b'Kitbash Library'.ljust(80, b' ')); f.write(np.uint32(len(T)).tobytes()); f.write(rec.tobytes())
for dst, src in P["inserts"]:
    out = os.path.join(LIB, dst); os.makedirs(os.path.dirname(out), exist_ok=True)
    stl_write(out, stl_read(os.path.join(NC, src.replace("\\", "/"))) * D)
print("wrote", len(P["inserts"]))

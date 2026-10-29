"""Add the second Mar Fil shin family (29-32) and Marta's shin pads to the pad test library."""
import json, os, numpy as np
M = json.load(open('/home/claude/blend/forclaude/fc_meshes.json')); Z = np.load('/home/claude/blend/forclaude/fc_meshes.npz')
LIB = '/home/claude/test/padlib'
def stl(name, rel):
    k = M[name]['key']; V = Z[k + '_v'].astype(np.float32); T = Z[k + '_t']
    tri = V[T]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    rec = np.zeros(len(T), dtype=[("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]); rec["n"] = n; rec["v"] = tri.reshape(-1, 9)
    p = os.path.join(LIB, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'wb') as f:
        f.write(b'\0' * 80 + np.uint32(len(T)).tobytes()); f.write(rec.tobytes())
    print(rel, len(T))
for n in ['29-Shin-Pad-1', '30-Shin-Pad-2', '31-Shin-Pad-3', '32-Shin-Pad-4']:
    stl(n, f'Mar Fil - Tacticus/Kit B/Knee Pads/{n}.stl')
for n in ['71-ShinPad-4', '72-ShinPad-5', '73-ShinPad-6']:
    stl(n, f'Mar Fil - Tacticus/Kit/Knee Pads/{n}.stl')
for n in ['Chin_pad_1_R', 'Chin_pad_2_L', 'Chin_pad_2_R', 'Chin_pad_3_L', 'Chin_pad_3_R']:
    stl(n, f'Marta PunkGirl - Mk10/Kit/ShinPads-RawSTL/{n}.stl')

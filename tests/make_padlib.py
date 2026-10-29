"""A small library of raw creator files (as they arrive) from 'for claude.blend', plus
lifted torso/arms from the actual file, for the pad tests."""
import json, os, shutil, numpy as np
M = json.load(open('/home/claude/blend/forclaude/fc_meshes.json')); Z = np.load('/home/claude/blend/forclaude/fc_meshes.npz')
LIB = '/home/claude/test/padlib'
shutil.rmtree(LIB, ignore_errors=True)
def stl(name, rel):
    k = M[name]['key']; V = Z[k + '_v'].astype(np.float32); T = Z[k + '_t']
    tri = V[T]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    rec = np.zeros(len(T), dtype=[("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]); rec["n"] = n; rec["v"] = tri.reshape(-1, 9)
    p = os.path.join(LIB, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'wb') as f:
        f.write(b'\0' * 80 + np.uint32(len(T)).tobytes()); f.write(rec.tobytes())
for n in ['29-Legs-2', '35-Legs-2-A']:
    stl(n, f'Mar Fil - Tacticus/Kit/Legs/{n}.stl')
for n in ['68-ShinPad-1', '69-ShinPad-2', '70-ShinPad-3']:
    stl(n, f'Mar Fil - Tacticus/Kit/Knee Pads/{n}.stl')
for n in ['56-ShoulderPad-1', '57-ShoulderPad-2', '58-ShoulderPad-3']:
    stl(n, f'Mar Fil - Tacticus/Kit/Shoulder Pads/{n}.stl')
for n in ['230-Accessory-1', '231-Accessory-2']:
    stl(n, f'Mar Fil - Tacticus/Kit/Accessories/{n}.stl')
src = '/home/claude/liblift_v3/Mar Fil - Tacticus/AssaultMarines-V2'
for rel in ['Chests/23-Torso-2.stl', 'Chests/23-Torso-2.sockets.json', 'Arms/77-Arm-1-R-B.stl', 'Arms/77-Arm-1-R-B.sockets.json',
            'Arms/126-Arm-11-R-A.stl']:
    d = os.path.join(LIB, 'Mar Fil - Tacticus/AssaultMarines-V2', rel); os.makedirs(os.path.dirname(d), exist_ok=True)
    if os.path.exists(os.path.join(src, rel)): shutil.copy(os.path.join(src, rel), d)
    else: print('missing', rel)
shutil.copy('/home/claude/tiow_blender/_library.json', os.path.join(LIB, '_library.json'))
for r, ds, fs in os.walk(LIB):
    for f in fs: print(os.path.relpath(os.path.join(r, f), LIB))

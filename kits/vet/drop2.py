"""Gap under the chest's rim (outside the waist plug) when the chest sits where Mar Fil exported it."""
import bpy, sys, json, glob, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import importlib.util
spec = importlib.util.spec_from_file_location('ti', '/home/claude/tiow_blender/tiow_inbox.py'); T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
RAW = '/home/claude/raw/'; UP = '/mnt/user-data/uploads/new cults/All Mar All the time/'
KITS = {'VS': (RAW, 'VeteranSquad/VeteranSquad/Body/'), 'VBS': (UP, 'VeteranBladeSquad/VeteranBladeSquad/Body/')}
AX = np.array([0.0, 0.571]); WZ = 29.307
out = {}
for kit, (base, sub) in KITS.items():
    files = sorted(glob.glob(base + sub + '*/*.stl'))
    chests = [f for f in files if 'Chest' in os.path.basename(f)]
    legs = [f for f in files if f not in chests]
    csamp = {}
    for c in chests:
        V, Tr = T.read_stl_np(c); S = T._surface_sample(V, Tr, 120000)
        r = np.linalg.norm(S[:, :2] - AX, axis=1)
        csamp[c] = S[(S[:, 2] < WZ + 1.0) & (r > float(sys.argv[1]) if len(sys.argv) > 1 else r > 3.6)]
    for l in legs:
        V, Tr = T.read_stl_np(l); tree = BVHTree.FromPolygons(V.tolist(), Tr.tolist())
        res = {}
        for c, S in csamp.items():
            gaps = []; pen = 0
            for p in S[::2]:
                q, n, _i, d = tree.find_nearest(Vector(p))
                if q is not None and (Vector(p) - q).dot(n) < 0 and d < 0.6: pen += 1; continue
                hit = tree.ray_cast(Vector(p), Vector((0.0, 0.0, -1.0)), 8.0)
                if hit[0] is not None: gaps.append(hit[3])
            g = np.array(gaps)
            res[os.path.basename(c)[:-4]] = (float(g.min()) if len(g) else None, int(pen), float(np.quantile(g, 0.02)) if len(g) else None)
        drop = min(v[0] for v in res.values() if v[0] is not None)
        anypen = max(v[1] for v in res.values())
        out[l[len(base):]] = {'drop': drop, 'per_chest': res}
        print('%-4s %-28s rim gap min %.2f mm (2%% %.2f) | rim points already in the legs: %d' % (kit, os.path.basename(l), drop, min(v[2] for v in res.values() if v[2] is not None), anypen), flush=True)
json.dump(out, open('/home/claude/kits/vet/drop2.json', 'w'), indent=1)

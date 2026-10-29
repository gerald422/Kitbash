"""Vet / Bladeguard: chest in Mar Fil's export position, lowered straight down (torso -Z) until it first touches the legs.
For each legs piece, the smallest drop over every chest of its kit (so no chest of the kit cuts in)."""
import bpy, sys, json, glob, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import importlib.util
spec = importlib.util.spec_from_file_location('ti', '/home/claude/tiow_blender/tiow_inbox.py'); T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
RAW = '/home/claude/raw/'; UP = '/mnt/user-data/uploads/new cults/All Mar All the time/'
KITS = {'VS': (RAW, 'VeteranSquad/VeteranSquad/Body/'), 'VBS': (UP, 'VeteranBladeSquad/VeteranBladeSquad/Body/')}
WAIST_Z = 29.307
def inside(tree, p):
    n, o, d = 0, Vector(p), Vector((0.0, 0.0, 1.0))
    for _ in range(40):
        hit = tree.ray_cast(o, d)
        if hit[0] is None: break
        n += 1; o = hit[0] + d * 1e-4
    return n % 2 == 1
out = {}
for kit, (base, sub) in KITS.items():
    files = sorted(glob.glob(base + sub + '*/*.stl'))
    chests = [f for f in files if 'Chest' in os.path.basename(f)]
    legs = [f for f in files if f not in chests]
    csamp = {}
    for c in chests:
        V, Tr = T.read_stl_np(c); S = T._surface_sample(V, Tr, 60000)
        csamp[c] = S[S[:, 2] < WAIST_Z + 1.5]
    for l in legs:
        V, Tr = T.read_stl_np(l); tree = BVHTree.FromPolygons(V.tolist(), Tr.tolist())
        best = None; per = {}
        for c, S in csamp.items():
            ds = []; pen = 0
            for p in S[::3]:
                if inside(tree, p): pen += 1; continue
                hit = tree.ray_cast(Vector(p), Vector((0.0, 0.0, -1.0)), 6.0)
                if hit[0] is not None: ds.append(hit[3])
            dz = float(min(ds)) if ds else None
            per[os.path.basename(c)] = (dz, pen)
            if dz is not None and (best is None or dz < best): best = dz
        rel = l[len(base):]
        out[rel] = {'drop': best, 'per_chest': per}
        print('%-4s %-30s drop %.2f mm   per chest: %s' % (kit, os.path.basename(l), best, {k[:-4]: (round(v[0], 2) if v[0] is not None else None, v[1]) for k, v in per.items()}), flush=True)
json.dump(out, open('/home/claude/kits/vet/drop.json', 'w'), indent=1)

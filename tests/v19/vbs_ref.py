"""A second built-in pauldron reference: Bladeguard arm 48-Arm-7-A (its three points copied from 76 by the swing match,
0.139), then matched onto every Bladeguard arm."""
import bpy, sys, json, time, os, glob
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import importlib.util
spec = importlib.util.spec_from_file_location('ti', '/home/claude/tiow_blender/tiow_inbox.py'); T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
U = '/mnt/user-data/uploads/new cults/All Mar All the time/'
REL = 'VeteranBladeSquad/VeteranBladeSquad/Arms/Arms-RawSTL/48-Arm-7-A.stl'
pm = json.load(open('/home/claude/test/v19/padmatch2.json'))[REL]
ref76 = T.builtin_refs('Pad')[0]; P76 = np.array(ref76['points'], float).reshape(3, 3)
R, t = np.array(pm['R']), np.array(pm['t'])
V, Tr = T.read_stl_np(U + REL); tree = BVHTree.FromPolygons(V.tolist(), Tr.tolist())
P = np.array([tree.find_nearest(Vector(p))[0] for p in P76 @ R.T + t])
region = T._region_around(V, Tr, P)
piv = T._shoulder_pivots(V, Tr, 1)[0]
J = np.array([5.568, 0.202, 31.949])
REF = {'name': '48-Arm-7-A', 'side': 'R', 'points': P.round(4).ravel().tolist(), 'region': region.round(4).ravel().tolist(), 'pivot': np.round(piv, 4).tolist(), 'joint': J.tolist()}
json.dump(REF, open('/home/claude/test/v19/ref48.json', 'w'))
print('ref 48: %d region points' % len(region))
MXv = np.array([-1.0, 1, 1]); res = {}
files = sorted(glob.glob(U + 'VeteranBladeSquad/VeteranBladeSquad/Arms/*/*.stl')) + sorted(glob.glob(U + 'VeteranBladeSquad/VeteranBladeSquad/Additional/*.stl'))
for f in files:
    rel = f[len(U):]; sd = 'L' if ('Mirrored' in rel or 'Additional' in rel) else 'R'
    W, Tw = T.read_stl_np(f); tw = BVHTree.FromPolygons(W.tolist(), Tw.tolist())
    reg, rj, PP = (region * MXv, J * MXv, P * MXv) if sd == 'L' else (region, J, P)
    joint = J * (MXv if sd == 'L' else 1)
    m, Rm, tm = T.match_shoulder(reg, piv * (MXv if sd == 'L' else 1), W, Tw, tw, [(joint, rj)])
    res[rel] = dict(full=m, R=Rm.tolist(), t=tm.tolist(), side=sd)
    print('%-30s %s  48-ref %.3f   (76-ref %.3f)' % (os.path.basename(rel), sd, m, json.load(open('/home/claude/test/v19/padmatch2.json')).get(rel, {}).get('full', -1)), flush=True)
json.dump(res, open('/home/claude/test/v19/padmatch48.json', 'w'))

"""Check sheet: every insert placed on the insert torso by socket @ fit (no TIOW), with the
closest approach / deepest cut into the torso (inside = three rays agree), rendered from the
front and 30 deg to the side. python sheet.py -- <stage lib> <out dir>"""
import json, os, sys, glob, numpy as np, bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; LIB, OUTD = a[0], a[1]; os.makedirs(OUTD, exist_ok=True)
TORSO = "Mar Fil - Tacticus/AssaultMarines-V2/Chests/MarFil Assault - Torso 2 Insert"


def stl(p):
    d = np.fromfile(p, dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]), offset=84)
    return d['v'].reshape(-1, 3).astype(float)


def mesh(name, V, W, col):
    W = np.asarray(W); V = (np.c_[V, np.ones(len(V))] @ W.T)[:, :3]
    me = bpy.data.meshes.new(name); n = len(V) // 3
    me.from_pydata(V.tolist(), [], [(3 * i, 3 * i + 1, 3 * i + 2) for i in range(n)]); me.validate()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    m = bpy.data.materials.new(name); m.diffuse_color = col; me.materials.append(m)
    return o, V


D = [Vector(d).normalized() for d in ((0.0123, 0.0177, 1), (1, 0.031, -0.017), (-0.023, -1, 0.041))]
def odd(t, v, d):
    k = 0; p = v.copy()
    for _ in range(12):
        h = t.ray_cast(p, d, 500)
        if h[0] is None: break
        k += 1; p = h[0] + d * 1e-4
    return k % 2


bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sd = json.load(open(os.path.join(LIB, TORSO + ".sockets.json")))
S = np.array(next(s for s in sd["sockets"] if s["type"] == "Chest Insert")["matrix"]).reshape(4, 4)
tor, VT = mesh("torso", stl(os.path.join(LIB, TORSO + ".stl")), np.eye(4), (0.55, 0.6, 0.7, 1))
tree = BVHTree.FromPolygons([Vector(v) for v in VT], [(3 * i, 3 * i + 1, 3 * i + 2) for i in range(len(VT) // 3)])
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
sc.render.resolution_x = sc.render.resolution_y = 260; sc.render.film_transparent = False
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 15
res = {}
for p in sorted(glob.glob(os.path.join(LIB, "Bits/Torso Inserts/Chest Inserts/*.stl"))):
    n = os.path.basename(p)[:-4]; F = np.array(json.load(open(p[:-4] + ".sockets.json"))["fits"]["Chest Insert"]).reshape(4, 4)
    o, V = mesh(n, stl(p), S @ F, (0.85, 0.55, 0.3, 1))
    P = V[::max(1, len(V) // 3000)]; close = 9e9; deep = 0.0
    for v in P:
        v = Vector(v); d = tree.find_nearest(v)[3]; close = min(close, d)
        if d > deep and d < 3 and all(odd(tree, v, dd) for dd in D): deep = d
    res[n] = (round(close, 3), round(deep, 3)); print("%-40s closest %.3f cut %.3f" % (n, close, deep), flush=True)
    for view, ang in (("front", 0), ("side", 35)):
        r = np.radians(ang); c = Vector((0, 0.9, 31.3)); dirv = Vector((np.sin(r), np.cos(r), 0.15)).normalized()
        cam.location = c + dirv * 60; cam.rotation_euler = (-dirv).to_track_quat('-Z', 'Z').to_euler()
        sc.render.filepath = os.path.join(OUTD, "%s_%s.png" % (n, view)); bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(o)
json.dump(res, open(os.path.join(OUTD, "cuts.json"), "w"), indent=1)

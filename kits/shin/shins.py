"""Lower legs of every Marta legs, front-right view, for spotting bare shins. python shins.py -- KEYS_JSON START END OUT_PREFIX"""
import bpy, sys, json, numpy as np
from mathutils import Matrix, Vector
sys.path.insert(0, "/home/claude/kitbash/kits/plates"); sys.path.insert(0, "/home/claude/test")
from hol_common import tf; import rend
from legs_frame import legs as legs_geo
a = sys.argv[sys.argv.index("--") + 1:]; K = json.load(open(a[0]))[int(a[1]):int(a[2])]; PRE = a[3]
ROOT = "/mnt/user-data/uploads/d/Kitbash Library/"
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; cam = rend.setup(sc, 220)
for i, k in enumerate(K):
    _, V, T, M = legs_geo(k, ROOT); P = tf(M, V)
    me = bpy.data.meshes.new("m"); me.from_pydata(P.tolist(), [], T.tolist()); me.update()
    o = bpy.data.objects.new("m", me); sc.collection.objects.link(o); o.color = rend.GREY
    z0, z1 = P[:, 2].min(), P[:, 2].max(); low = P[P[:, 2] < z0 + 0.62 * (z1 - z0)]
    c = (low.min(0) + low.max(0)) / 2; size = np.ptp(low, 0).max()
    dv = Vector((0.45, 1, 0.12)).normalized(); u = Vector((0, 0, 1)); yv = (u - dv * u.dot(dv)).normalized(); xv = yv.cross(dv)
    cam.matrix_world = Matrix.LocRotScale(Vector(c) + dv * 300, Matrix((xv, yv, dv)).transposed().to_quaternion(), None); cam.data.ortho_scale = size * 1.08
    sc.render.filepath = "%s_%03d.png" % (PRE, int(a[1]) + i); bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(o); bpy.data.meshes.remove(me)
print("done", len(K))

import bpy, sys, json, numpy as np
from mathutils import Matrix, Vector
sys.path.insert(0, "/home/claude/kitbash/kits/plates"); sys.path.insert(0, "/home/claude/test")
from hol_common import stl, tf, M16; import rend
from legs_frame import legs as legs_geo
U = "/mnt/user-data/uploads/d/Kitbash Library/"; L = "/home/claude/kitbash/library/"
C = json.load(open("/home/claude/work/shin/carried.json")); props = json.load(open("/home/claude/work/shin/proposed.json"))
a = sys.argv[sys.argv.index("--") + 1:]; i0, i1 = int(a[0]), int(a[1])
P = json.load(open("/home/claude/work/shin/pads.json")); pads = {}
for s in "RL":
    k = P["Marta May 2026 - Shin Pad 1 " + s]; V, T = stl(U + k + ".stl"); pads[s] = (V, T, M16(json.load(open(L + k + ".sockets.json", encoding="utf-8-sig"))["fits"]["Shin " + s]))
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; cam = rend.setup(sc, 260)
def ob(V, T, col):
    me = bpy.data.meshes.new("m"); me.from_pydata(V.tolist(), [], T.tolist()); me.update(); o = bpy.data.objects.new("m", me); sc.collection.objects.link(o); o.color = col; return o
for i in range(i0, i1):
    k = props[i]; _, V, T, M = legs_geo(k, U); Vt = tf(M, V); obs = [ob(Vt, T, rend.GREY)]
    for s in "RL":
        PV, PT, fit = pads[s]; obs.append(ob(tf(np.array(C[k][s]["socket_torso"]) @ fit, PV), PT, rend.BLUE if C[k][s]["ref"].startswith("Josh") else rend.ORANGE))
    z0, z1 = Vt[:, 2].min(), Vt[:, 2].max(); low = Vt[Vt[:, 2] < z0 + 0.62 * (z1 - z0)]; c = (low.min(0) + low.max(0)) / 2; size = np.ptp(low, 0).max()
    for vn, dv in (("r", (0.7, 1, 0.12)), ("l", (-0.7, 1, 0.12))):
        dv = Vector(dv).normalized(); u = Vector((0, 0, 1)); yv = (u - dv * u.dot(dv)).normalized(); xv = yv.cross(dv)
        cam.matrix_world = Matrix.LocRotScale(Vector(c) + dv * 300, Matrix((xv, yv, dv)).transposed().to_quaternion(), None); cam.data.ortho_scale = size * 1.1
        sc.render.filepath = "/home/claude/work/shin/r/c_%03d_%s.png" % (i, vn); bpy.ops.render.render(write_still=True)
    for o in obs: me = o.data; bpy.data.objects.remove(o); bpy.data.meshes.remove(me)
print("done")

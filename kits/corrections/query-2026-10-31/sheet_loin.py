"""Every loincloth as it hangs on the belt anchor (fit applied: Y up, Z out = facing the camera), from the page previews."""
import bpy, sys, json, struct
import numpy as np
from mathutils import Matrix
sys.path.insert(0, "/home/claude/test"); import rend
idx = json.load(open("/mnt/user-data/outputs/loincloths-2026-10-30/index.json"))
P = "/mnt/user-data/uploads/d/Kitbash Library/_builder/previews/"
parts = [p for p in idx["parts"] if p["type"] == "Loincloths"]
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene; rend.setup(scene, 260)
for i, p in enumerate(parts):
    b = open(P + p["id"] + ".bin", "rb").read(); nv, nt = struct.unpack_from("<II", b, 4)
    V = np.frombuffer(b, "<f4", nv * 3, 12).reshape(-1, 3); T = np.frombuffer(b, "<u4", nt * 3, 12 + nv * 12).reshape(-1, 3)
    me = bpy.data.meshes.new(p["id"]); me.from_pydata(V.tolist(), [], T.tolist()); me.update()
    o = bpy.data.objects.new(p["id"], me); scene.collection.objects.link(o)
    o.matrix_world = Matrix(np.array(p["fits"]["Belt Front"]).reshape(4, 4).tolist())   # anchor frame: Y up, Z out
    rend.render(scene, "/home/claude/twoarm/query2/sheet", "%02d" % i, [o], {"front": (0, -0.15, 1)}, [rend.ORANGE], pad=1.15, up=(0, 1, 0))
    o.hide_render = True
json.dump([p["name"] for p in parts], open("/home/claude/twoarm/query2/sheet/names.json", "w"))

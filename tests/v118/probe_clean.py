import bpy, sys, numpy as np
sys.path.insert(0, "/root/.config/blender/5.1/scripts/addons")
bpy.ops.wm.read_factory_settings(use_empty=True)
import tiow_inbox as T
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import bmesh
def inside(tree, p, d=Vector((0.123, 0.311, 0.942)).normalized()):
    n, pos = 0, Vector(p)
    for _ in range(50):
        loc, nr, i, dd = tree.ray_cast(pos, d, 100)
        if loc is None: break
        n += 1; pos = loc + d * 1e-5
    return n % 2 == 1
for f, c, r in (("LEG_HIGH", (-0.38, -0.146, 8.831), 2.889), ("FOOT_3", (0.042, 1.291, 3.222), 1.407), ("LEG_LOW", (0.026, -0.373, 1.345), 1.343)):
    bpy.ops.wm.stl_import(filepath=f"/home/claude/bionic/kit/{f}.stl"); ob = bpy.context.selected_objects[0]
    def stats(ob):
        b = bmesh.new(); b.from_mesh(ob.data); t = BVHTree.FromBMesh(b)
        V = np.array([v.co[:] for v in b.verts]); b.free()
        on = (np.abs(np.linalg.norm(V - np.array(c), axis=1) - r) < 0.03).sum()
        return inside(t, c), on
    print(f, "raw: centre inside", *stats(ob))
    T.bio_clean(ob)
    print(f, "cleaned: centre inside", *stats(ob))
    bpy.data.objects.remove(ob)

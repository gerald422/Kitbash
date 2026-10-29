"""Render several models (each a list of [npz, 16 floats, rgba]) with the same views, one blender session.
job: {out, res, views:{n:[x,y,z]}, models:[{name, items}], pad}"""
import bpy, json, sys, numpy as np, os
from mathutils import Matrix
sys.path.insert(0, "/home/claude/test")
import rend
job = json.load(open(sys.argv[-1]))
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene; rend.setup(scene, job.get("res", 600))
meshes = {}
def mesh(p):
    if p in meshes: return meshes[p]
    z = np.load(p); V, T = z["V"].astype(float), z["T"]
    me = bpy.data.meshes.new(os.path.basename(p))
    me.vertices.add(len(V)); me.vertices.foreach_set("co", V.ravel())
    me.loops.add(T.size); me.loops.foreach_set("vertex_index", T.ravel())
    me.polygons.add(len(T)); me.polygons.foreach_set("loop_start", np.arange(0, T.size, 3)); me.polygons.foreach_set("loop_total", np.full(len(T), 3))
    me.update(); me.validate(); meshes[p] = me; return me
os.makedirs(job["out"], exist_ok=True)
groups = []
for m in job["models"]:
    obs, cols = [], []
    for i, (p, M, col) in enumerate(m["items"]):
        ob = bpy.data.objects.new(f'{m["name"]}_{i}', mesh(p)); scene.collection.objects.link(ob)
        ob.matrix_world = Matrix(np.array(M, float).reshape(4, 4).tolist()); obs.append(ob); cols.append(tuple(col))
    groups.append((m["name"], obs, cols))
for name, obs, cols in groups:
    for _, o2, _ in groups:
        for o in o2: o.hide_render = o2 is not obs
    rend.render(scene, job["out"], name, obs, job.get("views", {"front": (0, 1, 0)}), cols, pad=job.get("pad", 1.08))

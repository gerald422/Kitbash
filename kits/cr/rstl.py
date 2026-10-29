"""Render STL files: python rstl.py job.json; job: {out,name,items:[[path, 16 floats, rgba]], views:{n:[x,y,z]}, res}"""
import bpy, json, sys, numpy as np, os
from mathutils import Matrix
sys.path.insert(0, "/home/claude/test"); sys.path.insert(0, "/home/claude/real")
import rend
job = json.load(open(sys.argv[-1]))
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene; rend.setup(scene, job.get("res", 600))
obs, cols = [], []
for i, (p, m, col) in enumerate(job["items"]):
    if p.endswith(".npz"):
        z = np.load(p); V, T = z["V"].astype(float), z["T"]
    else:
        raise SystemExit("npz only")
    me = bpy.data.meshes.new(f"m{i}")
    me.vertices.add(len(V)); me.vertices.foreach_set("co", np.asarray(V, float).ravel())
    me.loops.add(T.size); me.loops.foreach_set("vertex_index", np.asarray(T).ravel())
    me.polygons.add(len(T)); me.polygons.foreach_set("loop_start", np.arange(0, T.size, 3)); me.polygons.foreach_set("loop_total", np.full(len(T), 3))
    me.update(); me.validate()
    ob = bpy.data.objects.new(f"o{i}", me); scene.collection.objects.link(ob)
    ob.matrix_world = Matrix(np.array(m, float).reshape(4, 4).tolist())
    obs.append(ob); cols.append(tuple(col))
os.makedirs(job["out"], exist_ok=True)
rend.render(scene, job["out"], job["name"], obs, job.get("views", {"front": (0, 1, 0)}), cols, pad=job.get("pad", 1.05))

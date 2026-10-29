"""Quick look: python qrender.py job.json  (job: {"out": dir, "name": n, "items": [[rel, 16 floats, [r,g,b,a]], ...],
"views": {"front": [0,1,0], ...}, "res": 600, "tiles": optional})"""
import bpy, json, sys, numpy as np, os, hashlib
from mathutils import Matrix, Vector
sys.path.insert(0, "/home/claude/test"); import rend
job = json.load(open(sys.argv[-1]))
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene; rend.setup(scene, job.get("res", 600))
CACHE = "/home/claude/kits/cache/"
obs, cols = [], []
for i, (rel, m, col) in enumerate(job["items"]):
    z = np.load(CACHE + hashlib.md5(rel.encode()).hexdigest() + ".npz")
    V, T = z["V"].astype(float), z["T"]
    me = bpy.data.meshes.new(f"m{i}")
    me.vertices.add(len(V)); me.vertices.foreach_set("co", V.ravel())
    me.loops.add(T.size); me.loops.foreach_set("vertex_index", T.ravel())
    me.polygons.add(len(T)); me.polygons.foreach_set("loop_start", np.arange(0, T.size, 3)); me.polygons.foreach_set("loop_total", np.full(len(T), 3))
    me.update(); me.validate()
    ob = bpy.data.objects.new(os.path.basename(rel), me); scene.collection.objects.link(ob)
    ob.matrix_world = Matrix(np.array(m).reshape(4, 4).tolist())
    obs.append(ob); cols.append(tuple(col))
os.makedirs(job["out"], exist_ok=True)
if job.get("centre") is None:
    rend.render(scene, job["out"], job["name"], obs, job.get("views", {"front": (0, 1, 0)}), cols, pad=job.get("pad", 1.05))
else:
    cam = scene.camera
    for o in scene.objects:
        if o.type == 'MESH': o.hide_render = o not in obs
    for o, c in zip(obs, cols): o.color = c
    c = Vector(job["centre"]); size = float(job["size"])
    for vname, d in job["views"].items():
        d = Vector(d).normalized(); u = Vector((0, 0, 1))
        if abs(u.dot(d)) > 0.99: u = Vector((0, 1, 0))
        y = (u - d * u.dot(d)).normalized(); x = y.cross(d)
        cam.matrix_world = Matrix.LocRotScale(c + d * (size * 3 + 80), Matrix((x, y, d)).transposed().to_quaternion(), None)
        cam.data.ortho_scale = size
        scene.render.filepath = f"{job['out']}/{job['name']}_{vname}.png"; bpy.ops.render.render(write_still=True)

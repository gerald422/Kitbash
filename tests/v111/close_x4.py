import bpy, sys, os, json
from mathutils import Matrix, Vector
sys.path.insert(0, "/home/claude/test"); import rend
bpy.ops.wm.open_mainfile(filepath="/home/claude/test/v111/out/cross_test.blend")
scene = bpy.context.scene; rend.setup(scene, 520)
lg = next(o for o in bpy.data.objects if o.name.startswith("17-Body-A") and o.type == 'MESH' and any(c.get("ws_type") == "Hip R" and any(g.name.startswith("23-Book") for g in c.children) for c in o.children))
items = [g for c in lg.children for g in c.children if g.type == 'MESH' and (g.name.startswith("23-Book") or g.name.startswith("25-Holster"))]
for c in lg.children:
    if c.get("ws_type") in ("Hip R", "Hip L"):
        print(c["ws_type"], "at", [round(x, 2) for x in c.matrix_world.translation], "Z", [round(x, 2) for x in c.matrix_world.to_3x3().col[2]])
for g in items:
    print(g.name, "centre", [round(x, 2) for x in (g.matrix_world @ (Vector(g.bound_box[0]) + Vector(g.bound_box[6])) / 2)], "parent socket", g.parent.get("ws_type"))
obs = [lg] + items
for o in scene.objects:
    if o.type == 'MESH': o.hide_render = o not in obs
    if o.type == 'EMPTY': o.hide_render = True
for o in obs: o.color = rend.ORANGE if o in items else rend.GREY
pts = [lg.matrix_world @ Vector(c) for c in lg.bound_box]
lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
c = (lo + hi) / 2; c.z = hi.z - 8; size = 26
cam = scene.camera
for vn, d in {"front": (0, 1, 0.1), "right": (1, 0, 0.1), "back": (0, -1, 0.1), "left": (-1, 0, 0.1)}.items():
    d = Vector(d).normalized(); u = Vector((0, 0, 1)); y = (u - d * u.dot(d)).normalized(); x = y.cross(d)
    cam.matrix_world = Matrix.LocRotScale(c + d * 100, Matrix((x, y, d)).transposed().to_quaternion(), None); cam.data.ortho_scale = size
    scene.render.filepath = f"/home/claude/test/v111/out/close/x4belt_{vn}.png"; bpy.ops.render.render(write_still=True)

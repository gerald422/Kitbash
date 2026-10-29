import bpy, sys, json
from mathutils import Matrix, Vector
sys.path.insert(0, "/home/claude/test"); import rend
bpy.ops.wm.open_mainfile(filepath="/home/claude/test/v111/out/cross_test.blend")
scene = bpy.context.scene; rend.setup(scene, 460)
rows = []
legs = [o for o in bpy.data.objects if o.type == 'MESH' and any(g.type == 'MESH' and str(g.get("tiow_category", "")) in ("Accessories", "Grenades") for c in o.children for g in c.children)]
for lg in legs:
    items = [g for c in lg.children for g in c.children if g.type == 'MESH' and str(g.get("tiow_category", "")) in ("Accessories", "Grenades")]
    obs = [lg] + items
    for o in scene.objects:
        if o.type == 'MESH': o.hide_render = o not in obs
        if o.type == 'EMPTY': o.hide_render = True
    for o in obs: o.color = rend.ORANGE if o in items else rend.GREY
    W = Matrix([lg.parent.parent.matrix_world.col[i] for i in range(4)]).transposed() if lg.parent and lg.parent.parent else lg.matrix_world
    torso = lg.parent.parent
    R = torso.matrix_world.to_3x3().normalized()
    c = torso.matrix_world @ Vector((0, 0.5, 22.0)); files = []
    for vn, d in {"front": (0, 1, 0.15), "right": (1, 0, 0.15), "back": (0, -1, 0.15), "left": (-1, 0, 0.15)}.items():
        d = (R @ Vector(d)).normalized(); u = R @ Vector((0, 0, 1)); y = (u - d * u.dot(d)).normalized(); x = y.cross(d)
        cam = scene.camera; cam.matrix_world = Matrix.LocRotScale(c + d * 100, Matrix((x, y, d)).transposed().to_quaternion(), None); cam.data.ortho_scale = 24
        f = f"/home/claude/test/v111/out/close/belt2_{lg.name}_{vn}.png"; scene.render.filepath = f; bpy.ops.render.render(write_still=True); files.append((f, f"{lg.name[:14]} {vn}"))
    rows.append(files)
json.dump(rows, open("/home/claude/test/v111/out/close/belt2_rows.json", "w"))

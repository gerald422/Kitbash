exec(open("/home/claude/test/v17/common17.py").read())
prefs.bionic_dir = "/home/claude/test/v118/kit"
OUT = "/home/claude/test/v118/out7"
LEGS = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "29-Legs-2"
rend.setup(scene, 640)
select(None); torso = send(f"{AM}/Chest/24-Torso-3.stl", "Chests", (0, 0, 0))
select(torso); legs = send(f"{AM}/Legs/{LEGS}.stl", "Legs")
torso.hide_set(True)
for c in T._descendants(torso):
    if c is not legs and c.type == 'MESH' and legs not in list(T._ancestors(c)): c.hide_set(True)
vl.update()
cam = scene.camera
u = Vector((0, 0, 1))
fw = (legs.matrix_world.to_3x3() @ Vector((0, 1, 0))).normalized(); rt = (legs.matrix_world.to_3x3() @ Vector((1, 0, 0))).normalized()
c0 = legs.matrix_world @ Vector((0, 0.5, 15.5))
for o in scene.objects:
    if o.type == 'MESH': o.hide_render = o is not legs
    if o.type == 'EMPTY': o.hide_render = True
legs.color = rend.GREY
for vname, d in (("front", fw), ("R_out", rt), ("R_front_out", (fw + rt).normalized()), ("L_front_out", (fw - rt).normalized()), ("below_front", (fw * 0.6 - u).normalized()), ("back", -fw)):
    y = (u - d * u.dot(d)).normalized() if abs(d.dot(u)) < 0.95 else fw; x = y.cross(d)
    cam.matrix_world = Matrix.LocRotScale(c0 + d * 200, Matrix((x, y, d)).transposed().to_quaternion(), None)
    cam.data.ortho_scale = 16
    scene.render.filepath = f"{OUT}/{LEGS}_{vname}.png"; bpy.ops.render.render(write_still=True)

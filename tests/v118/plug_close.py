exec(open("/home/claude/test/v17/common17.py").read())
prefs.bionic_dir = "/home/claude/test/v118/kit"
OUT = "/home/claude/test/v118/out8"
LEGS = sys.argv[sys.argv.index("--") + 1]
TAG = sys.argv[sys.argv.index("--") + 2]
rend.setup(scene, 900)
select(None); torso = send(f"{AM}/Chest/24-Torso-3.stl", "Chests", (0, 0, 0))
select(torso); legs = send(f"{AM}/Legs/{LEGS}.stl", "Legs")
for side in ("R", "L"):
    T.bionic_build(legs, side, prefs, cut="belt")
vl.update()
cam = scene.camera
u = Vector((0, 0, 1)); fw = (legs.matrix_world.to_3x3() @ Vector((0, 1, 0))).normalized(); rt = (legs.matrix_world.to_3x3() @ Vector((1, 0, 0))).normalized()
obs = [legs] + [o for side in ("R", "L") for r, o in T.bio_parts(legs, side).items() if o.type == 'MESH' and not r.startswith('cut')]
cols = [rend.GREY] + [rend.ORANGE if o.get("tiow_bionic_role") == "plug" else rend.BLUE for o in obs[1:]]
for o in scene.objects:
    if o.type == 'MESH': o.hide_render = o not in obs
    if o.type == 'EMPTY': o.hide_render = True
for o, c in zip(obs, cols): o.color = c
for side, vname, d in (("L", "front", fw), ("R", "back", -fw), ("L", "front_low", (fw - 0.5 * u).normalized()), ("R", "back_low", (-fw - 0.5 * u).normalized())):
    c0 = T.bio_parts(legs, side)["hip"].matrix_world.translation
    y = (u - d * u.dot(d)).normalized(); x = y.cross(d)
    cam.matrix_world = Matrix.LocRotScale(c0 + d * 200, Matrix((x, y, d)).transposed().to_quaternion(), None)
    cam.data.ortho_scale = 10
    scene.render.filepath = f"{OUT}/{LEGS}_{TAG}_close_{side}_{vname}.png"; bpy.ops.render.render(write_still=True)

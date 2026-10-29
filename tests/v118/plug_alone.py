exec(open("/home/claude/test/v17/common17.py").read())
import bmesh
prefs.bionic_dir = "/home/claude/test/v118/kit"
OUT = "/home/claude/test/v118/out8"
LEGS = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "29-Legs-2"
rend.setup(scene, 900)
select(None); torso = send(f"{AM}/Chest/24-Torso-3.stl", "Chests", (0, 0, 0))
select(torso); legs = send(f"{AM}/Legs/{LEGS}.stl", "Legs")
for side in ("R", "L"):
    T.bionic_build(legs, side, prefs, cut="belt")
vl.update()
st = json.loads(legs["tiow_bionic_state"])
print("collar points L", len(st["L"].get("collar") or []), "R", len(st["R"].get("collar") or []))
pl = T.bio_parts(legs, "L")["plug"]
bm = bmesh.new(); bm.from_mesh(pl.data); print("plug L faces", len(bm.faces), "open edges", sum(1 for e in bm.edges if len(e.link_faces) != 2)); bm.free()
cam = scene.camera
u = Vector((0, 0, 1)); fw = (legs.matrix_world.to_3x3() @ Vector((0, 1, 0))).normalized()
c0 = T.bio_parts(legs, "L")["hip"].matrix_world.translation
for o in scene.objects:
    if o.type == 'MESH': o.hide_render = o is not pl
    if o.type == 'EMPTY': o.hide_render = True
pl.color = rend.ORANGE
for vname, d in (("front", fw), ("up", (fw + 1.5 * u).normalized()), ("side", (legs.matrix_world.to_3x3() @ Vector((-1, 0, 0.2))).normalized())):
    y = (u - d * u.dot(d)).normalized() if abs(d.dot(u)) < 0.95 else fw; x = y.cross(d)
    cam.matrix_world = Matrix.LocRotScale(c0 + d * 200, Matrix((x, y, d)).transposed().to_quaternion(), None)
    cam.data.ortho_scale = 10
    scene.render.filepath = f"{OUT}/plugL_alone_{vname}.png"; bpy.ops.render.render(write_still=True)

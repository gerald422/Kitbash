"""Close-ups from iv2_test.blend: hands + hand-less weapons, arm pieces at the shoulder, heavy arms with cables."""
import bpy, sys, os, json
from mathutils import Matrix, Vector
sys.path.insert(0, "/home/claude/test"); import rend
bpy.ops.wm.open_mainfile(filepath="/home/claude/test/v110/out/iv2_test.blend")
scene = bpy.context.scene; rend.setup(scene, 520)
OUT = "/home/claude/test/v110/out/close"; os.makedirs(OUT, exist_ok=True)
def desc(o):
    for c in o.children:
        yield c; yield from desc(c)
def root_of(o):
    while o.parent is not None: o = o.parent
    return o
def find(name):
    return [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(name)]
CATCOL = {"Hands": rend.ORANGE, "Hand-less Weapons": rend.BLUE, "Melee": rend.BLUE, "Pistols": rend.BLUE, "Shields": rend.BLUE,
          "Heavy Weapon Cables": rend.GREEN, "Arms": rend.GREY}
def shot(tag, focus, views, pad=1.4):
    root = root_of(focus[0]); obs = [o for o in [root] + list(desc(root)) if o.type == 'MESH' and not o.hide_get()]
    for o in scene.objects:
        if o.type == 'MESH': o.hide_render = o not in obs
        if o.type == 'EMPTY': o.hide_render = True
    for o in obs: o.color = CATCOL.get(str(o.get("tiow_category", "")), rend.GREY) if o not in focus else (rend.ORANGE if str(o.get("tiow_category", "")) in ("Hands", "Arms") else rend.BLUE)
    pts = [o.matrix_world @ Vector(c) for o in focus for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    c = (lo + hi) / 2; size = (hi - lo).length
    cam = scene.camera; files = []
    for vn, d in views.items():
        d = Vector(d).normalized(); u = Vector((0, 0, 1))
        if abs(u.dot(d)) > 0.99: u = Vector((0, 1, 0))
        y = (u - d * u.dot(d)).normalized(); x = y.cross(d)
        cam.matrix_world = Matrix.LocRotScale(c + d * (size * 3 + 60), Matrix((x, y, d)).transposed().to_quaternion(), None)
        cam.data.ortho_scale = size * pad
        f = f"{OUT}/{tag}_{vn}.png"; scene.render.filepath = f; bpy.ops.render.render(write_still=True); files.append((f, f"{tag} {vn}"))
    return files
V = {"front": (0, 1, 0.15), "out": (1, 0.3, 0.2), "back": (0, -1, 0.3), "in": (-1, 0.3, 0.2)}
rows = []
plan = json.load(open(sys.argv[-1]))
for tag, names, views in plan:
    focus = [o for n in names for o in find(n)[:1]]
    if not focus: print("missing", names); continue
    rows.append(shot(tag, focus, {k: V[k] for k in views}))
json.dump(rows, open(OUT + "/rows.json", "w"))

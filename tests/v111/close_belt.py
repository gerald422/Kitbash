"""Belt bits on the Chaplain legs: as the inbox settled them (orange) vs Mar Fil's spot (blue)."""
import bpy, sys, os, json
import numpy as np
from mathutils import Matrix, Vector
sys.path.insert(0, "/home/claude/test"); import rend
import json as _j
bpy.ops.wm.open_mainfile(filepath="/home/claude/test/v111/out/cj_test.blend")
scene = bpy.context.scene; rend.setup(scene, 520)
OUT = "/home/claude/test/v111/out/close"
PO = json.load(open("/home/claude/kits/cj/pose.json"))
def desc(o):
    for c in o.children:
        yield c; yield from desc(c)
legs_of = {}
for o in bpy.data.objects:
    if o.type == 'MESH' and 'Legs-' in o.name and 'Chaplain' in o.name: legs_of[o.name.split('-')[2]] = o
rows = []
for X in "ABCD":
    lg = legs_of[X]
    acc = [c for c in desc(lg) if c.type == 'MESH' and str(c.get("tiow_category", "")) in ("Accessories", "Grenades")]
    ghosts = []
    Pm = Matrix(np.array(PO[X]["P"]).tolist())
    l, r, _ = lg.matrix_world.decompose(); Lw = Matrix.LocRotScale(l, r, Vector((1, 1, 1)))
    for a in acc:
        g = a.copy(); g.data = a.data; g.parent = None; scene.collection.objects.link(g); g.matrix_world = Lw @ Pm; ghosts.append(g)
    obs = [lg] + acc + ghosts
    for o in scene.objects:
        if o.type == 'MESH': o.hide_render = o not in obs
        if o.type == 'EMPTY': o.hide_render = True
    for o in obs: o.color = rend.GREY
    for a in acc: a.color = rend.ORANGE
    for g in ghosts: g.color = (0.45, 0.65, 0.88, 0.5)
    pts = [o.matrix_world @ Vector(c) for o in acc for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    c = (lo + hi) / 2; size = (hi - lo).length
    files = []
    for vn, d in {"front": (0, 1, 0.15), "left": (-1, 0, 0.15), "back": (0, -1, 0.15), "top": (0, 0.01, 1)}.items():
        d = Lw.to_3x3() @ Pm.to_3x3() @ Vector(d); d.normalize(); u = Vector((0, 0, 1))
        if abs(u.dot(d)) > 0.99: u = Vector((0, 1, 0))
        y = (u - d * u.dot(d)).normalized(); x = y.cross(d)
        cam = scene.camera; cam.matrix_world = Matrix.LocRotScale(c + d * (size * 3 + 60), Matrix((x, y, d)).transposed().to_quaternion(), None)
        cam.data.ortho_scale = size * 1.2
        f = f"{OUT}/belt{X}_{vn}.png"; scene.render.filepath = f; bpy.ops.render.render(write_still=True); files.append((f, f"{X} {vn}"))
    for g in ghosts: bpy.data.objects.remove(g)
    rows.append(files)
_j.dump(rows, open(OUT + "/belt_rows.json", "w"))

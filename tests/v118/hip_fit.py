exec(open("/home/claude/test/v17/common17.py").read())
import bmesh
from mathutils.bvhtree import BVHTree
prefs.bionic_dir = "/home/claude/test/v118/kit"
OUT = "/home/claude/test/v118/out6"
LEGS = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "29-Legs-2"
rend.setup(scene, 700)
select(None); torso = send(f"{AM}/Chest/24-Torso-3.stl", "Chests", (0, 0, 0))
select(torso); legs = send(f"{AM}/Legs/{LEGS}.stl", "Legs")
for side in ("R", "L"):
    print(side, T.bionic_build(legs, side, prefs, cut="belt"))
vl.update()
dg = bpy.context.evaluated_depsgraph_get()
tl = BVHTree.FromObject(legs, dg)        # legs space
inv = legs.matrix_world.inverted()
def inside(tree, p, d=Vector((0.123, 0.311, 0.942)).normalized()):
    n, pos = 0, Vector(p)
    for _ in range(60):
        loc, nr, i, dd = tree.ray_cast(pos, d, 1000)
        if loc is None: break
        n += 1; pos = loc + d * 1e-5
    return n % 2 == 1
st = json.loads(legs["tiow_bionic_state"])
Lw = A(legs.matrix_world)
for side in ("R", "L"):
    P = T.bio_parts(legs, side); th = P["thigh"]
    ball = A(P["hip"].matrix_world)[:3, 3]
    up = Lw[:3, :3] @ np.array(st[side]["d"]); up /= np.linalg.norm(up)
    tv = np.array([A(th.matrix_world) @ np.r_[v.co[:], 1] for v in th.data.vertices])[:, :3]
    ins = np.array([v for v in tv[::2] if inside(tl, inv @ Vector(v))])
    print(side, "thigh vertices (1 in 2) inside the legs:", len(ins), "of", len(tv[::2]))
    if len(ins):
        rel = ins - ball
        h = rel @ up
        print("   height along the belt's up from the ball centre: %.2f .. %.2f   (median %.2f)" % (h.min(), h.max(), np.median(h)))
        print("   distance from the ball centre: %.2f .. %.2f" % (np.linalg.norm(rel, axis=1).min(), np.linalg.norm(rel, axis=1).max()))
        lat = Lw[:3, :3] @ np.array([1.0, 0, 0]); lat /= np.linalg.norm(lat); fw = Lw[:3, :3] @ np.array([0, 1.0, 0]); fw /= np.linalg.norm(fw)
        print("   mean offset (x right, y front, up): %.2f %.2f %.2f" % (rel @ lat).mean(), (rel @ fw).mean(), h.mean()) if False else print("   mean offset x %.2f  y %.2f  up %.2f" % ((rel @ lat).mean(), (rel @ fw).mean(), h.mean()))
# section through each ball, square to the model's front
def section_copy(ob, co, no, evaluated=False):
    if evaluated:
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    else:
        me = ob.data.copy()
    bm = bmesh.new(); bm.from_mesh(me); bm.transform(ob.matrix_world)
    r = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=co, plane_no=no, clear_inner=True)
    edges = [e for e in r["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
    try:
        bmesh.ops.holes_fill(bm, edges=edges, sides=0)
    except Exception:
        pass
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(ob.name + " sec", me); scene.collection.objects.link(o); return o
for side in ("R", "L"):
    P = T.bio_parts(legs, side)
    ball = Vector(A(P["hip"].matrix_world)[:3, 3])
    fw = (legs.matrix_world.to_3x3() @ Vector((0, 1, 0))).normalized()
    secs = [section_copy(legs, ball, -fw, True), section_copy(P["plug"], ball, -fw), section_copy(P["thigh"], ball, -fw)]
    cols = [rend.GREY, rend.ORANGE, rend.BLUE]
    # camera: from the front, centred on the ball, 16 mm across
    cam = scene.camera
    for o in scene.objects:
        if o.type == 'MESH': o.hide_render = o not in secs
        if o.type == 'EMPTY': o.hide_render = True
    for o, c in zip(secs, cols): o.color = c
    u = Vector(Lw[:3, :3] @ np.array(st[side]["d"])).normalized() if False else Vector((0, 0, 1))
    for vname, d, scale in (("section", fw, 18 * float(legs.get("tiow_unit") or 1)),):
        y = (u - d * u.dot(d)).normalized(); x = y.cross(d)
        cam.matrix_world = Matrix.LocRotScale(ball + d * 200, Matrix((x, y, d)).transposed().to_quaternion(), None)
        cam.data.ortho_scale = scale
        scene.render.filepath = f"{OUT}/{LEGS}_{side}_{vname}.png"; bpy.ops.render.render(write_still=True)
    for o in secs: bpy.data.objects.remove(o)
    # and the whole hip, unsectioned, front and outside, close
    obs = [legs] + [o for r, o in P.items() if o.type == 'MESH' and not r.startswith('cut')]
    cols = [rend.GREY] + [rend.ORANGE if r == 'plug' else rend.BLUE for r, o in P.items() if o.type == 'MESH' and not r.startswith('cut')]
    for o in scene.objects:
        if o.type == 'MESH': o.hide_render = o not in obs
    for o, c in zip(obs, cols): o.color = c
    out_ = (legs.matrix_world.to_3x3() @ Vector((1 if side == "R" else -1, 0, 0))).normalized()
    for vname, d in (("front", fw), ("outside", out_), ("front_out", (fw + out_ * 0.8).normalized())):
        y = (u - d * u.dot(d)).normalized(); x = y.cross(d)
        cam.matrix_world = Matrix.LocRotScale(ball - u * 5 * float(legs.get("tiow_unit") or 1) + d * 200, Matrix((x, y, d)).transposed().to_quaternion(), None)
        cam.data.ortho_scale = 30 * float(legs.get("tiow_unit") or 1)
        scene.render.filepath = f"{OUT}/{LEGS}_{side}_{vname}.png"; bpy.ops.render.render(write_still=True)
# both legs together, front and 3/4
obs = [legs] + [o for side in ("R", "L") for r, o in T.bio_parts(legs, side).items() if o.type == 'MESH' and not r.startswith('cut')]
cols = [rend.GREY] + [rend.ORANGE if o.get("tiow_bionic_role") == "plug" else rend.BLUE for o in obs[1:]]
for o in scene.objects:
    if o.type == 'MESH': o.hide_render = o not in obs
for o, c in zip(obs, cols): o.color = c
fw = (legs.matrix_world.to_3x3() @ Vector((0, 1, 0))).normalized(); rt = (legs.matrix_world.to_3x3() @ Vector((1, 0, 0))).normalized()
c0 = legs.matrix_world @ Vector((0, 0.5, 14.0))
for vname, d in (("both_front", fw), ("both_q", (fw + 0.8 * rt).normalized()), ("both_below", (fw * 0.5 - Vector((0, 0, 1)) * 0.8 + rt * 0.2).normalized())):
    y = (u - d * u.dot(d)).normalized(); x = y.cross(d)
    cam.matrix_world = Matrix.LocRotScale(c0 + d * 200, Matrix((x, y, d)).transposed().to_quaternion(), None)
    cam.data.ortho_scale = 26 * float(legs.get("tiow_unit") or 1)
    scene.render.filepath = f"{OUT}/{LEGS}_{vname}.png"; bpy.ops.render.render(write_still=True)

exec(open("/home/claude/test/v17/common17.py").read())
import bmesh
prefs.bionic_dir = "/home/claude/test/v118/kit"
OUT = "/home/claude/test/v118/out6"
LEGS = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "30-Legs-3"
rend.setup(scene, 700)
select(None); torso = send(f"{AM}/Chest/24-Torso-3.stl", "Chests", (0, 0, 0))
select(torso); legs = send(f"{AM}/Legs/{LEGS}.stl", "Legs")
print(T.bionic_build(legs, "R", prefs, cut="belt"))
vl.update()
st = json.loads(legs["tiow_bionic_state"])["R"]
print("state out_auto", st.get("out_auto"), "swing", st.get("swing"), "tilt", st.get("tilt"))
P = T.bio_parts(legs, "R")
print("cutters:", [o.name for r, o in P.items() if r.startswith("cut")])
K = T.bio_kit_side(T.bionic_kit(prefs.bionic_dir), "R")
g = P["plug"].matrix_world @ Vector(K["plug"][1]["glue"])
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=0.35, matrix=Matrix.Translation(g)); me = bpy.data.meshes.new("g"); bm.to_mesh(me); bm.free()
mk = bpy.data.objects.new("glue", me); scene.collection.objects.link(mk)
obs = [legs, mk]; cols = [rend.GREY, rend.RED]
cam = scene.camera
for o in scene.objects:
    if o.type == 'MESH': o.hide_render = o not in obs
    if o.type == 'EMPTY': o.hide_render = True
for o, c in zip(obs, cols): o.color = c
u = Vector((0, 0, 1)); fw = (legs.matrix_world.to_3x3() @ Vector((0, 1, 0))).normalized(); rt = (legs.matrix_world.to_3x3() @ Vector((1, 0, 0))).normalized()
n = (legs.matrix_world.to_3x3() @ Vector(st["d"])).normalized()
for vname, d in (("cf_below", -n), ("cf_front", fw), ("cf_out", (rt + fw * 0.3).normalized()), ("cf_below_front", (-n + fw * 0.8).normalized())):
    y = (u - d * u.dot(d)).normalized() if abs(d.dot(u)) < 0.95 else fw; x = y.cross(d)
    cam.matrix_world = Matrix.LocRotScale(g + d * 200, Matrix((x, y, d)).transposed().to_quaternion(), None)
    cam.data.ortho_scale = 16
    scene.render.filepath = f"{OUT}/{LEGS}_{vname}.png"; bpy.ops.render.render(write_still=True)
from mathutils.bvhtree import BVHTree
dg = bpy.context.evaluated_depsgraph_get(); tree = BVHTree.FromObject(legs, dg)
inv = legs.matrix_world.inverted()
gl = inv @ g; nl = Vector(st["d"]).normalized()
for lab, dd in (("up (+n)", nl), ("down (-n)", -nl)):
    hit = tree.ray_cast(gl + dd * 1e-4, dd, 20)
    print(lab, "first hit", None if hit[0] is None else round((hit[0] - gl).length, 3), "normal.n", None if hit[0] is None else round(hit[1].normalized().dot(nl), 3))
loc, nr, i, dist = tree.find_nearest(gl); print("nearest", round(dist, 3), "normal.n", round(nr.normalized().dot(nl), 3), "offset along n", round((loc - gl).dot(nl), 3))
# sample the glue disc: how much of it touches body (a hit within 0.05 above or the point inside)
K2 = K["plug"][1]; import numpy as np
Mp = A(P["plug"].matrix_world)
fn = np.array(K2["flat_n"]); fn /= np.linalg.norm(fn); e1 = np.cross(fn, [0, 1.0, 0]); e1 /= np.linalg.norm(e1); e2 = np.cross(fn, e1)
touch = 0; tot = 0
for rr in (0.6, 1.2, 1.8, 2.3):
    for a in np.linspace(0, 2 * np.pi, 24, endpoint=False):
        q = np.array(K2["glue"]) + rr * (np.cos(a) * e1 + np.sin(a) * e2)
        w = inv @ Vector((Mp @ np.r_[q, 1])[:3]); tot += 1
        hit = tree.ray_cast(w - nl * 0.05, nl, 0.15)
        if hit[0] is not None: touch += 1
print(f"glue disc points with body within 0.1 mm above: {touch}/{tot}")

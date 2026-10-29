exec(open("/home/claude/test/v17/common17.py").read())
import bmesh
from mathutils.bvhtree import BVHTree
prefs.bionic_dir = "/home/claude/test/v118/kit"
select(None); torso = send(f"{AM}/Chest/24-Torso-3.stl", "Chests", (0, 0, 0))
select(torso); legs = send(f"{AM}/Legs/29-Legs-2.stl", "Legs")
for side in ("R", "L"):
    print(side, T.bionic_build(legs, side, prefs, cut="belt"))
vl.update(); dg = bpy.context.evaluated_depsgraph_get()
me = bpy.data.meshes.new_from_object(legs.evaluated_get(dg))
bm = bmesh.new(); bm.from_mesh(me); bm.transform(legs.matrix_world); print("body volume", round(bm.calc_volume(signed=True), 2)); tb = BVHTree.FromBMesh(bm)
def inside(tree, p, d=Vector((0.123, 0.311, 0.942)).normalized()):
    n, pos = 0, Vector(p)
    for _ in range(80):
        loc, nr, i, dd = tree.ray_cast(pos, d, 1000)
        if loc is None: break
        n += 1; pos = loc + d * 1e-5
    return n % 2 == 1
for side in ("R", "L"):
    P = T.bio_parts(legs, side)
    pl = P["plug"]
    b2 = bmesh.new(); b2.from_mesh(pl.data); print(side, "plug volume (own)", round(b2.calc_volume(signed=True), 2), "det", round(pl.matrix_world.to_3x3().determinant(), 3)); b2.free()
    c = P["hip"].matrix_world.translation
    rng = np.random.default_rng(1); k = 0; n = 0
    ins = []
    for _ in range(400):
        q = rng.normal(size=3); q = q / np.linalg.norm(q) * 2.5 * rng.random() ** (1 / 3)
        p = c + Vector(q)
        # inside the plug?
        if not inside(BVHTree.FromObject(pl, dg) if False else None, p) if False else True:
            pass
        k += 1
        if inside(tb, p): n += 1; ins.append(q)
    ins = np.array(ins)
    print(side, f"random points within 2.5 mm of the ball centre inside the body: {n}/{k}", ("mean offset " + str(ins.mean(0).round(2))) if n else "")

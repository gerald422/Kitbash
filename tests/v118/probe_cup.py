exec(open("/home/claude/test/v17/common17.py").read())
prefs.bionic_dir = "/home/claude/test/v118/kit"
OUT = "/home/claude/test/v118/out5"; os.makedirs(OUT, exist_ok=True)
rend.setup(scene, 560)
select(None); torso = send(f"{AM}/Chest/24-Torso-3.stl", "Chests", (0, 0, 0))
select(torso); legs = send(f"{AM}/Legs/29-Legs-2.stl", "Legs")
for side in ("R", "L"):
    msg = T.bionic_build(legs, side, prefs, cut="belt", offset=0.0, out=0.0, tilt=0.0); print(side, msg)
vl.update()
st = json.loads(legs["tiow_bionic_state"])
for side in ("R", "L"):
    P = T.bio_parts(legs, side)
    th = P["thigh"]
    # how much of the thigh is inside the ball (should be none: the cup is round it)
    from mathutils.bvhtree import BVHTree
    import bmesh as bm_
    b = bm_.new(); b.from_mesh(P["plug"].data); b.transform(P["plug"].matrix_world); tp = BVHTree.FromBMesh(b); b.free()
    b = bm_.new(); b.from_mesh(th.data); b.transform(th.matrix_world); tt = BVHTree.FromBMesh(b); b.free()
    print(side, "plug/thigh overlap pairs:", len(tp.overlap(tt)))
    ball = A(P["hip"].matrix_world)[:3, 3]
    kk = T.bio_kit_side(T.bionic_kit(prefs.bionic_dir), side)
    op = A(th.matrix_world)[:3, :3] @ np.array(kk["thigh"][1]["opening"]); op /= np.linalg.norm(op)
    dpl = A(P["plug"].matrix_world)[:3, :3] @ np.array(kk["plug"][1]["flat_n"]); dpl /= np.linalg.norm(dpl)
    cupc = A(th.matrix_world) @ np.r_[kk["thigh"][1]["cup"], 1]; ballc = A(P["plug"].matrix_world) @ np.r_[kk["plug"][1]["ball"], 1]
    print(side, "ball centre to cup centre %.3f mm" % np.linalg.norm(cupc[:3] - ballc[:3]))
    print(side, "cup opening", op.round(2), "plug stem", dpl.round(2), "angle %.1f" % math.degrees(math.acos(max(-1, min(1, op @ dpl)))))
def view(name, hide):
    for side in ("R", "L"):
        for r in hide: T.bio_parts(legs, side)[r].hide_set(True)
    vl.update()
    obs = [o for o in [legs] + list(T._descendants(legs)) if o.type == 'MESH' and not o.hide_get() and o.display_type != 'WIRE']
    cols = [rend.ORANGE if o.get("tiow_bionic_role") == "plug" else rend.BLUE if o.get("tiow_bionic") else rend.GREY for o in obs]
    rend.render(scene, OUT, name, obs, {"front": (0, 1, -0.1), "side": (1, 0, -0.1), "back": (0, -1, -0.2), "below": (0.2, 0.4, -1)}, cols)
    for side in ("R", "L"):
        for r in hide: T.bio_parts(legs, side)[r].hide_set(False)
view("cup_thigh", ("shin", "foot"))
view("cup_full", ())
# where do plug and thigh intersect: plug vertices inside the thigh (ray parity), relative to the ball frame
def inside(tree, p, d=Vector((0.123, 0.311, 0.942)).normalized()):
    n, pos = 0, Vector(p)
    for _ in range(50):
        loc, nr, i, dd = tree.ray_cast(pos, d, 100)
        if loc is None: break
        n += 1; pos = loc + d * 1e-5
    return n % 2 == 1
for side in ("R", "L"):
    P = T.bio_parts(legs, side); th = P["thigh"]; pl = P["plug"]
    b = bm_.new(); b.from_mesh(th.data); b.transform(th.matrix_world); tt = BVHTree.FromBMesh(b); b.free()
    ball = A(P["hip"].matrix_world)[:3, 3]
    kk = T.bio_kit_side(T.bionic_kit(prefs.bionic_dir), side)
    dpl = A(pl.matrix_world)[:3, :3] @ np.array(kk["plug"][1]["flat_n"]); dpl /= np.linalg.norm(dpl)
    vs = [pl.matrix_world @ v.co for v in pl.data.vertices]
    ins = [np.array(v) for v in vs if inside(tt, v)]
    print(side, "plug vertices inside the thigh:", len(ins), "of", len(vs))
    if ins:
        I = np.array(ins); rel = I - ball
        print("   their height along the stem (mm): %.2f..%.2f, distance from ball centre %.2f..%.2f" % ((rel @ dpl).min(), (rel @ dpl).max(), np.linalg.norm(rel, axis=1).min(), np.linalg.norm(rel, axis=1).max()))
    # and the legs body: thigh vertices inside the cut legs
    dg = bpy.context.evaluated_depsgraph_get(); tl = BVHTree.FromObject(legs, dg)
    inv = legs.matrix_world.inverted()
    tv = [th.matrix_world @ v.co for v in th.data.vertices]
    ins2 = [v for v in tv[::3] if inside(tl, inv @ v)]
    print(side, "thigh vertices (1 in 3) inside the legs:", len(ins2), "of", len(tv[::3]))

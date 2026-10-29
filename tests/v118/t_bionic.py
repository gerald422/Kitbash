"""Bionic Leg (TIOW Inbox 1.18) on Mar Fil marines built through the inbox:
cut + plug + jointed leg posed like the old leg, joints, foot swap, armour
places, remove; both sides; several legs. Renders for a look."""
exec(open("/home/claude/test/v17/common17.py").read())
import bmesh
OUT = "/home/claude/test/v118/out"; os.makedirs(OUT, exist_ok=True)
KIT = "/home/claude/test/v118/kit"
prefs.bionic_dir = KIT
for _f in os.listdir(KIT):                 # armour places saved by an earlier run
    if _f.endswith(".sockets.json"): os.remove(os.path.join(KIT, _f))
VW = {"front": (0, 1, 0.1), "q": (0.7, 0.7, 0.25), "side": (1, 0, 0.05), "back": (-0.3, -1, 0.2)}
def snap(name, root, views=VW):
    vl.update()
    obs = [o for o in [root] + list(T._descendants(root)) if o.type == 'MESH' and not o.hide_get() and o.display_type != 'WIRE']
    cols = [rend.BLUE if o.get("tiow_bionic") else rend.GREY for o in obs]
    rend.render(scene, OUT, name, obs, views, cols)
def ev_mesh(ob):
    dg = bpy.context.evaluated_depsgraph_get(); e = ob.evaluated_get(dg); me = e.to_mesh()
    V = np.array([v.co[:] for v in me.vertices]); F = [list(p.vertices) for p in me.polygons]
    bm = bmesh.new(); bm.from_mesh(me); bm.edges.ensure_lookup_table()
    nonman = sum(1 for e_ in bm.edges if len(e_.link_faces) != 2)
    # islands
    bm.verts.ensure_lookup_table(); seen = set(); isl = 0
    for v in bm.verts:
        if v.index in seen: continue
        isl += 1; stack = [v]; seen.add(v.index)
        while stack:
            x = stack.pop()
            for ed in x.link_edges:
                o = ed.other_vert(x)
                if o.index not in seen: seen.add(o.index); stack.append(o)
    vol = bm.calc_volume(); bm.free(); e.to_mesh_clear()
    return V, nonman, isl, vol
def W(ob): return A(ob.matrix_world)
def pt(ob, p): return (W(ob) @ np.r_[np.asarray(p, float), 1])[:3]
def DK(side, k=1.0):
    """joint points for this side (the right leg is the kit mirrored), at the kit's size k"""
    K = T.bio_kit_side(T.bionic_kit(KIT), side)
    d = {"LINK_LEG": K["plug"][1], "LEG_HIGH": K["thigh"][1], "LEG_LOW": K["shin"][1]}
    d.update({k_: r for k_, (_p, r) in K["feet"].items()})
    out = {}
    for stem, rec in d.items():
        rec = dict(rec)
        for key in ("ball", "glue", "cup", "knee", "ankle"):
            if rec.get(key) is not None:
                rec[key] = list(np.array(rec[key]) * k)
        out[stem] = rec
    return out

def KS(legs, side):
    return float(json.loads(legs["tiow_bionic_state"])[side].get("scale", 1.0))

def check_leg(tag, legs, side, foot_stem):
    D = DK(side, KS(legs, side))
    P = T.bio_parts(legs, side)
    for r in ("plug", "hip", "thigh", "knee", "shin", "ankle", "foot", "cut0", "cut1", "cut2"):
        ck(f"{tag}: {r} made", r in P, sorted(P))
    if not all(r in P for r in ("plug", "hip", "thigh", "knee", "shin", "ankle", "foot")):
        return P
    ball = pt(P["plug"], D["LINK_LEG"]["ball"])
    ck(f"{tag}: hip joint on the plug's ball", np.linalg.norm(W(P["hip"])[:3, 3] - ball) < 0.01)
    ck(f"{tag}: thigh's cup on the ball", np.linalg.norm(pt(P["thigh"], D["LEG_HIGH"]["cup"]) - ball) < 0.01)
    kt = pt(P["thigh"], D["LEG_HIGH"]["knee"]); ks = pt(P["shin"], D["LEG_LOW"]["knee"])
    ck(f"{tag}: knee hinge: thigh and shin centres together", np.linalg.norm(kt - ks) < 0.03, np.linalg.norm(kt - ks))
    ck(f"{tag}: knee joint on the hinge", np.linalg.norm(W(P["knee"])[:3, 3] - kt) < 0.01)
    xt, xs, xk = (W(P[r])[:3, 0] / np.linalg.norm(W(P[r])[:3, 0]) for r in ("thigh", "shin", "knee"))
    ck(f"{tag}: thigh, shin and knee joint share the hinge axis", xt @ xs > 0.9999 and xt @ xk > 0.9999, (xt @ xs, xt @ xk))
    an = pt(P["shin"], D["LEG_LOW"]["ankle"])
    ck(f"{tag}: ankle joint on the shin's ball", np.linalg.norm(W(P["ankle"])[:3, 3] - an) < 0.01)
    ck(f"{tag}: foot's cup on the ankle ball", np.linalg.norm(pt(P["foot"], D[foot_stem]["cup"]) - an) < 0.01)
    # the plug's neck and glue face inside the leg, its ball coming out of the cut (a stump)
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    tree = BVHTree.FromObject(legs, dg); inv = legs.matrix_world.inverted()
    st_ = json.loads(legs["tiow_bionic_state"])[side]
    nl = Vector(st_["d"]).normalized()
    def inside(p, dd=Vector((0.123, 0.311, 0.942)).normalized()):
        n_, pos = 0, Vector(p)
        for _ in range(80):
            hit = tree.ray_cast(pos, dd, 1000)
            if hit[0] is None: break
            n_ += 1; pos = hit[0] + dd * 1e-5
        return n_ % 2 == 1
    fn = np.array(D["LINK_LEG"]["flat_n"]); fn /= np.linalg.norm(fn); e1 = np.cross(fn, [0, 1.0, 0]); e1 /= np.linalg.norm(e1); e2 = np.cross(fn, e1)
    Mp = W(P["plug"]); kk_ = KS(legs, side); ins = tot = 0
    tree_p = BVHTree.FromObject(P["plug"], dg); invp = P["plug"].matrix_world.inverted()
    def inside_p(p, dd=Vector((0.123, 0.311, 0.942)).normalized()):
        n_, pos = 0, Vector(p)
        for _ in range(80):
            hit = tree_p.ray_cast(pos, dd, 1000)
            if hit[0] is None: break
            n_ += 1; pos = hit[0] + dd * 1e-5
        return n_ % 2 == 1
    hc = T.BIO_PLUG_STEP * kk_ - 0.03 + 0.03            # just above the trimmed top: covered by the leg or the plug's skirt
    rs = math.sqrt(max((2.689 * kk_) ** 2 - hc * hc, 0.0))
    for rr in (0.0, 0.3, 0.6, 0.8, 0.95):
        for a in np.linspace(0, 2 * np.pi, 1 if rr == 0 else 24, endpoint=False):
            q = np.array(D["LINK_LEG"]["ball"]) + hc * fn + rr * rs * (np.cos(a) * e1 + np.sin(a) * e2)
            wq = Vector((Mp @ np.r_[q, 1])[:3])
            ins += inside(inv @ wq) or inside_p(Vector(np.array(Mp)[:3, :3].T @ (np.array(wq) - Mp[:3, 3])))
            tot += 1
    n_plug = Mp[:3, :3] @ fn; n_plug /= np.linalg.norm(n_plug)
    n_cut = np.array(legs.matrix_world.to_3x3() @ nl); n_cut /= np.linalg.norm(n_cut)
    ck(f"{tag}: plug a stump: no flat top showing (leg or skirt over it), square to the cut", ins / tot > 0.95 and n_plug @ n_cut > 0.9999,
       (ins, tot, round(float(n_plug @ n_cut), 5)))
    Ve, nonman, isl, vol = ev_mesh(legs)
    ck(f"{tag}: cut legs still one closed piece", nonman == 0 and isl == 1, (nonman, isl))
    return P

# ---- marine 1: legs 29, bionic right leg
select(None)
TORSO = f"{AM}/Chest/24-Torso-3.stl"
torso = send(TORSO, "Chests", (0, 0, 0))
select(torso); legs = send(f"{AM}/Legs/29-Legs-2.stl", "Legs")
select(torso); send(f"{AM}/Arms/106-Arm-7-R-A.stl", "Arms")
select(torso); send(f"{AM}/Arms/109-Arm-7-L-B.stl", "Arms")
select(torso); send(f"{AM}/Helmet-Heads/3-Helmet-3.stl", "Heads")
ck("legs have Shin R and Shin L", sock(legs, "Shin R") is not None and sock(legs, "Shin L") is not None)
_V0, _n0, _i0, vol0 = ev_mesh(legs)
snap("m1_before", torso)
select(legs)
t = time.time(); r = bpy.ops.tiow.bionic_leg(side='R'); print(f"      [{time.time() - t:4.1f}s]", T._state["last"])
ck("Bionic Leg R ran", r == {'FINISHED'}, T._state["last"])
m = legs.modifiers.get("TIOW Bionic Cut")
ck("legs: live cut (Boolean, Manifold) + tidy", m is not None and m.solver == 'MANIFOLD' and legs.modifiers.get("TIOW Bionic Tidy") is not None)
ck("Shin R anchor gone, Shin L kept", sock(legs, "Shin R") is None and sock(legs, "Shin L") is not None)
P = check_leg("m1 R", legs, "R", "FOOT_3")
_V1, _n1, _i1, vol1 = ev_mesh(legs)
ck("the leg came off (legs volume down by a leg's worth)", vol0 - vol1 > 400, (vol0, vol1))
snap("m1_bionic_R", torso)
# the knee turns on its hinge only
D = DK("R", KS(legs, "R"))
ck("kit fitted to the legs (110-125 %)", 1.10 <= KS(legs, "R") <= 1.25, KS(legs, "R"))
k = P["knee"]; th0 = W(P["thigh"]).copy(); f0 = W(P["foot"]).copy()
k.rotation_euler.x += math.radians(25); k.rotation_euler.y += math.radians(10); vl.update()
ck("knee: locked off its other axes", k.lock_rotation[1] and k.lock_rotation[2])
ck("turning the knee moves the shin and foot, not the thigh", np.allclose(W(P["thigh"]), th0) and not np.allclose(W(P["foot"]), f0))
kt = pt(P["thigh"], D["LEG_HIGH"]["knee"]); ks = pt(P["shin"], D["LEG_LOW"]["knee"])
ck("after turning: shin still on the hinge", np.linalg.norm(kt - ks) < 0.03)
h = P["hip"]; h.rotation_euler.z += math.radians(15); vl.update()
ck("turning the hip keeps the thigh's cup on the ball", np.linalg.norm(pt(P["thigh"], D["LEG_HIGH"]["cup"]) - pt(P["plug"], D["LINK_LEG"]["ball"])) < 0.01)
select(legs); bpy.ops.tiow.bionic_follow(side='R'); vl.update()
ck("Follow Old Leg puts the foot back", np.allclose(W(P["foot"]), f0, atol=1e-4))
# foot swap
st = json.loads(legs["tiow_bionic_state"])["R"]
sole_ref = None
select(legs); bpy.ops.tiow.bionic_foot(side='R', step=3); vl.update()
st2 = json.loads(legs["tiow_bionic_state"])["R"]
ck("Next Foot x3 -> FOOT_6", st2["foot"] == "FOOT_6", st2["foot"])
P = check_leg("m1 R foot 6", legs, "R", "FOOT_6")
# the new foot's sole on the old sole: its lowest point along the foot's up at the same height
def sole_h(ob, up, A_):
    v = np.array([x.co[:] for x in ob.data.vertices]); w = (W(ob) @ np.c_[v, np.ones(len(v))].T).T[:, :3]
    return float(((w - A_) @ up).min())
uf_w = W(legs)[:3, :3] @ np.array(st2["uf"]); uf_w /= np.linalg.norm(uf_w)
A_w = (W(legs) @ np.r_[np.array(st2["A"]), 1])[:3]
ck("foot 6 stands on the old sole (unless the leg is too short)", abs(sole_h(P["foot"], uf_w, A_w) - st2["sole"]) < 0.05 or "short" in T._state["last"], (sole_h(P["foot"], uf_w, A_w), st2["sole"], T._state["last"]))
snap("m1_bionic_R_foot6", torso)
# armour: parked, moved, saved; a left leg then gets it mirrored
select(legs); bpy.ops.tiow.bionic_armour(side='R', stem="LEG_LOW_ARMOR")
P = T.bio_parts(legs, "R"); arm = P.get("armour:LEG_LOW_ARMOR")
ck("shin plate added (parked: no place saved yet)", arm is not None and arm.get("tiow_bionic_parked"))
# 'place it by eye': in front of the shin's plate
shin = P["shin"]
arm.matrix_world = shin.matrix_world @ Matrix.Translation((28.04, 31.18 - 2.6, -0.3)); vl.update()
F_by_eye = A(shin.matrix_world.inverted() @ arm.matrix_world)
select(legs); bpy.ops.tiow.bionic_save_armour(side='R')
sc = json.load(open(os.path.join(KIT, "LEG_LOW_ARMOR.sockets.json")))
ck("armour place saved in its sockets file", "fit" in sc.get("bionic", {}), sc)
# ---- left leg on the same model
select(legs)
t = time.time(); r = bpy.ops.tiow.bionic_leg(side='L'); print(f"      [{time.time() - t:4.1f}s]", T._state["last"])
check_leg("m1 L", legs, "L", "FOOT_3")
ck("left leg the same size as the right", KS(legs, "L") == KS(legs, "R"), (KS(legs, "L"), KS(legs, "R")))
select(legs); bpy.ops.tiow.bionic_armour(side='L', stem="LEG_LOW_ARMOR")
PL = T.bio_parts(legs, "L"); armL = PL.get("armour:LEG_LOW_ARMOR")
MX = np.diag([-1.0, 1, 1, 1])
FL = A(PL["shin"].matrix_world.inverted() @ armL.matrix_world)
ck("left leg: the shin plate at the saved place, mirrored", armL is not None and not armL.get("tiow_bionic_parked") and np.allclose(FL, MX @ F_by_eye @ MX, atol=1e-4))
_cuts = [o for sd in ("R", "L") for r, o in T.bio_parts(legs, sd).items() if r.startswith("cut")]
ck("both cuts in one Boolean", len(_cuts) >= 6 and set(T._bio_cut_collection(legs).objects) == set(_cuts), [o.name for o in T._bio_cut_collection(legs).objects])
snap("m1_bionic_both", torso)
# remove right: the right leg comes back, left stays
select(legs); bpy.ops.tiow.bionic_remove(side='R')
ck("remove R: R parts gone, L kept", not T.bio_parts(legs, "R") and T.bio_parts(legs, "L"))
ck("remove R: Shin R anchor back", sock(legs, "Shin R") is not None)
select(legs); bpy.ops.tiow.bionic_remove(side='L')
ck("remove L: no modifiers, no cutter collection, no state", not legs.modifiers.get("TIOW Bionic Cut") and not legs.modifiers.get("TIOW Bionic Tidy")
   and bpy.data.collections.get(f"Bionic Cut - {legs.name}") is None and "tiow_bionic_state" not in legs)
_V2, _n2, _i2, vol2 = ev_mesh(legs)
ck("legs whole again", abs(vol2 - vol0) < 1e-3, (vol0, vol2))
# mirror refuses on a bionic model
select(legs); bpy.ops.tiow.bionic_leg(side='R')
select(legs)
try:
    rr = bpy.ops.tiow.mirror_part()
except RuntimeError as exc:
    rr = str(exc)
ck("Mirror refuses legs with a bionic leg", rr != {'FINISHED'}, rr)

# ---- more legs: one side each, renders
for i, (rel, side_) in enumerate([(f"{AM}/Legs/31-Legs-4.stl", "L"), (f"{AM}/Legs(JumpPack)/37-Legs-3-A.stl", "R"),
                                  (f"{AM}/Legs/30-Legs-3.stl", "R"), (f"{AM}/Legs/32-Legs-5.stl", "L"),
                                  ("All Mar All the time/VeteranBladeSquad/VeteranBladeSquad/Body/Body-RawSTL/19-Legs-1-A.stl", "R")]):
    select(None); tt = send(TORSO if i != 1 else f"{AM}/Chest/23-Torso-2.stl", "Chests", (60 * (i + 1), 0, 0))
    select(tt); lg = send(rel, "Legs")
    select(lg)
    t = time.time(); r = bpy.ops.tiow.bionic_leg(side=side_); print(f"      [{time.time() - t:4.1f}s]", T._state["last"])
    tag = os.path.basename(rel)[:-4] + " " + side_
    ck(f"{tag}: Bionic Leg ran", r == {'FINISHED'}, T._state["last"])
    if r == {'FINISHED'}:
        n0 = len(fails)
        check_leg(tag, lg, side_, "FOOT_3")
        if "Blade" in rel and len(fails) > n0:          # Josh: not expected to work with the tabard
            print("  (known) Bladeguard tabard:", fails[n0:]); del fails[n0:]
        snap(f"legs_{i}_{os.path.basename(rel)[:-4]}_{side_}", tt)
    # free the memory before the next one
    for o in [tt] + list(T._descendants(tt)):
        if o.name in bpy.data.objects: bpy.data.objects.remove(o)
    for me in [m for m in bpy.data.meshes if m.users == 0]: bpy.data.meshes.remove(me)

print("FAILS:", fails)

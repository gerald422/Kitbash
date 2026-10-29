"""Bionic Leg (TIOW Inbox 1.18) on Mar Fil marines built through the inbox:
cut + plug + jointed leg posed like the old leg, joints, foot swap, armour
places, remove; both sides; several legs. Renders for a look."""
exec(open("/home/claude/test/v17/common17.py").read())
import bmesh
OUT = "/home/claude/test/v118/out"; os.makedirs(OUT, exist_ok=True)
KIT = "/home/claude/test/v118/kit"
prefs.bionic_dir = KIT
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
D = T.BIONIC_DEFAULT

def check_leg(tag, legs, side, foot_stem):
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
    # the plug's glue face sits on the cut face of the legs
    g = pt(P["plug"], D["LINK_LEG"]["glue"])
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    tree = BVHTree.FromObject(legs, dg)
    loc, nrm, _i, dist = tree.find_nearest(legs.matrix_world.inverted() @ Vector(g))
    n_plug = W(P["plug"])[:3, :3] @ np.array(D["LINK_LEG"]["flat_n"]); n_plug /= np.linalg.norm(n_plug)
    n_cut = np.array(legs.matrix_world.to_3x3() @ nrm); n_cut /= np.linalg.norm(n_cut)
    ck(f"{tag}: plug's glue face on the cut face (centre on it, faces together)", dist < 0.02 and n_plug @ n_cut < -0.999,
       (round(dist, 4), round(float(n_plug @ n_cut), 5)))
    Ve, nonman, isl, vol = ev_mesh(legs)
    ck(f"{tag}: cut legs still one closed piece", nonman == 0 and isl == 1, (nonman, isl))
    return P

TORSO = f"{AM}/Chest/24-Torso-3.stl"
# ---- legs other makers make: no Mar Fil shin points found, a clicked Shin anchor's three points instead
select(None); tc = send(TORSO, "Chests", (0, 120, 0))
select(tc); lc = send(f"{AM}/Legs/29-Legs-2.stl", "Legs")
select(lc); bpy.ops.tiow.bionic_leg(side='R'); vl.update()
ref = A(lc.matrix_world.inverted() @ T.bio_parts(lc, "R")["plug"].matrix_world)
ref_foot = A(lc.matrix_world.inverted() @ T.bio_parts(lc, "R")["foot"].matrix_world)
select(lc); bpy.ops.tiow.bionic_remove(side='R')
real = T.find_shin_points
T.find_shin_points = lambda V, T_: []
try:
    select(lc); r = bpy.ops.tiow.bionic_leg(side='R'); vl.update()
finally:
    T.find_shin_points = real
ck("clicked Shin anchor: Bionic Leg runs without Mar Fil's shin points", r == {'FINISHED'}, T._state["last"])
if r == {'FINISHED'}:
    got = A(lc.matrix_world.inverted() @ T.bio_parts(lc, "R")["plug"].matrix_world)
    gotf = A(lc.matrix_world.inverted() @ T.bio_parts(lc, "R")["foot"].matrix_world)
    ck("... cut and plug within 1.5 mm / 3 deg of the found-points result", np.linalg.norm(got[:3, 3] - ref[:3, 3]) < 1.5 and ang(got, ref) < 3.0, (np.linalg.norm(got[:3, 3] - ref[:3, 3]), ang(got, ref)))
    ck("... foot within 0.3 mm / 3 deg", np.linalg.norm(gotf[:3, 3] - ref_foot[:3, 3]) < 0.3 and ang(gotf, ref_foot) < 3.0, (np.linalg.norm(gotf[:3, 3] - ref_foot[:3, 3]), ang(gotf, ref_foot)))

print("FAILS:", fails)

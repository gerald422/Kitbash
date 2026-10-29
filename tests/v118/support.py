exec(open("/home/claude/test/v17/common17.py").read())
from mathutils.bvhtree import BVHTree
import bmesh
prefs.bionic_dir = "/home/claude/test/v118/kit"
KIT = T.bionic_kit(prefs.bionic_dir)
res = []
for i, rel in enumerate(sys.argv[sys.argv.index("--") + 1:]):
    select(None); torso = send(f"{AM}/Chest/24-Torso-3.stl", "Chests", (80 * i, 0, 0))
    select(torso); legs = send(rel if "/" in rel else f"{AM}/Legs/{rel}.stl", "Legs")
    for side in ("R", "L"):
        msg = T.bionic_build(legs, side, prefs, cut="belt")
    vl.update(); dg = bpy.context.evaluated_depsgraph_get()
    tree = BVHTree.FromObject(legs, dg); inv = legs.matrix_world.inverted()
    me = bpy.data.meshes.new_from_object(legs.evaluated_get(dg)); body = bpy.data.objects.new("body", me); scene.collection.objects.link(body); body.matrix_world = legs.matrix_world
    st = json.loads(legs["tiow_bionic_state"])
    for side in ("R", "L"):
        P = T.bio_parts(legs, side); K = dict(T.bio_kit_side(KIT, side)["plug"][1])
        K["glue"] = list(np.array(K["glue"]) * st[side].get("scale", 1.0))
        Mp = A(P["plug"].matrix_world); nl = Vector(st[side]["d"]).normalized()
        fn = np.array(K["flat_n"]); fn /= np.linalg.norm(fn); e1 = np.cross(fn, [0, 1.0, 0]); e1 /= np.linalg.norm(e1); e2 = np.cross(fn, e1)
        touch = tot = 0
        def inside_(p, dd=Vector((0.123, 0.311, 0.942)).normalized()):
            n_, pos = 0, Vector(p)
            for _ in range(80):
                hh = tree.ray_cast(pos, dd, 1000)
                if hh[0] is None: break
                n_ += 1; pos = hh[0] + dd * 1e-5
            return n_ % 2 == 1
        kk2 = st[side].get("scale", 1.0); hc = T.BIO_PLUG_STEP * kk2 - 0.03 - 0.03
        rs = math.sqrt(max((2.689 * kk2) ** 2 - hc * hc, 0.0))
        for rr in (0.0, 0.3, 0.6, 0.8, 0.95):
            for a in np.linspace(0, 2 * np.pi, 1 if rr == 0 else 24, endpoint=False):
                q = np.array(T.bio_kit_side(KIT, side)["plug"][1]["ball"]) * kk2 + hc * fn + rr * rs * (np.cos(a) * e1 + np.sin(a) * e2)
                w = inv @ Vector((Mp @ np.r_[q, 1])[:3]); tot += 1
                touch += inside_(w)
        # the plug itself: one closed piece
        import bmesh as _bm
        b_ = _bm.new(); b_.from_mesh(P["plug"].data); nm = sum(1 for e in b_.edges if len(e.link_faces) != 2); b_.free()
        # thigh overlap with the body
        th = P["thigh"]; c = bpy.data.objects.new("x", th.data.copy()); scene.collection.objects.link(c); c.matrix_world = th.matrix_world
        m = c.modifiers.new("i", 'BOOLEAN'); m.operation = 'INTERSECT'; m.object = body; m.solver = 'EXACT'
        vl.update(); dg2 = bpy.context.evaluated_depsgraph_get(); r = bpy.data.meshes.new_from_object(c.evaluated_get(dg2))
        bm = bmesh.new(); bm.from_mesh(r); ov = abs(bm.calc_volume()); bm.free()
        bpy.data.objects.remove(c); bpy.data.meshes.remove(r)
        k = T.bio_kit_side(KIT, side)
        op = A(th.matrix_world)[:3, :3] @ np.array(k["thigh"][1]["opening"]); op /= np.linalg.norm(op)
        dpl = A(P["plug"].matrix_world)[:3, :3] @ fn; dpl /= np.linalg.norm(dpl)
        # the ball's sides against the leg's sides (across the leg, square to its line, at the leg's top)
        V0, T0 = T.mesh_np(legs); V0 = V0 / float(legs.get("tiow_unit") or 1.0)
        pts_ = T._bio_side_shin_points(legs, V0, T0); plan_ = T.bio_plan(V0, T0, *pts_[side])
        belt_ = T.bio_belt(legs, V0); lat_ = belt_["lat"][side]
        w_, dep_, mid_ = T.bio_leg_section(V0, T0, plan_, lat_)
        dl = plan_["d"] / np.linalg.norm(plan_["d"]); la = lat_ - (lat_ @ dl) * dl; la /= np.linalg.norm(la)
        Bc = (np.linalg.inv(A(legs.matrix_world)) @ np.r_[A(P["hip"].matrix_world)[:3, 3], 1])[:3]
        kk = st[side]["scale"]; rb = 2.689 * kk
        sec_lo, sec_hi = mid_ @ la - w_ / 2, mid_ @ la + w_ / 2
        ub_ = belt_["up"]; lp = lat_ - (lat_ @ ub_) * ub_; lp /= np.linalg.norm(lp)
        opl = np.linalg.inv(A(legs.matrix_world))[:3, :3] @ op; opl /= np.linalg.norm(opl)
        dd_ = np.array(st[side]["d"]); dd_ /= np.linalg.norm(dd_)
        ang = lambda v: math.degrees(math.atan2(-(v @ lp), v @ ub_))
        hx = np.linalg.inv(A(legs.matrix_world))[:3, :3] @ A(P["thigh"].matrix_world)[:3, 0]; hx /= np.linalg.norm(hx)
        line0 = f"   cup opening leans in {ang(opl):.0f} deg, the cut {ang(dd_):.0f} deg (swing {st[side].get('swing', 0):.0f}); knee hinge vs level-across {math.degrees(math.acos(min(1, abs(hx @ lp)))):.0f} deg; foot off {T._state.get('last', '')[-60:]}"
        line = (f"{os.path.basename(rel)} {side}: kit {kk * 100:.0f}% (leg {w_:.2f} wide x {dep_:.2f} deep, ball {2 * rb:.2f}); "
                f"ball's inner side {Bc @ la - rb - sec_lo:+.2f} / outer side {Bc @ la + rb - sec_hi:+.2f} mm from the leg's; "
                f"plug top covered {touch}/{tot} (open edges {nm}); thigh in the body {ov:.3f} mm3; cup {math.degrees(math.acos(max(-1, min(1, op @ dpl)))):.0f} deg off the ball"
                + (" notch" if any(o.name.endswith("notch") for o in P.values()) else ""))
        print("RES", line); print("RES", line0); res.append(line)
    bpy.data.objects.remove(body)
    for o in [torso] + list(T._descendants(torso)):
        if o.name in bpy.data.objects: bpy.data.objects.remove(o)

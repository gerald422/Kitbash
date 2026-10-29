"""Settle bias of the Chaplain belt bits at Mar Fil's spots (what Save Fit for Folder would record there)."""
exec(open("/home/claude/test/v18/common18.py").read())
K = "All Mar All the time/ChaplainWithJumpPack (1)/ChaplainWithJumpPack"
PO = json.load(open("/home/claude/kits/cj/pose.json")); ACC = json.load(open("/home/claude/kits/cj/acc.json"))
sk, co = T._part_sockets()
spec = T.DEFAULT_JOINTS["Accessories"]; sk.ensure_type(scene, "Hip R")
res = {}
for i, X in enumerate("ABCD"):
    select(None); lg = send(f"{K}/Legs/Legs-Raw-STL/{os.path.basename(PO[X]['legs'])}", "Bodies", (70 * i, 0, 0))
    bpy.context.view_layer.update()
    for a in ("23-Book", "24-Badge", "25-Holster", "26-Grenade"):
        # a temporary anchor at Mar Fil's spot (legs file coords: P_X @ K)
        M = Matrix((np.array(PO[X]["P"]) @ np.array(ACC["K"][a])).tolist())
        e = bpy.data.objects.new("tmp_anchor", None); scene.collection.objects.link(e)
        e["ws_type"] = "Hip R"; e.parent = lg; e.matrix_world = frame(lg) @ M
        for c in lg.children:
            if c.get("ws_type") == "Hip R" and c is not e: c["ws_type"] = "_off"
        select(None); p = send(f"{K}/Accesories/Accesories-Raw-STL/{a}.stl", "Accessories")
        err, _ = sk.snap_part_to_socket(bpy.context, p, e, tname="Hip R"); bpy.context.view_layer.update()
        want = frame(lg) @ Matrix(np.array(PO[X]["P"]).tolist())
        print(f"   {X} {a}: snapped at Mar Fil's spot: {ang(frame(p), want):.3f} deg {np.linalg.norm(A(frame(p))[:3,3]-A(want)[:3,3]):.3f} mm", err or "")
        hosts = T._model_around(e)
        tilt = T.rock_settle(p, hosts, e.matrix_world, float(spec["rock"]), dry=True)
        others = hosts + T._occupants(e, co, bpy.context.view_layer, False, (p,))
        s0 = T.settle_onto(p, others, e.matrix_world.to_3x3() @ T._settle_axis(spec), push_out=True, touch=float(spec.get("touch") or 0.0), frame=e.matrix_world, dry=True)
        R = np.array(tilt); print(f"      rock wants {math.degrees(math.acos(max(-1,min(1,(np.trace(R)-1)/2)))):.1f} deg, slide {s0}")
        res.setdefault(a, []).append({"rock": R.tolist(), "slide": s0})
        T._remove_part(p); bpy.data.objects.remove(e)
        for c in lg.children:
            if c.get("ws_type") == "_off": c["ws_type"] = "Hip R"
json.dump(res, open("/home/claude/kits/cj/bias_raw.json", "w"), indent=1)

exec(open("/home/claude/test/v17/common17.py").read())
prefs.bionic_dir = "/home/claude/test/v118/kit"
KIT = T.bionic_kit(prefs.bionic_dir)
for i, rel in enumerate(sys.argv[sys.argv.index("--") + 1:]):
    select(None); torso = send(f"{AM}/Chest/24-Torso-3.stl", "Chests", (80 * i, 0, 0))
    select(torso); legs = send(f"{AM}/Legs/{rel}.stl", "Legs")
    for side in ("R", "L"):
        T.bionic_build(legs, side, prefs, cut="belt")
    vl.update(); dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(legs.evaluated_get(dg))
    V = np.array([v.co[:] for v in me.vertices]); F = [list(p.vertices) for p in me.polygons]
    Tr = np.array([f for f in F if len(f) == 3] + [[f[0], f[j], f[j + 1]] for f in F if len(f) > 3 for j in range(1, len(f) - 1)])
    st = json.loads(legs["tiow_bionic_state"]); Li = np.linalg.inv(A(legs.matrix_world))
    for side in ("R", "L"):
        P = T.bio_parts(legs, side); k = st[side]["scale"]
        n = np.array(st[side]["d"]); n /= np.linalg.norm(n)
        B = (Li @ np.r_[A(P["hip"].matrix_world)[:3, 3], 1])[:3]
        h_trim = T.BIO_PLUG_STEP * k - 0.03
        r_trim = math.sqrt((2.689 * k) ** 2 - h_trim ** 2)
        out = []
        for lift in (0.05, 0.3, 0.6):                     # body outline just above the trimmed top
            c = B + (h_trim + lift) * n
            loops = T.bio_slice(V, Tr, c, n, 12.0)
            best = None
            for L in loops:
                Pl = np.asarray(L[0]); q = Pl - c; q -= np.outer(q @ n, n)
                # does the loop surround the axis? winding via angle sum
                e1 = np.cross(n, [0, 1.0, 0]); e1 /= np.linalg.norm(e1); e2 = np.cross(n, e1)
                ang = np.unwrap(np.arctan2(q @ e2, q @ e1)); wind = abs(ang[-1] - ang[0] + (np.arctan2(q[0] @ e2, q[0] @ e1) - np.arctan2(q[-1] @ e2, q[-1] @ e1))) / (2 * math.pi)
                d_ = np.linalg.norm(q, axis=1)
                if wind > 0.5 and (best is None or d_.min() > best[0]):
                    best = (d_.min(), Pl[np.argmin(d_)])
            if best is None:
                out.append(f"+{lift}: axis not inside"); continue
            out.append(f"+{lift}: outline {best[0]:.2f} from the axis (ball edge {r_trim:.2f}) -> ledge up to {max(0, r_trim - best[0]):.2f}")
        print(f"RES {rel} {side} k {k:.2f}: " + "; ".join(out))
    for o in [torso] + list(T._descendants(torso)):
        if o.name in bpy.data.objects: bpy.data.objects.remove(o)

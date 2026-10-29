exec(open("/home/claude/test/v17/common17.py").read())
import bmesh
prefs.bionic_dir = "/home/claude/test/v118/kit"
LEGS = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "29-Legs-2"
select(None); torso = send(f"{AM}/Chest/24-Torso-3.stl", "Chests", (0, 0, 0))
select(torso); legs = send(f"{AM}/Legs/{LEGS}.stl", "Legs")
for side in ("R", "L"):
    print(side, T.bionic_build(legs, side, prefs, cut="belt"))
vl.update()
dg = bpy.context.evaluated_depsgraph_get()
me = bpy.data.meshes.new_from_object(legs.evaluated_get(dg)); body = bpy.data.objects.new("body", me); scene.collection.objects.link(body); body.matrix_world = legs.matrix_world
print("cut legs: %d verts, manifold %s" % (len(me.vertices), T._bio_manifold(body)))
def vol(m):
    bm = bmesh.new(); bm.from_mesh(m); v = bm.calc_volume(signed=True); bm.free(); return v
st = json.loads(legs["tiow_bionic_state"])
inv = np.array(legs.matrix_world.inverted())
def frame(side):
    up = np.array(st[side]["d"]); up /= np.linalg.norm(up)
    lat = np.array(st[side]["C"]) - np.array(st["L" if side == "R" else "R"]["C"]); lat -= (lat @ up) * up; lat /= np.linalg.norm(lat)
    return lat, np.cross(up, lat), up
for side in ("R", "L"):
    P = T.bio_parts(legs, side)
    ball = (inv @ np.r_[P["hip"].matrix_world.translation[:], 1])[:3]
    lat, fw, up = frame(side)
    for role in ("plug", "thigh", "shin", "foot"):
        ob = P[role]
        c = bpy.data.objects.new("x", ob.data.copy()); scene.collection.objects.link(c); c.matrix_world = ob.matrix_world
        m = c.modifiers.new("i", 'BOOLEAN'); m.operation = 'INTERSECT'; m.object = body; m.solver = 'EXACT'
        vl.update(); dg = bpy.context.evaluated_depsgraph_get()
        r = bpy.data.meshes.new_from_object(c.evaluated_get(dg))
        V = np.array([(inv @ np.r_[(c.matrix_world @ v.co)[:], 1])[:3] for v in r.vertices]) if len(r.vertices) else np.zeros((0, 3))
        v_ = abs(vol(r)) / float(legs.get("tiow_unit") or 1) ** 3
        if len(V):
            rel = V - ball
            print(f"{side} {role}: overlap {v_:.3f} mm3; out (towards this hip) {(rel @ lat).min():.2f}..{(rel @ lat).max():.2f}  front {(rel @ fw).min():.2f}..{(rel @ fw).max():.2f}  up {(rel @ up).min():.2f}..{(rel @ up).max():.2f}")
        else:
            print(f"{side} {role}: no overlap")
        bpy.data.objects.remove(c); bpy.data.meshes.remove(r)

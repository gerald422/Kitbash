exec(open("/home/claude/test/v17/common17.py").read())
import bmesh
prefs.bionic_dir = "/home/claude/test/v118/kit"
select(None); torso = send(f"{AM}/Chest/24-Torso-3.stl", "Chests", (0, 0, 0))
select(torso); legs = send(f"{AM}/Legs/31-Legs-4.stl", "Legs")
T.bionic_build(legs, "L", prefs, cut="belt")
st = json.loads(legs["tiow_bionic_state"])["L"]
s = 1.0
sv, sf = T._bio_skirt_mesh(st["skirt"], s)
me = bpy.data.meshes.new("sk"); me.from_pydata(sv.tolist(), [], sf); me.update()
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
print("skirt: verts", len(bm.verts), "faces", len(bm.faces), "open edges", sum(1 for e in bm.edges if len(e.link_faces) != 2), "volume", round(bm.calc_volume(signed=True), 3))
bm.free()
sk = st["skirt"]; print("B", np.round(sk["B"], 2), "n", np.round(sk["n"], 3))
pl = T.bio_parts(legs, "L")["plug"]
Bp = np.linalg.inv(A(legs.matrix_world)) @ np.r_[A(T.bio_parts(legs, "L")["hip"].matrix_world)[:3, 3], 1]
print("hip (ball) in legs coords", np.round(Bp[:3], 2))
# test the join directly on a copy of the plug
c = bpy.data.objects.new("pc", pl.data.copy()); scene.collection.objects.link(c); c.matrix_world = pl.matrix_world
Pinv = np.linalg.inv(np.linalg.inv(A(legs.matrix_world)) @ A(pl.matrix_world))
loc = (Pinv @ np.c_[sv, np.ones(len(sv))].T).T[:, :3]
n0 = len(c.data.polygons)
T._bio_join_hull(c, loc, sf)
b2 = bmesh.new(); b2.from_mesh(c.data); print("join: faces", n0, "->", len(b2.faces), "open", sum(1 for e in b2.edges if len(e.link_faces) != 2), "volume", round(b2.calc_volume(), 3)); b2.free()
b3 = bmesh.new(); b3.from_mesh(pl.data); print("plug as built: volume", round(b3.calc_volume(), 3)); b3.free()

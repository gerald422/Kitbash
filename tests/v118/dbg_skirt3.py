exec(open("/home/claude/test/v17/common17.py").read())
prefs.bionic_dir = "/home/claude/test/v118/kit"
select(None); torso = send(f"{AM}/Chest/24-Torso-3.stl", "Chests", (0, 0, 0))
select(torso); legs = send(f"{AM}/Legs/31-Legs-4.stl", "Legs")
orig = T._bio_skirt_mesh
def spy(sk, s=1.0):
    v, f = orig(sk, s)
    print("SKIRT B", np.round(sk["B"], 2), "h_top", round(sk["h_top"], 2), "top min/max", round(min(sk["top"]), 2), round(max(sk["top"]), 2), "verts range", np.round(v.min(0), 1), np.round(v.max(0), 1))
    return v, f
T._bio_skirt_mesh = spy
oj = T._bio_join_hull
def spy2(ob, pts, faces=None):
    print("JOIN", ob.name, "pts local range", np.round(np.min(pts, 0), 1), np.round(np.max(pts, 0), 1), "ob matrix t", np.round(np.array(ob.matrix_world.translation), 2))
    return oj(ob, pts, faces)
T._bio_join_hull = spy2
for side in ("R", "L"):
    T.bionic_build(legs, side, prefs, cut="belt")
    pl = T.bio_parts(legs, side)["plug"]
    V = np.array([v.co[:] for v in pl.data.vertices]); print("PLUG", side, "local range", np.round(V.min(0), 1), np.round(V.max(0), 1))

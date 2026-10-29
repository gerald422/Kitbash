exec(open("/home/claude/test/v17/common17.py").read())
prefs.bionic_dir = "/home/claude/test/v118/kit"
select(None); torso = send(f"{AM}/Chest/24-Torso-3.stl", "Chests", (0, 0, 0))
select(torso); legs = send(f"{AM}/Legs/29-Legs-2.stl", "Legs")
for side in ("R", "L"):
    print(side, T.bionic_build(legs, side, prefs, cut="belt")); print("   swing", round(json.loads(legs["tiow_bionic_state"])[side].get("swing", 0), 1))
vl.update()
st = json.loads(legs["tiow_bionic_state"])
s = float(legs.get("tiow_unit") or 1.0)
V, Tr = T.mesh_np(legs); V = V / s
belt = T.bio_belt(legs, V)
kit = T.bionic_kit(prefs.bionic_dir)
Lw = A(legs.matrix_world); Li = np.linalg.inv(Lw)
for side in ("R", "L"):
    k = T.bio_kit_side(kit, side)
    P = T.bio_parts(legs, side)
    M = Li @ A(P["thigh"].matrix_world)
    up = belt["up"]; out = belt["lat"][side]; out = out - (out @ up) * up; out /= np.linalg.norm(out); fw = np.cross(up, out) if side == "R" else np.cross(out, up)
    def show(v): v = v / np.linalg.norm(v); return f"out {v @ out:+.2f} fwd {v @ fw:+.2f} up {v @ up:+.2f}"
    op = M[:3, :3] @ np.array(k["thigh"][1]["opening"])
    zt = M[:3, :3] @ np.array([0, 0, 1.0])
    xt = M[:3, :3] @ np.array([1.0, 0, 0])
    print(side, "plug axis d:", show(np.array(st[side]["d"])))
    print(side, "cup opening:", show(op))
    print(side, "thigh axis :", show(zt), "| thigh +X:", show(xt), "| det", round(np.linalg.det(M[:3, :3]), 3))
    print(side, "old leg d  :", show(T.bio_plan(V, Tr, *T._bio_side_shin_points(legs, V, Tr)[side])["d"]) if False else "")

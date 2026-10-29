exec(open("/home/claude/test/v17/common17.py").read())
prefs.bionic_dir = "/home/claude/test/v118/kit"
select(None); torso = send(f"{AM}/Chest/24-Torso-3.stl", "Chests", (0, 0, 0))
select(torso); legs = send(f"{AM}/Legs/29-Legs-2.stl", "Legs")
s = float(legs.get("tiow_unit") or 1.0)
V, Tr = T.mesh_np(legs); V = V / s
belt = T.bio_belt(legs, V)
print("unit", s, "belt up", belt["up"].round(3), "lat R", belt["lat"]["R"].round(3), "centre", belt["centre"].round(2), "hips", {k: v.round(2) for k, v in belt["hip"].items()})
pts = T._bio_side_shin_points(legs, V, Tr)
plans = {k: T.bio_plan(V, Tr, *pts[k]) for k in pts if k in ("R", "L")}
for side in ("R", "L"):
    pl = plans[side]
    Cp, dp, hp = T.bio_belt_cut(V, pl, belt, side, 0.0, auto=(a := {}))
    lat = belt["lat"][side]
    print(side, "plan C", pl["C"].round(2), "d", pl["d"].round(2), "ext %.2f" % pl["ext"], "| glue point", Cp.round(2), "lateral from middle %.2f" % ((Cp - belt["centre"]) @ lat), "auto", a, "hull pts", len(hp))
    B = Cp - 0.37 * dp
    near = V[np.linalg.norm(V - B, axis=1) < 3.0]
    lat_n = (near - belt["centre"]) @ lat
    print("   body verts within 3 mm of the ball: %d, their lateral %.2f..%.2f, up from glue %.2f..%.2f" % (len(near), lat_n.min() if len(near) else 0, lat_n.max() if len(near) else 0, ((near - Cp) @ dp).min() if len(near) else 0, ((near - Cp) @ dp).max() if len(near) else 0))

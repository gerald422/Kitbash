exec(open("/home/claude/test/v17/common17.py").read())
prefs.bionic_dir = "/home/claude/test/v118/kit"
select(None); torso = send(f"{AM}/Chest/24-Torso-3.stl", "Chests", (0, 0, 0))
select(torso); legs = send(f"{AM}/Legs/31-Legs-4.stl", "Legs")
for side in ("R", "L"):
    T.bionic_build(legs, side, prefs, cut="belt")
st = json.loads(legs["tiow_bionic_state"])
for side in ("R", "L"):
    sk = st[side].get("skirt")
    if not sk: print(side, "no skirt"); continue
    top = np.array(sk["top"]); r_trim = math.sqrt(sk["R"] ** 2 - sk["h_trim"] ** 2)
    print(side, f"r_trim {r_trim:.2f}, h_trim {sk['h_trim']:.2f}, h_top {sk['h_top']:.2f}; top radii min {top.min():.2f} max {top.max():.2f}; below r_trim-0.05 at {np.sum(top < r_trim - 0.05)} of {len(top)}")
    print("   radii:", np.round(top[::6], 2))
    pl = T.bio_parts(legs, side)["plug"]; print("   plug faces", len(pl.data.polygons))

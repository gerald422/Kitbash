exec(open("/home/claude/test/v17/common17.py").read())
prefs.bionic_dir = "/home/claude/test/v118/kit"
OUT = "/home/claude/test/v118/out3"; os.makedirs(OUT, exist_ok=True)
rend.setup(scene, 560)
select(None); torso = send(f"{AM}/Chest/24-Torso-3.stl", "Chests", (0, 0, 0))
select(torso); legs = send(f"{AM}/Legs/29-Legs-2.stl", "Legs")
VARS = [(0.0, 0.0), (1.0, 20.0), (2.0, 35.0), (2.6, 50.0)]
for i, (o, tl) in enumerate(VARS):
    msg = T.bionic_build(legs, "R", prefs, cut="belt", offset=0.0, out=o, tilt=tl); print(i, o, tl, msg)
    vl.update()
    P = T.bio_parts(legs, "R")
    obs_all = [o_ for o_ in [torso] + list(T._descendants(torso)) if o_.type == 'MESH' and not o_.hide_get() and o_.display_type != 'WIRE']
    cols = [rend.ORANGE if o_.get("tiow_bionic_role") == "plug" else rend.BLUE if o_.get("tiow_bionic") else rend.GREY for o_ in obs_all]
    rend.render(scene, OUT, f"v{i}_leg", obs_all, {"front": (0, 1, 0.05), "side": (1, 0.15, 0.05)}, cols)
    for r in ("thigh", "shin", "foot"): P[r].hide_set(True)
    obs = [legs, P["plug"]]
    rend.render(scene, OUT, f"v{i}_ball", obs, {"front": (0.15, 1, -0.25), "side": (1, 0.2, -0.2), "below": (0.4, 0.5, -1)}, [rend.GREY, rend.ORANGE])
    for r in ("thigh", "shin", "foot"): P[r].hide_set(False)

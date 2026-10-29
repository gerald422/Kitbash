exec(open("/home/claude/test/v17/common17.py").read())
prefs.bionic_dir = "/home/claude/test/v118/kit"
OUT = "/home/claude/test/v118/out"
rend.setup(scene, 900)
select(None); torso = send(f"{AM}/Chest/24-Torso-3.stl", "Chests", (0, 0, 0))
select(torso); legs = send(f"{AM}/Legs/29-Legs-2.stl", "Legs")
select(legs); bpy.ops.tiow.bionic_leg(side='R'); vl.update()
P = T.bio_parts(legs, "R")
obs = [legs] + [o for r, o in P.items() if o.type == 'MESH' and not r.startswith('cut')]
cols = [rend.GREY] + [rend.ORANGE if r == 'plug' else rend.BLUE for r, o in P.items() if o.type == 'MESH' and not r.startswith('cut')]
rend.render(scene, OUT, "close_R", obs, {"front": (0.3, 1, 0.15), "right": (1, 0.2, 0.1), "below": (0.4, 0.6, -0.6), "back": (0.2, -1, 0.1)}, cols)
# without the leg: the cut and the plug
obs2 = [legs, P["plug"]]
rend.render(scene, OUT, "close_cut", obs2, {"front": (0.3, 1, -0.3), "below": (0.3, 0.3, -1)}, [rend.GREY, rend.ORANGE])
for o in P.values():
    if o.type == 'MESH' and not o.get("tiow_bionic_role", "").startswith("cut"): o.hide_set(True)
rend.render(scene, OUT, "close_cutonly", [legs], {"front": (0.3, 1, -0.3), "below": (0.3, 0.3, -1)}, [rend.GREY])

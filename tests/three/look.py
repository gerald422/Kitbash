exec(open("/home/claude/test/variants/common.py").read())
OUT = "/home/claude/test/three"
select(None)
legs = send(f"{MF}/Kit/Legs/29-Legs-2.stl", "Legs", (0, 0, 0)); a = shin_anchors(legs, "29-Legs-2")
for side in ("R", "L"):
    sx = 1 if side == "R" else -1
    rend.render(scene, OUT, f"leg29_{side}", [legs], {"front": (0.3 * sx, 1, 0.1), "out": (sx, 0.2, 0.05)}, [rend.GREY])
torso, shR, shL = torso_both()
select(torso); arm = send(f"{MF}/AssaultMarines-V2/Arms/111-Arm-8-R-A.stl", "Arms", (230, 0, 0))
F = shR.matrix_world
rend.render(scene, OUT, "arm111", [arm], {"out": (1, 0, 0.2), "front": (0.3, 1, 0.3), "top": (0.3, 0.2, 1)}, [rend.BLUE], frame=F)

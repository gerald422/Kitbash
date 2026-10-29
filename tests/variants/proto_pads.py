exec(open("/home/claude/test/variants/common.py").read())
OUT = "/home/claude/test/variants/proto"
torso, shR, shL = torso_both()
arms = {}
for side in ("R", "L"):
    select(torso); arms[side] = send(f"{MF}/AssaultMarines-V2/Arms/111-Arm-8-{side}-A.stl", "Arms", (230, 0, 0))
pads = {}
Tm = torso.matrix_world @ MX @ torso.matrix_world.inverted()
for side, rel in (("R", "Shoulder Pads/56-ShoulderPad-1.stl"), ("L", "Shoulder Pads Mirrored/56-ShoulderPad-1-L.stl")):
    select(torso); p = send(f"{MF}/Kit/{rel}", "Shoulder Pads", (260, 0, 0))
    if side == "R":
        byeye_pauldron(p, arms["R"], shR); PR = p.matrix_world.copy()
    else:
        p.matrix_world = Tm @ PR @ MX
    T.save_folder_fit(p); pads[side] = p
V = {"front": (0, 1, 0.25), "right": (1, 0, 0.15), "top": (0.2, 0.6, 1.0)}
rend.render(scene, OUT, "pads_111", [torso, arms["R"], arms["L"], pads["R"], pads["L"]], V, [rend.GREY, rend.BLUE, rend.BLUE, rend.ORANGE, rend.ORANGE])
for arm_id in ("126-Arm-11", "131-Arm-12", "101-Arm-6"):
    for side in ("R", "L"):
        select(torso); arms[side] = send(f"{MF}/AssaultMarines-V2/Arms/{arm_id}-{side}-A.stl", "Arms", (300, 0, 0))
    rend.render(scene, OUT, f"pads_{arm_id.split('-')[0]}", [torso, arms["R"], arms["L"], pads["R"], pads["L"]], V, [rend.GREY, rend.BLUE, rend.BLUE, rend.ORANGE, rend.ORANGE])

import bpy, json, math, os, sys, tempfile
import numpy as np
from mathutils import Matrix, Vector
exec(open("/home/claude/test/diag/pad_diag.py").read().split("padA = sock(arm")[0])
MX = Matrix.Scale(-1, 4, (1, 0, 0))
L_local = MX @ (torso.matrix_world.inverted() @ shR.matrix_world) @ MX
shL = bpy.data.objects.new("23-Torso-2_socket_Shoulder L", None); torso.users_collection[0].objects.link(shL)
shL["ws_type"] = "Shoulder L"; shL.empty_display_type = 'ARROWS'; shL.parent = torso
shL.matrix_parent_inverse = torso.matrix_world.inverted(); shL.matrix_world = torso.matrix_world @ L_local
T._part_sockets()[0].ensure_type(scene, "Shoulder L")
t_sl = next(t for t in scene.ws_types if t.name == "Shoulder L"); t_r = next(t for t in scene.ws_types if t.name == "Shoulder R")
t_sl.mat = list(t_r.mat); t_sl.captured = True
for arm_id in ("111-Arm-8", "101-Arm-6", "126-Arm-11", "131-Arm-12"):
    for side in ("R", "L"):
        select(torso)
        a = send(f"{MF}/AssaultMarines-V2/Arms/{arm_id}-{side}-A.stl", "Arms", (300, 0, 0))
        pa = sock(a, f"Pad {side}")
        sw = pa.get("tiow_swing")
        sh = shR if side == 'R' else shL; loc, rot, _ = sh.matrix_world.decompose()
        F = Matrix.LocRotScale(loc, rot, Vector((1, 1, 1))) @ Matrix.Rotation(math.radians(sw), 4, 'X')
        Fi = F.inverted()
        print(arm_id, "swing", sw, "anchor in F:", (Fi @ pa.matrix_world.translation))
        row = []
        for x in [v * (1 if side == 'R' else -1) for v in (0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0)]:
            o = F @ Vector((x, 0, 10)); d = F.to_3x3() @ Vector((0, 0, -1))
            inv = a.matrix_world.inverted()
            ok, hit, nn_, ii_ = a.ray_cast(inv @ o, (inv.to_3x3() @ d).normalized())
            row.append(f"x={x}: {(Fi @ (a.matrix_world @ hit)).z:5.2f}" if ok else f"x={x}: --")
        print("   top along F-z:", "  ".join(row))

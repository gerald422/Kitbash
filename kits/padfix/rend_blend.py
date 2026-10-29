import bpy, sys
sys.path.insert(0, "/home/claude/test"); import rend
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath="/mnt/user-data/uploads/Desktop/issues with pauldrons.blend")
sc = bpy.context.scene; rend.setup(sc, 800)
names = ["MarFil Intercessor - Chest 5", "MarFil Intercessor - Legs 10", "CyberBrush Bug Hunters - Fist 3 (3)", "CyberBrush Bug Hunters - Axe Arm 3",
         "MarFil Outrider - Shoulder Pad DA 1", "MarFil Outrider - Shoulder Pad L (mirrored)", "MarFil Intercessor - Head 2"]
obs = [bpy.data.objects[n] for n in names]
for o in obs: o.hide_set(False); o.hide_render = False
cols = [rend.GREY, rend.GREY, rend.BLUE, rend.BLUE, rend.ORANGE, rend.ORANGE, rend.GREY]
root = obs[0]
F = root.matrix_world
# model axes: Mar Fil frame front = +Y? use torso matrix axes
rend.render(sc, "/home/claude/kits/padfix", "model", obs, {"front": (0, 1, 0.15), "back": (0, -1, 0.15), "right": (-1, 0.2, 0.2), "left": (1, 0.2, 0.2), "top": (0, 0.3, 1)}, cols, frame=F)
# close-up of each shoulder: arm + pad + torso
for arm, pad, tag in ((obs[3], obs[5], "R"), (obs[2], obs[4], "L")):
    rend.render(sc, "/home/claude/kits/padfix", "sh" + tag, [obs[0], arm, pad], {"front": (0, 1, 0.2), "side": ((-1 if tag == "R" else 1), 0.1, 0.2), "top": (0, 0.2, 1)}, [rend.GREY, rend.BLUE, rend.ORANGE], frame=F)
for o in obs:
    print(o.name, o.parent.name if o.parent else None, o.parent_type, o.get("tiow_socket"), [k for k in o.keys()][:12])

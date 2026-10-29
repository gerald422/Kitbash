import bpy, sys, bmesh
sys.path.insert(0, "/home/claude/test"); import rend
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; rend.setup(sc, 700)
D = "/mnt/user-data/uploads/new cults/All Mar All the time/CaptainWithJumpPack/CaptainWithJumpPack/RawStl/"
def load(f):
    bpy.ops.wm.stl_import(filepath=D + f); o = bpy.context.selected_objects[0]; o.name = f[:-4]; return o
body = load("3-Legs.stl"); w1 = load("8-WaistPlate-1.stl"); w2 = load("9-WaistPlate-2.stl"); w3 = load("10-WaistPlate-3.stl"); rel = load("11-Relic.stl")
# crop helper: a box object to frame the view
bpy.ops.mesh.primitive_cube_add(size=1, location=(4, 3, 33)); box = bpy.context.active_object; box.scale = (22, 22, 16)
box.display_type = 'WIRE'; box.hide_render = True
out = "/home/claude/kits/capjp"
def r(name, obs, cols, views):
    rend.render(sc, out, name, obs + [box], views, cols + [(0,0,0,0)])
for o in (w1, w2, w3, rel): pass
r("hipR_body", [body], [rend.GREY], {"side": (1, 0.3, 0.1), "front": (0.3, 1, 0.1)})
r("hipR_w1", [body, w1], [rend.GREY, rend.GREEN], {"side": (1, 0.3, 0.1)})
r("hipR_w2", [body, w2], [rend.GREY, rend.GREEN], {"side": (1, 0.3, 0.1)})
box.location = (-8, -2, 31)
r("hipL_body", [body], [rend.GREY], {"side": (-1, 0.3, 0.1)})
r("hipL_w3", [body, w3, rel], [rend.GREY, rend.PURPLE, rend.RED], {"side": (-1, 0.3, 0.1)})

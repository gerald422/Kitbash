import bpy, sys, math, numpy as np
from mathutils import Matrix, Vector
sys.path.insert(0, "/home/claude/test"); import rend
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; rend.setup(sc, 700)
AM = "/mnt/user-data/uploads/new cults/All Mar All the time/AssaultMarines-V2/AssaultMarines-V2/RawSTL"
def load(p, name):
    bpy.ops.wm.stl_import(filepath=p); o = bpy.context.selected_objects[0]; o.name = name; return o
plate = load("/home/claude/kits/hip/WaistPlate.stl", "plate")
legs = load(AM + "/Legs/29-Legs-2.stl", "legs")
torso = load(AM + "/Chest/23-Torso-2.stl", "torso")
for o in (plate, legs, torso):
    V = np.array([v.co[:] for v in o.data.vertices]); print(o.name, "bbox", V.min(0).round(2), V.max(0).round(2), "tris", len(o.data.polygons))
rend.render(sc, "/home/claude/kits/hip", "plate_alone", [plate], {"front": (0, 1, 0.2), "side": (1, 0, 0.2), "back": (0, -1, 0.2), "top": (0.2, 0.3, 1)}, [rend.ORANGE])
rend.render(sc, "/home/claude/kits/hip", "plate_on_legs", [legs, torso, plate], {"front": (0, 1, 0.1), "side": (1, 0, 0.1), "q": (0.7, 0.7, 0.2), "back": (0, -1, 0.1)}, [rend.GREY, rend.GREY, rend.ORANGE])

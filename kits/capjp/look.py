import bpy, sys, numpy as np
sys.path.insert(0, "/home/claude/test"); import rend
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; rend.setup(sc, 700)
D = "/mnt/user-data/uploads/new cults/All Mar All the time/CaptainWithJumpPack/CaptainWithJumpPack/RawStl/"
def load(f):
    bpy.ops.wm.stl_import(filepath=D + f); o = bpy.context.selected_objects[0]; o.name = f[:-4]; return o
body = load("3-Legs.stl"); plate = load("6-Plate.stl"); cape = load("7-Cape.stl")
w1 = load("8-WaistPlate-1.stl"); w2 = load("9-WaistPlate-2.stl"); w3 = load("10-WaistPlate-3.stl"); relic = load("11-Relic.stl")
jp = load("4-JumpPack.stl")
out = "/home/claude/kits/capjp"
V = {"front": (0, 1, 0.1), "back": (0, -1, 0.1), "left": (1, 0, 0.1), "right": (-1, 0, 0.1)}
rend.render(sc, out, "kit", [body, plate, cape, w1, w3, relic], V, [rend.GREY, rend.ORANGE, rend.BLUE, rend.GREEN, rend.PURPLE, rend.RED])
rend.render(sc, out, "kit2", [body, w2], {"left": (1, 0, 0.1), "q": (0.7, 0.7, 0.2)}, [rend.GREY, rend.GREEN])
rend.render(sc, out, "jp", [body, jp], {"left": (1, 0, 0.1)}, [rend.GREY, rend.BLUE])

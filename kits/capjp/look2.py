import bpy, sys
sys.path.insert(0, "/home/claude/test"); import rend
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; rend.setup(sc, 700)
D = "/mnt/user-data/uploads/new cults/All Mar All the time/CaptainWithJumpPack/CaptainWithJumpPack/RawStl/"
def load(f):
    bpy.ops.wm.stl_import(filepath=D + f); o = bpy.context.selected_objects[0]; o.name = f[:-4]; return o
body = load("3-Legs.stl"); cape = load("7-Cape.stl"); jp = load("4-JumpPack.stl")
out = "/home/claude/kits/capjp"
rend.render(sc, out, "back", [body], {"back": (0, -1, 0.15), "backtop": (0, -0.6, 0.8)}, [rend.GREY])
rend.render(sc, out, "jpv", [jp], {"front": (0, 1, 0.1), "back": (0, -1, 0.1), "side": (1, 0, 0.1)}, [rend.BLUE])
rend.render(sc, out, "cape", [body, cape], {"backtop": (0, -0.6, 0.8), "side": (1, 0, 0)}, [rend.GREY, rend.BLUE])

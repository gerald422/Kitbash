import bpy, sys, glob, os
sys.path.insert(0, "/home/claude/test"); import rend
L = "/mnt/user-data/uploads/d/Kitbash Library/"
files = sorted(glob.glob(L + "CyberBrush - Tacticus/Space Bugs Hunters/Space Bug Hunters Loinclothes/Accessories/*.stl"))
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene; rend.setup(scene, 300)
for i, f in enumerate(files):
    before = set(bpy.data.objects)
    bpy.ops.wm.stl_import(filepath=f)
    o = next(x for x in bpy.data.objects if x not in before)
    for k in [x for x in bpy.data.objects if x is not o]: k.hide_render = True
    rend.render(scene, "/home/claude/twoarm/loin/out", "cb%d" % (i + 1), [o], {"posY": (0, 1, 0.15), "negY": (0, -1, 0.15), "posX": (1, 0, 0.15)}, [rend.ORANGE], pad=1.1)
    o.hide_render = True

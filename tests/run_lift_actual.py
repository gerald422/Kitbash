import bpy, sys, os
dry = sys.argv[-1] == "dry"
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.wm.open_mainfile(filepath="/home/claude/blend/3rd attempt finalising actual.blend", load_ui=False)
os.makedirs("/home/claude/ps_lib2", exist_ok=True)
bpy.context.preferences.addons["part_sockets"].preferences.library_path = "/home/claude/ps_lib2/shape_templates.json"
vl = bpy.context.view_layer
def walk(lc):
    yield lc
    for c in lc.children: yield from walk(c)
excl = [lc.collection.name for lc in walk(vl.layer_collection) if lc.exclude]
print("COUNT bpy.data.objects", len(bpy.data.objects), "| view layer objects", len(vl.objects), "| excluded collections", excl)
src = open("/home/claude/tiow_blender/lift/lift_parts_to_library.py").read()
src = src.replace('LIBRARY = r"E:\\Library"', 'LIBRARY = r"/home/claude/liblift_actual"').replace("DRY_RUN = True", f"DRY_RUN = {dry}")
exec(compile(src, "lift", "exec"), {"__name__": "__main__"})

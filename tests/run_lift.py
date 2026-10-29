import bpy, sys, runpy, time
dry = sys.argv[-1] == "dry"
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.wm.open_mainfile(filepath="/home/claude/blend/finalising.blend", load_ui=False)
import os; os.makedirs("/home/claude/ps_lib", exist_ok=True)
bpy.context.preferences.addons["part_sockets"].preferences.library_path = "/home/claude/ps_lib/shape_templates.json"
src = open("/home/claude/tiow_blender/lift/lift_parts_to_library.py").read()
src = src.replace('LIBRARY = r"E:\\Library"', 'LIBRARY = r"/home/claude/liblift"').replace("DRY_RUN = True", f"DRY_RUN = {dry}")
t = time.time(); exec(compile(src, "lift", "exec"), {"__name__": "__main__"}); print("took", round(time.time() - t, 1), "s")

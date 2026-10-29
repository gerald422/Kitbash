import bpy, sys
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_install(filepath="/home/claude/tiow_blender/tiow_inbox.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="tiow_inbox")
import tiow_inbox as T
T.get_prefs().inbox_path = "/home/claude/test/install/local-data/blender-inbox"
bpy.context.scene.unit_settings.scale_length = 0.001
n = T.process_inbox()
objs = [o.name for o in bpy.data.collections["Arms"].objects]
print("RESULT imported", n, objs, bpy.context.view_layer.objects.active.name)
sys.exit(0 if n == 3 and len(objs) == 3 else 1)

"""Josh's query.blend correction (31 Oct 2026: a loincloth that sits under the belt buckle), saved with TIOW Inbox 1.17.4's own Save Correction code,
one side at a time (both=False) and for that part only (folder=False), into a work copy of the library."""
import bpy, json, os
WORK = "/home/claude/twoarm/query2/work/Kitbash Library"
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath="/home/claude/kitbash/addons/tiow_inbox.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="tiow_inbox")
bpy.ops.wm.open_mainfile(filepath="/mnt/user-data/uploads/Desktop/query.blend")
import tiow_inbox as T
for o in bpy.data.objects:
    s = o.get("tiow_src")
    if s and "Kitbash Library\\" in s:
        o["tiow_src"] = os.path.join(WORK, s.split("Kitbash Library\\", 1)[1].replace("\\", "/"))
ob = {o.name: o for o in bpy.data.objects}
PART = ["Marta May 2026 - Loincloth 3"]        # tucked up under the buckle: the loincloth's own placement, not the legs' anchor
for n in PART:
    print("PART  ", n, "->", T.correct_part(ob[n], folder=False, both=False))

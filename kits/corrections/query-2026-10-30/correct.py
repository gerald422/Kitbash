"""Josh's query.blend corrections (30 Oct 2026), saved with TIOW Inbox 1.17.2's own Save Correction code,
one side at a time (both=False) and for that part only (folder=False), into a work copy of the library."""
import bpy, json, os
WORK = "/home/claude/twoarm/query/work/Kitbash Library"
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath="/home/claude/tiow_117x/tiow_inbox.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="tiow_inbox")
bpy.ops.wm.open_mainfile(filepath="/mnt/user-data/uploads/Desktop/query.blend")
import tiow_inbox as T
for o in bpy.data.objects:
    s = o.get("tiow_src")
    if s and "Kitbash Library\\" in s:
        o["tiow_src"] = os.path.join(WORK, s.split("Kitbash Library\\", 1)[1].replace("\\", "/"))
ob = {o.name: o for o in bpy.data.objects}
SOCKET = ["MarFil Bladeguard - Shoulder Pad 1",          # Pad R on the BBoosty bionic arm
          "MarFil Bladeguard - Shin Pad 7",              # Shin R on Legs 4B
          "Marta Jul 2026 - Shin Pad 3 L",               # Shin L on Legs 4B
          "TN Mk10 Assault - Jump Pack Accessories 1",   # Hip L on Legs 4B
          "TN Mk10 Assault - Jump Pack Accessories 9",   # Hip R on Legs 4B
          "TN Mk10 Assault - Jump Pack Accessories 4"]   # Belt Back on Legs 4B
PART = ["TN Mk6 Assault - Jump Pack Universal", "30-Rock-D"]
for n in SOCKET:
    print("SOCKET", n, "->", T.correct_socket(ob[n], folder=False, both=False))
for n in PART:
    print("PART  ", n, "->", T.correct_part(ob[n], folder=False, both=False))

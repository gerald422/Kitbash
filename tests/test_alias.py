"""Library parts (new joint names) snap into a file set up with the old names."""
import bpy, json, os, sys, tempfile
import numpy as np
fails = []
def ck(l, c, d=""):
    print(("  ok   " if c else "  FAIL ") + l + ("" if c else f"  {d}")); c or fails.append(l)
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.wm.open_mainfile(filepath="/home/claude/blend/actual.blend", load_ui=False)
bpy.ops.preferences.addon_install(filepath="/home/claude/tiow_blender/tiow_inbox.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="tiow_inbox")
import tiow_inbox as T
inbox = tempfile.mkdtemp(); T.get_prefs().inbox_path = inbox
vl = bpy.context.view_layer; ob = bpy.data.objects
torso, combi = ob["23-Torso-2.001"], ob["115-CombiWeapon-3-B"]
home = combi.get("dr_home")
for o in vl.objects: o.select_set(False)
torso.select_set(True); vl.objects.active = torso
json.dump({"path": "/home/claude/liblift_v3/Mar Fil - Tacticus/AssaultMarines-V2/Arms/77-Arm-1-R-B.stl", "category": "Arms"},
          open(os.path.join(inbox, "1.json"), "w"))
T.process_inbox(); print("    ", T._state["last"])
arm = vl.objects.active
sock = ob["23-Torso-2.001_socket_arm__Torso_r"]
ck("library arm snapped onto the old arm__Torso_r socket", arm.ws_snap_sock_ref == sock, arm.ws_snap_sock_ref)
ck("origin on the socket", np.abs(np.array(arm.matrix_world) - np.array(sock.matrix_world)).max() < 1e-4)
ck("your hidden combi (a parked variant) is left alone on the socket", combi.parent == sock and combi.hide_get())
# now with the combi showing: it is the part in the way, so it goes home
bpy.data.objects.remove(arm); combi.hide_set(False)
for o in vl.objects: o.select_set(False)
torso.select_set(True); vl.objects.active = torso
json.dump({"path": "/home/claude/liblift_v3/Mar Fil - Tacticus/AssaultMarines-V2/Arms/77-Arm-1-R-B.stl", "category": "Arms"},
          open(os.path.join(inbox, "2.json"), "w"))
T.process_inbox(); print("    ", T._state["last"])
arm = vl.objects.active
ck("arm on the socket", arm.ws_snap_sock_ref == sock)
ck("your visible combi was sent home, not deleted", ob.get("115-CombiWeapon-3-B") is not None and combi.parent is None)
ck("status", "sent home" in T._state["last"], T._state["last"])
print(f"\n{len(fails)} failure(s)"); sys.exit(1 if fails else 0)

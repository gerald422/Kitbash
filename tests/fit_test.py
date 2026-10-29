"""A hand-nudged part survives the lift if its fit is stored first (Store Per-Part Fit)."""
import bpy, json, os, sys, tempfile, numpy as np
fails = []
def ck(l, c, d=""):
    print(("  ok   " if c else "  FAIL ") + l + ("" if c else f"  {d}")); c or fails.append(l)
mw = lambda o: np.array([list(r) for r in o.matrix_world])
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.wm.open_mainfile(filepath="/home/claude/blend/finalising.blend", load_ui=False)
scene = bpy.context.scene; ob = bpy.data.objects
torso, pack, sock = ob["23-Torso-2.001"], ob["55-JumpPack-1"], ob["23-Torso-2.001_socket_Backpack"]
want = np.linalg.inv(mw(torso)) @ mw(pack)
if not sock.users_collection: scene.collection.objects.link(sock)   # in the file it is in no collection
scene.ws_types_index = [t.name for t in scene.ws_types].index("Backpack")
for o in bpy.context.view_layer.objects: o.select_set(False)
pack.select_set(True); sock.select_set(True); bpy.context.view_layer.objects.active = sock
ck("Store Per-Part Fit on the nudged jump pack", bpy.ops.ws.store_part_fit() == {'FINISHED'} and "ws_fit::Backpack" in pack.keys())
g = {"__name__": "lift"}
exec(open("/home/claude/tiow_blender/lift/lift_parts_to_library.py").read(), g)
lib = tempfile.mkdtemp()
for o, rel in ((torso, "Chests/23-Torso-2.stl"), (pack, "Jump Packs/55-JumpPack-1.stl")):
    p = os.path.join(lib, rel); g["write_stl"](p, o)
    side = g["sidecar"](o, scene, {})
    json.dump(side, open(p[:-4] + ".sockets.json", "w"))
ck("jump pack sidecar carries the fit", "Backpack" in json.load(open(os.path.join(lib, "Jump Packs/55-JumpPack-1.sockets.json")))["fits"])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath="/home/claude/tiow_blender/tiow_inbox.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="tiow_inbox")
import tiow_inbox as T
inbox = tempfile.mkdtemp(); T.get_prefs().inbox_path = inbox; scene = bpy.context.scene
got = {}
for i, (k, rel, cat) in enumerate((("torso", "Chests/23-Torso-2.stl", "Chests"), ("pack", "Jump Packs/55-JumpPack-1.stl", "Jump Packs"))):
    scene.cursor.location = (i * 50.0, 0, 0)
    json.dump({"path": os.path.join(lib, rel), "category": cat}, open(os.path.join(inbox, f"{i}.json"), "w"))
    T.process_inbox(); got[k] = bpy.context.view_layer.objects.active
torso, pack = got["torso"], got["pack"]
ck("fit restored on import", "ws_fit::Backpack" in pack.keys())
scene.ws_types_index = [t.name for t in scene.ws_types].index("Backpack")
for o in bpy.context.view_layer.objects: o.select_set(False)
pack.select_set(True); torso.select_set(True); bpy.context.view_layer.objects.active = torso
r = bpy.ops.ws.snap_part()
now = np.linalg.inv(mw(torso)) @ mw(pack)
ck("snaps back to the hand-nudged position", r == {'FINISHED'} and np.abs(now - want).max() < 2e-3, np.abs(now - want).max())
print(f"{len(fails)} failure(s)"); sys.exit(1 if fails else 0)

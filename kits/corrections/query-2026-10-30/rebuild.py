"""Rebuild Josh's query.blend model with TIOW Inbox (1.17.2, or --tiow FILE) from the library sidecars, in the page's send order,
then compare every part with Josh's placement (both relative to the torso). What differs is what Josh moved by hand.
Usage: python rebuild.py [LIBROOT] [OUT.json] [--save BLEND]"""
import bpy, json, os, sys, tempfile, math
from mathutils import Matrix
LIBROOT = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "/mnt/user-data/uploads/d/Kitbash Library"
OUT = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "/home/claude/twoarm/query/rebuild.json"
SAVE = sys.argv[sys.argv.index("--save") + 1] if "--save" in sys.argv else None
TIOW = sys.argv[sys.argv.index("--tiow") + 1] if "--tiow" in sys.argv else "/home/claude/tiow_117x/tiow_inbox.py"
Q = json.load(open("/home/claude/twoarm/query/parts.json"))
ORDER = {"Chests": 0, "Legs": 1, "Arms": 2, "Heads": 5, "Jump Packs": 6, "Shoulder Pads": 7, "Melee": 9, "Shields": 10,
         "Knee Pads": 11, "Accessories": 13, "Bases": 17}
SOCK2 = {"Shoulder R": 3, "Shoulder L": 4, "Pad R": 7, "Pad L": 8, "Hand R": 9, "Hand L": 10, "Shin R": 11, "Shin L": 12,
         "Hip R": 13, "Hip L": 14, "Belt Front": 15, "Belt Back": 16}
def loc(win):
    return os.path.join(LIBROOT, win.split("Kitbash Library\\", 1)[1].replace("\\", "/"))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath=TIOW, overwrite=True)
bpy.ops.preferences.addon_enable(module="tiow_inbox")
import tiow_inbox as T
prefs = T.get_prefs(); prefs.inbox_path = tempfile.mkdtemp()
inbox = os.path.join(tempfile.mkdtemp(), "_builder", "inbox"); os.makedirs(inbox); prefs.builder_inbox = inbox
prefs.adaptor_dir = os.path.join(LIBROOT, "Bits", "Adapters")
T.process_inbox()
reqs = sorted(Q, key=lambda p: SOCK2.get(p["snap"], ORDER.get(p["cat"], 99)))
mid = "rebuild-1"
for i, p in enumerate(reqs):
    path = loc(p["src"])
    r = {"schemaVersion": 1, "path": path, "name": os.path.basename(path)[:-4], "title": os.path.basename(path)[:-4],
         "category": p["cat"], "tags": [], "itemId": "", "sentAt": "", "model": mid}
    if p["cat"] == "Chests": r["at"] = [0, 0, 0]
    elif p["snap"]: r["socket"] = p["snap"]
    json.dump(r, open(os.path.join(inbox, "sb-%04d.json" % i), "w"))
T._state["beat"] = {}; T.process_inbox()
obs = [o for o in bpy.context.view_layer.objects if o.type == 'MESH' and o.get("tiow_model") == mid]
U = T._unscaled
tor_q = next(p for p in Q if p["cat"] == "Chests")
tq = U(Matrix(tor_q["M"])); tr = U(next(o for o in obs if o.get("tiow_category") == "Chests").matrix_world)
res = {}
for p in Q:
    o = next((o for o in obs if o.name.startswith(p["name"][:50]) and o.get("tiow_category") == p["cat"]), None)
    if o is None:
        print("MISSING", p["name"]); continue
    A = tq.inverted() @ U(Matrix(p["M"]))       # Josh's, in the torso's frame
    B = tr.inverted() @ U(o.matrix_world)        # TIOW's own, in the torso's frame
    D = B.inverted() @ A
    unit = float(o.get("tiow_unit", 1.0)) or 1.0
    res[p["name"]] = {"obj": o.name, "snap": o.get("ws_snap_type"), "d_mm": D.translation.length / unit,
                      "ang": math.degrees(D.to_quaternion().angle), "unit": unit}
    print("%-48s %-12s %6.2f mm %6.1f deg" % (p["name"][:48], o.get("ws_snap_type"), D.translation.length / unit, math.degrees(D.to_quaternion().angle)))
json.dump(res, open(OUT, "w"), indent=1)
if SAVE:
    bpy.ops.wm.save_as_mainfile(filepath=SAVE)
